import webbrowser
import frappe
import requests
import json
from datetime import datetime, timedelta
from frappe.utils import now_datetime

CLIENT_CREDENTIALS_GRANT = "Client Credentials"
DEFAULT_SCOPE = "https://api.businesscentral.dynamics.com/.default"
DEFAULT_RESOURCE = "https://api.businesscentral.dynamics.com"
DEFAULT_TIMEOUT = 30
CACHE_KEY_TEMPLATE = "qp_authorization:client_credentials:{}:{}"


class ClientCredentialsError(Exception):
    pass


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

    if not enviroment:

        frappe.log_error(message="create_session sin environment, no se inserta sesion", title="qp_authorization: create_session sin environment")

        return

    session = frappe.get_doc( doctype = "qp_auth_session", **response_json)

    session.expire_date = now_datetime() + timedelta(seconds=int(response_json["expires_in"]))

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

def get_token(enviroment, credentials_name=None):

    if credentials_name:

        credentials = frappe.get_doc("qp_auth_credentials", credentials_name)

        if credentials.grant_type == CLIENT_CREDENTIALS_GRANT:

            return get_client_credentials_token(credentials, enviroment)

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


def get_client_credentials_token(credentials, environment_code):

    credentials_name = (
        credentials if isinstance(credentials, str) else credentials.name
    )

    cache_key = CACHE_KEY_TEMPLATE.format(environment_code, credentials_name)

    cached_token = frappe.cache().get_value(cache_key, expires=True)

    if cached_token:

        return cached_token

    if isinstance(credentials, str):

        credentials = frappe.get_doc("qp_auth_credentials", credentials)

    if credentials.grant_type != CLIENT_CREDENTIALS_GRANT:

        raise ClientCredentialsError(
            "La credencial {} no es de tipo {}".format(
                credentials.name,
                CLIENT_CREDENTIALS_GRANT,
            )
        )

    access_token, expires_in = request_client_credentials_token(credentials)

    ttl = max(int(expires_in) - 60, 60)

    frappe.cache().set_value(cache_key, access_token, expires_in_sec=ttl)

    return access_token


def request_client_credentials_token(credentials):

    token_url = (
        credentials.get("access_token_url")
        or credentials.get("auth_url")
        or ""
    ).strip()
    client_id = (credentials.get("client_id") or "").strip()
    client_secret = credentials.get("client_secret") or ""

    if not token_url:

        raise ClientCredentialsError(
            "La credencial no tiene access_token_url ni auth_url"
        )

    if not client_id:

        raise ClientCredentialsError("La credencial no tiene client_id")

    if not client_secret:

        raise ClientCredentialsError("La credencial no tiene client_secret")

    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    payload.update(get_token_resource_params(credentials, token_url))

    try:

        response = requests.post(
            token_url,
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=DEFAULT_TIMEOUT,
        )

    except requests.RequestException as error:

        raise ClientCredentialsError(
            "Error de red obteniendo token: {}".format(error)
        )

    if response.status_code != 200:

        raise ClientCredentialsError(
            "Error obteniendo token Client Credentials ({}): {}".format(
                response.status_code,
                (response.text or "")[:500],
            )
        )

    try:

        response_json = response.json()

    except ValueError:

        raise ClientCredentialsError(
            "La respuesta del token no es JSON"
        )

    access_token = response_json.get("access_token")

    if not access_token:

        raise ClientCredentialsError(
            "La respuesta del token no incluye access_token"
        )

    return access_token, response_json.get("expires_in") or 3600


def get_token_resource_params(credentials, token_url):

    configured = (credentials.get("scope") or "").strip()

    if "oauth2/v2.0/token" in token_url:

        return {"scope": configured or DEFAULT_SCOPE}

    if "oauth2/token" in token_url:

        return {"resource": configured or DEFAULT_RESOURCE}

    return {"scope": configured or DEFAULT_SCOPE}
