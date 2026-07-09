import frappe
import base64
from qp_authorization.use_case.bearer.authorize import get_enviroment
from qp_authorization.use_case.rest.request import handler as send_request_base

def get_headers(enviroment):

    credentials = f"{enviroment.user}:{enviroment.password}"

    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {encoded_credentials}'
    }

    return headers

def send_request(endpoint_code, id = None, payload = "", param = None):
    
    response, status = send_request_status(endpoint_code, id, payload, param)

    return response

def send_request_status(endpoint_code, id = None, payload = "", param = None, is_query_param = False):
    
    enviroment, endpoint, setup = get_enviroment(endpoint_code)

    url = enviroment.get_url(endpoint.url, id)
    
    type_param = ""
    
    if param:
    
        type_param = "?" if is_query_param else "/"
    
    url += f"{type_param}{param}"    
    
    headers = get_headers(enviroment)

    response, status =  send_request_base(url, payload, headers, method = endpoint.method)

    return response, status

def send_request_with_param(endpoint_code, id = None, payload = ""):
    
    response, status = send_request_status_with_param(endpoint_code, id, payload)
    
    return response
    
def send_request_status_with_param(endpoint_code, id = None, payload = ""):
    
    enviroment, endpoint, setup = get_enviroment(endpoint_code)
    
    url = enviroment.get_url(endpoint.url, id)

    headers = get_headers(enviroment)

    response, status =  send_request_base(url, payload, headers, method = endpoint.method)

    return response, status
