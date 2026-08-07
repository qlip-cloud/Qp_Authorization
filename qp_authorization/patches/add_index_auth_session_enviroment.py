import frappe

def execute():
    frappe.reload_doctype("qp_auth_session")
    frappe.db.add_index("qp_auth_session", ["enviroment"], index_name="enviroment")
