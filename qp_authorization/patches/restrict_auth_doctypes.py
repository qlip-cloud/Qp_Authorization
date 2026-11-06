"""Remove the legacy "All" role from qp_authorization doctypes.

The auth configuration and session doctypes were readable and writable by every
logged-in user. Only System Manager should manage them; application code uses
frappe.get_doc/frappe.get_all and creates sessions with ignore_permissions.
"""

import frappe


PROTECTED_DOCTYPES = (
    "qp_auth_credentials",
    "qp_auth_Enviroment",
    "qp_auth_Endpoint",
    "qp_auth_Setup",
    "qp_auth_session",
)


def execute():
    for doctype in PROTECTED_DOCTYPES:

        frappe.db.delete("DocPerm", {"parent": doctype, "role": "All"})

        if frappe.db.table_exists("Custom DocPerm"):

            frappe.db.delete(
                "Custom DocPerm", {"parent": doctype, "role": "All"}
            )

        frappe.clear_cache(doctype=doctype)
