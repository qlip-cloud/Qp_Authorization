import frappe

def get_endpoint(endpoint_code, setup_code): 

    filters = {
        "setup": setup_code, 
        "code": endpoint_code
    }
    
    return frappe.get_last_doc("qp_auth_Endpoint", filters = filters)
