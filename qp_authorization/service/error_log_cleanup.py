"""One-off purge for Error Log rows created by the old unredacted logger.

The previous qp_authorization logger wrote full request data, headers
(including Authorization), payloads and response bodies into `tabError Log`.
This module deletes those rows in batches. It is intentionally NOT a patch:
run it explicitly per site after reviewing the dry-run output.

Usage:
    bench --site <site> execute \
        qp_authorization.service.error_log_cleanup.purge_secret_rows \
        --kwargs '{"dry_run": True}'

    bench --site <site> execute \
        qp_authorization.service.error_log_cleanup.purge_secret_rows \
        --kwargs '{"dry_run": False}'
"""

import frappe


SECRET_ROW_FILTER = """
(
    (error like '%data:%' and error like '%headers:%' and error like '%response.text:%')
    or error like '%Authorization%'
    or error like '%Password%'
    or error like '%client_secret%'
    or error like '%access_token%'
    or error like '%refresh_token%'
)
"""


def count_secret_rows():
    return frappe.db.sql(
        "select count(*) from `tabError Log` where " + SECRET_ROW_FILTER
    )[0][0]


def describe_secret_rows(limit=10):
    return frappe.db.sql(
        "select name, method, creation from `tabError Log` where "
        + SECRET_ROW_FILTER
        + " order by creation asc limit {0}".format(int(limit)),
        as_dict=True,
    )


def purge_secret_rows(dry_run=True, batch_size=5000):
    """Delete Error Log rows that contain credentials, headers or tokens.

    ``dry_run`` defaults to True so an accidental call never deletes data.
    Set ``dry_run=False`` after reviewing the matching count and sample.
    """

    if isinstance(dry_run, str):
        dry_run = dry_run.lower() not in ("0", "false", "no", "")

    batch_size = int(batch_size)

    if batch_size <= 0:
        batch_size = 5000

    matched_before = count_secret_rows()

    if dry_run:
        return {
            "dry_run": True,
            "matched_before": matched_before,
            "batch_size": batch_size,
            "sample": describe_secret_rows(),
        }

    deleted = 0

    while True:
        frappe.db.sql(
            "delete from `tabError Log` where "
            + SECRET_ROW_FILTER
            + " limit {0}".format(batch_size)
        )

        affected = frappe.db.sql("select row_count()")[0][0]

        frappe.db.commit()

        deleted += affected

        if affected < batch_size:
            break

    return {
        "dry_run": False,
        "matched_before": matched_before,
        "deleted": deleted,
        "remaining": count_secret_rows(),
    }
