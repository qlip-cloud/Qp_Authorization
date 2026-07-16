import frappe
from datetime import datetime
from frappe.utils import now_datetime
from qp_authorization.constant.endpoint import AUTH
from qp_authorization.use_case.rest.request import handler as send_request_base
import jwt
import json
from qp_authorization.service.utils import get_endpoint

def get_token(enviroment, setup_code):
    
    session = get_session(enviroment.name)
    
    if session:

        return session.access_token
    
    endpoint = get_endpoint(AUTH, setup_code)

    session = create_session(enviroment, endpoint)
    
    return session.access_token

def get_session(enviroment_code):
    
    session_cache = get_cache_session(enviroment_code)  

    if session_cache:

        return session_cache
     
    return get_doc_session(enviroment_code)
    
def get_doc_session(enviroment_code):
    
    filters = {"enviroment": enviroment_code}
    
    if frappe.db.count('qp_auth_session', filters=filters):

        session = frappe.get_last_doc('qp_auth_session', filters=filters)

        if session and session.is_valid():

            save_cache_session(session, enviroment_code)

            return session
    
def get_cache_session(enviroment_code):

    cache = frappe.cache()
    
    current_site = frappe.local.site

    session_cache = cache.get(f"session-{current_site}-{enviroment_code}")

    if session_cache:

        session_json = json.loads(session_cache)

        session = frappe.get_doc(session_json)

        if session and session.is_valid():

            return session

        cache.delete(f"session-{current_site}-{enviroment_code}")

def search_token(enviroment, endpoint):
    
    url = enviroment.get_url(endpoint.url)

    headers = get_headers()

    username_key = enviroment.username_key if hasattr(enviroment, "username_key") and enviroment.username_key else "Username"
    password_key = enviroment.password_key if hasattr(enviroment, "password_key") and enviroment.password_key else "Password"

    payload = {
        username_key: enviroment.user,
        password_key: enviroment.password
    }

    response, status_code = send_request_base(url, payload, headers, method = endpoint.method)

    assert_authentication_ok(status_code)
    
    response_lower = {k.lower(): v for k, v in response.items()}
    
    return response_lower.get("token")

def get_headers(token = None):

    headers = {
        'Content-Type': 'application/json'
    }

    if token:
        
        token = "Bearer " + token
        
        headers.setdefault("Authorization", token)

    return headers

def send_request(endpoint_code, id = None, payload = "", param = None):
    
    response, status = send_request_status(endpoint_code, id, payload, param)

    return response

def send_request_status(endpoint_code, id = "", payload = "", param = "", is_query_param = False):
    
    enviroment, endpoint, setup = get_enviroment(endpoint_code)
    
    token = get_token(enviroment, setup.name)

    url = enviroment.get_url(endpoint.url, id)
    
    type_param = ""
    
    if param:
    
        type_param = "?" if is_query_param else "/"
    
    url += f"{type_param}{param or ''}"    
    
    headers = get_headers(token)

    response, status =  send_request_base(url, payload, headers, method = endpoint.method)

    return response, status

def send_request_with_param(endpoint_code, id = None, payload = ""):
    
    response, status = send_request_status_with_param(endpoint_code, id = None, payload = "")
    
    return response
    
def send_request_status_with_param(endpoint_code, id = None, payload = ""):
    
    enviroment, endpoint, setup = get_enviroment(endpoint_code)
    
    token = get_token(enviroment, setup.name)

    url = enviroment.get_url(endpoint.url, id)

    headers = get_headers(token)

    response, status =  send_request_base(url, payload, headers, method = endpoint.method)

    return response, status

def assert_authentication_ok(status_code):

    if status_code != 200:

        cache = frappe.cache()

        cache.set("enviroment", '')

        raise AuthenticationFail()
    
class AuthenticationFail(Exception):
    
    def __init__(self, message="Error en autenticacion"):

        self.message = message

        super().__init__(self.message)

def create_session(enviroment, endpoint):

    token = search_token(enviroment, endpoint)

    expire_date = get_expire_date(token)

    session = save_session(token, expire_date, enviroment.name)

    save_cache_session(session, enviroment.name)

    return session

def save_cache_session(session, enviroment_code):

    cache = frappe.cache()
    
    current_site = frappe.local.site
    
    cache.set(f"session-{current_site}-{enviroment_code}", session.as_json())

def save_session(token, expire_date, enviroment_code):

    session_json = {
        "token_type": "bearer",
        "access_token": token,
        "expire_date": expire_date,
        "enviroment": enviroment_code
    }

    session = frappe.get_doc(doctype = "qp_auth_session", **session_json)
    
    session.save()

    frappe.db.commit()

    return session

def get_expire_date(token):

    decoded_token = jwt.decode(token, verify=False)
    
    expiration_time = decoded_token.get('exp')

    expire_system = datetime.fromtimestamp(expiration_time)

    return expire_system + (now_datetime() - datetime.now())

def get_enviroment(endpoint_code, setup_list_code = None):

    endpoint = frappe.get_doc("qp_auth_Endpoint", endpoint_code)
    
    if not setup_list_code:
        
        setup_list_code = endpoint.setup
        
    setup = frappe.get_doc("qp_auth_Setup", setup_list_code)
    
    enviroment_code = setup.enviroment
        
    enviroment = frappe.get_doc("qp_auth_Enviroment", enviroment_code)

    return enviroment, endpoint, setup