"""Move existing plaintext secrets into Frappe's encrypted ``__Auth`` table.

The affected fields changed from ``Data``/``Long Text`` to ``Password``. Frappe
masks the DocType column with ``*****`` and stores the encrypted value in
``__Auth`` only when a document is saved after the change, so existing rows
need this one-time migration.
"""

import frappe
from frappe.utils.password import set_encrypted_password


PASSWORD_FIELDS = {
    "qp_auth_credentials": ("client_secret", "password"),
    "qp_auth_Enviroment": ("password",),
    "qp_auth_session": ("access_token", "refresh_token", "code"),
}


def execute():
    for doctype, fields in PASSWORD_FIELDS.items():
        migrate_secrets(doctype, fields)

    cleanup_orphan_secrets()

    frappe.db.commit()

    clear_session_cache()


def clear_session_cache():
    """Drop legacy plaintext token payloads from the custom Redis cache."""

    try:
        frappe.cache().delete_keys("session-*")
        frappe.cache().delete_keys("qp_authorization:client_credentials:*")
    except Exception:
        pass


def migrate_secrets(doctype, fields):
    if not frappe.db.table_exists(doctype):
        return

    for fieldname in fields:
        if not column_exists(doctype, fieldname):
            continue

        rows = frappe.db.sql(
            "select name, `{0}` as secret_value from `tab{1}` "
            "where `{0}` is not null and `{0}` != ''".format(fieldname, doctype),
            as_dict=True,
        )

        for row in rows:
            value = row.get("secret_value")
            name = row.get("name")

            if not value or is_dummy_password(value):
                continue

            set_encrypted_password(doctype, name, value, fieldname)

            mask_secret(doctype, name, fieldname, value)


def mask_secret(doctype, name, fieldname, value):
    frappe.db.sql(
        "update `tab{0}` set `{1}`=%s where name=%s".format(doctype, fieldname),
        ("*" * len(value), name),
    )


def is_dummy_password(value):
    return bool(value) and set(value) == set("*")


def column_exists(doctype, fieldname):
    return bool(
        frappe.db.sql(
            "show columns from `tab{0}` like %s".format(doctype), (fieldname,)
        )
    )


def cleanup_orphan_secrets():
    """Remove encrypted rows left behind by bulk deletions."""

    for doctype in PASSWORD_FIELDS:

        if not frappe.db.table_exists(doctype):
            continue

        frappe.db.sql(
            "delete from `__Auth` where doctype=%s "
            "and name not in (select name from `tab{0}`)".format(doctype),
            (doctype,),
        )
