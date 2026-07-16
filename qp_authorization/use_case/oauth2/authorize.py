import webbrowser
import frappe
import requests
import json
from datetime import datetime, timedelta
from frappe.utils import now_datetime

@frappe.whitelist()
def request_code(enviroment=None):

    frappe.cache().set("access_token", "empty")

    credentials = frappe.db.get_list('qp_auth_credentials', filters = {"grant_type":  "Authorization Code"}, fields = ["auth_url", "client_id", "callback_url"])

    url = credentials[0].auth_url
    
    client_id = credentials[0].client_id
    
    redirect_uri = credentials[0].callback_url

    state_param = "&state={}".format(enviroment) if enviroment else ""

    auth_url = "{url}&response_type=code&client_id={client_id}&redirect_uri={redirect_uri}{state_param}".format(url =url, client_id=client_id, redirect_uri=redirect_uri, state_param=state_param)
    
    webbrowser.open(auth_url)

@frappe.whitelist()
def get_access_token():

    query_params = frappe.request.args

    credentials = frappe.db.get_list('qp_auth_credentials', filters = {"grant_type":  "Authorization Code"}, fields = ["access_token_url", "client_id", "callback_url", "client_secret"])

    url = credentials[0].access_token_url

    payload = {
        "client_id": credentials[0].client_id,
        "code": query_params.get("code"),
        "redirect_uri": credentials[0].callback_url,
        "grant_type": "authorization_code",
        "client_secret": credentials[0].client_secret,
        "resource": "https://api.businesscentral.dynamics.com"
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(url, headers=headers, data=payload)

    response_json = json.loads(response.text)

    if "error" in response_json:
        
        frappe.log_error(response_json, "Error en peticion de BC")

        request_code()

    enviroment = query_params.get("state")

    create_session(response_json, enviroment)

    return response_json["access_token"]

def create_session(response_json, enviroment=None):

    session = frappe.get_doc( doctype = "qp_auth_session", **response_json)

    session.expire_date = now_datetime() + timedelta(seconds=int(response_json["expires_in"]))
    
    if enviroment:
        session.enviroment = enviroment

    session.insert()

    frappe.db.commit()

    frappe.cache().set("access_token", "full")

def get_refresh_token(session):

    credentials = frappe.db.get_list('qp_auth_credentials', filters = {"grant_type":  "Authorization Code"}, fields = ["access_token_url", "client_id", "callback_url", "client_secret"])

    url = credentials[0].access_token_url

    payload = {
        "client_id": credentials[0].client_id,
        "refresh_token": session.refresh_token,
        "redirect_uri": credentials[0].callback_url,
        "grant_type": "refresh_token",
        "client_secret": credentials[0].client_secret,
        "resource": "https://api.businesscentral.dynamics.com"
    }


    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(url, headers=headers, data=payload)
    
    response_json = json.loads(response.text)

    if "error" in response_json:
        
        frappe.log_error(response_json, "Error en peticion de BC")
        
        request_code()

    create_session(response_json, session.enviroment)

    return response_json["access_token"]

def get_token(enviroment):

    session = frappe.get_last_doc('qp_auth_session', filters = {"enviroment": enviroment})
        
    if session.expire_date > now_datetime():

        return session.access_token

    return get_refresh_token(session)

def callback():

    if frappe.get_list('qp_auth_session'):

        session = frappe.get_last_doc('qp_auth_session')
        
        if session.expire_date > now_datetime():

            return session.access_token

        return get_refresh_token(session)
    
    status = frappe.cache().get("access_token")
    
    if status == "empty":

        return False
    
    if not status:
        
        request_code()

        return False
