import webbrowser
import frappe
import requests
import json
from datetime import datetime, timedelta

@frappe.whitelist()
def request_code():

    frappe.cache().set("access_token", "empty")

    credentials = frappe.db.get_list('qp_auth_credentials', fields = ["auth_url", "client_id", "callback_url"])

    url = credentials[0].auth_url
    
    client_id = credentials[0].client_id
    
    redirect_uri = credentials[0].callback_url

    auth_url = "{url}&response_type=code&client_id={client_id}&redirect_uri={redirect_uri}".format(url =url, client_id=client_id, redirect_uri=redirect_uri)
    
    webbrowser.open(auth_url)

@frappe.whitelist()
def get_access_token():

    query_params = frappe.request.args

    credentials = frappe.db.get_list('qp_auth_credentials', fields = ["access_token_url", "client_id", "callback_url", "client_secret"])

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

        request_code()

    create_session(response_json)

    return response_json["access_token"]

def create_session(response_json):

    session = frappe.get_doc( doctype = "qp_auth_session", **response_json)

    session.expire_date = datetime.now() + timedelta(seconds=int(response_json["expires_in"]))
    
    session.insert()

    frappe.db.commit()

    frappe.cache().set("access_token", "full")

def get_refresh_token(session):

    credentials = frappe.db.get_list('qp_auth_credentials', fields = ["access_token_url", "client_id", "callback_url", "client_secret"])

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

        request_code()

    create_session(response_json)

    return response_json["access_token"]

def get_token():

    session = frappe.get_last_doc('qp_auth_session')
        
    if session.expire_date > datetime.now():

        return session.access_token

    return get_refresh_token(session)
















def callback():

    if frappe.get_list('qp_auth_session'):

        session = frappe.get_last_doc('qp_auth_session')
        
        if session.expire_date > datetime.now():

            return session.access_token

        return get_refresh_token(session)
    
    status = frappe.cache().get("access_token")
    
    if status == "empty":

        return False
    
    if not status:
        
        request_code()

        return False
