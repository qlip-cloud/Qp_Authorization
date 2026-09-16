import frappe
from frappe.utils import cint


def execute():
    frappe.reload_doctype("qp_auth_Setup", force=True)
    frappe.reload_doctype("qp_auth_Endpoint", force=True)

    if frappe.db.count("qp_auth_Setup"):
        return

    config = get_legacy_config()

    if not config.get("enviroment"):
        return

    setup = create_setup(config)

    link_endpoints(setup.name)

    link_sessions(config.get("enviroment"))


def get_legacy_config():
    try:
        rows = frappe.db.sql(
            "select field, value from `tabSingles` where doctype='qp_auth_Setup'",
            as_dict=True,
        )
    except Exception:
        return {}

    return {row.field: row.value for row in rows}


def create_setup(config):
    setup = frappe.get_doc({
        "doctype": "qp_auth_Setup",
        "code": make_code(config.get("enviroment")),
        "enviroment": config.get("enviroment"),
        "autenticacion": config.get("autenticacion"),
        "token_valid_minutes": cint(config.get("token_valid_minutes")) or 30,
    })

    setup.flags.ignore_permissions = True

    setup.insert()

    frappe.db.commit()

    return setup


def make_code(enviroment):
    code = frappe.scrub(enviroment or "") or "default"

    candidate = code

    index = 1

    while frappe.db.exists("qp_auth_Setup", candidate):
        candidate = "{}-{}".format(code, index)
        index += 1

    return candidate


def link_endpoints(setup_name):
    frappe.db.sql(
        "update `tabqp_auth_Endpoint` set setup=%s where setup is null or setup=''",
        (setup_name,),
    )

    frappe.db.commit()


def link_sessions(enviroment):
    try:
        has_column = frappe.db.sql(
            "show columns from `tabqp_auth_session` like 'enviroment'"
        )
    except Exception:
        has_column = None

    if not has_column:
        return

    frappe.db.sql(
        "update `tabqp_auth_session` set enviroment=%s where enviroment is null or enviroment=''",
        (enviroment,),
    )

    frappe.db.commit()
