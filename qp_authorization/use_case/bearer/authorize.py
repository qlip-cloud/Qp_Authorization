import frappe
from datetime import datetime
from qp_authorization.service.utils import get_endpoint, get_cache_enviroment
from qp_authorization.constant.endpoint import AUTH
from qp_authorization.use_case.rest.request import handler as send_request_base
import jwt
import json

def get_token():
    
    session = get_session()
    
    if session:

        return session.access_token

    session = create_session()
    
    return session.access_token

def get_session():
    
    session_cache = get_cache_session()  

    if session_cache:

        return session_cache
    
    session_doc = get_doc_session()
    
    if session_doc:

        return session_doc

def get_doc_session():

    if frappe.db.count('qp_auth_session'):

        session = frappe.get_last_doc('qp_auth_session')

        if session and session.is_valid():

            save_cache_session(session)

            return session
    
def get_cache_session():

    cache = frappe.cache()
    
    current_site = frappe.local.site

    session_cache = cache.get(f"session-{current_site}")

    if session_cache:

        session_json = json.loads(session_cache)

        session = frappe.get_doc(session_json)

        if session and session.is_valid():

            return session

def search_token(enviroment = None):
    
    if not enviroment:
        
        enviroment = get_cache_enviroment()

    endpoint = get_endpoint(AUTH)

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

def send_request_status(endpoint_code, id = None, payload = "", param = None, is_query_param = False):
    
    token = get_token()

    enviroment = get_cache_enviroment()

    endpoint = get_endpoint(endpoint_code)

    url = enviroment.get_url(endpoint.url, id)
    
    type_param = "?" if is_query_param else "/"
    
    url += f"{type_param}{param}"    
    
    headers = get_headers(token)

    response, status =  send_request_base(url, payload, headers, method = endpoint.method)

    return response, status

def send_request_with_param(endpoint_code, id = None, payload = ""):
    
    response, status = send_request_status_with_param(endpoint_code, id = None, payload = "")
    
    return response
    
def send_request_status_with_param(endpoint_code, id = None, payload = ""):
    
    token = get_token()

    enviroment = get_cache_enviroment()

    endpoint = get_endpoint(endpoint_code)

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

def create_session():

    token = search_token()

    expire_date = get_expire_date(token)

    session = save_session(token, expire_date)

    save_cache_session(session)

    return session

def save_cache_session(session):

    cache = frappe.cache()
    
    current_site = frappe.local.site
    
    cache.set(f"session-{current_site}", session.as_json())

def save_session(token, expire_date):

    session_json = {
        "token_type": "bearer",
        "access_token": token,
        "expire_date": expire_date
    }

    session = frappe.get_doc(doctype = "qp_auth_session", **session_json)
    
    session.save()

    frappe.db.commit()

    return session

def get_expire_date(token):

    decoded_token = jwt.decode(token, verify=False)
    
    expiration_time = decoded_token.get('exp')

    return datetime.fromtimestamp(expiration_time)