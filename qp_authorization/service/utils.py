import frappe
import json


def get_setup():

    return frappe.get_doc("qp_auth_Setup")

def get_endpoint(code): 

    return frappe.get_doc("qp_auth_Endpoint", code)

def  get_enviroment():

    setup = frappe.get_doc("qp_auth_Setup")
    
    assert_setup_config(setup)
    
    assert_setup_config_enviroment(setup.enviroment)
    
    return frappe.get_doc("qp_auth_Enviroment", setup.enviroment)

def get_cache_enviroment():

    cache = frappe.cache()
    
    current_site = frappe.local.site

    cache.set(f"enviroment-{current_site}", "")
    
    enviroment_url = cache.get(f"enviroment-{current_site}")
    
    if not enviroment_url:

        enviroment = get_enviroment()

        cache.set(f"enviroment-{current_site}", enviroment.as_json())

        return enviroment
        
    enviroment_json = json.loads(cache.get(f"enviroment-{current_site}"))

    enviroment_json.setdefault("doctype", "qp_auth_Enviroment")

    return frappe.get_doc(enviroment_json)

def assert_setup_config(setup):

    if not setup:

        raise SetupNotConfig()
    
def assert_setup_config_enviroment(enviroment):

    if not enviroment:

        raise SetupNotConfigEnviroment    

class SetupNotConfig(Exception):

    def __init__(self, message="Setup no configurado"):

        self.message = message

        super().__init__(self.message)

class SetupNotConfigEnviroment(Exception):
    
    def __init__(self, message="Enviroment en setup no configurado"):

        self.message = message

        super().__init__(self.message)