import webbrowser
import frappe
import requests
import json
from datetime import datetime, timedelta
from frappe.utils import now_datetime
from qp_authorization.service.secrets import get_secret
from qp_authorization.use_case.rest.safe_logging import (
    describe_http_error,
    summarize_error_response,
)

CLIENT_CREDENTIALS_GRANT = "Client Credentials"
DEFAULT_SCOPE = "https://api.businesscentral.dynamics.com/.default"
DEFAULT_RESOURCE = "https://api.businesscentral.dynamics.com"
DEFAULT_TIMEOUT = 30
CACHE_KEY_TEMPLATE = "qp_authorization:client_credentials:{}:{}"


class ClientCredentialsError(Exception):
    pass


def get_authorization_code_credentials():
    """Load the configured Authorization Code credential document.

    Reading ``client_secret`` from a list query returns the Password dummy
    value, so callers must always use the document and ``get_secret``.
    """

    rows = frappe.get_all(
        "qp_auth_credentials",
        filters={"grant_type": "Authorization Code"},
        fields=["name"],
        limit=1,
        order_by="modified desc",
        ignore_permissions=True,
    )

    if not rows:

        frappe.throw("No hay credenciales de tipo Authorization Code")

    return frappe.get_doc("qp_auth_credentials", rows[0].name)


@frappe.whitelist()
def request_code(enviroment=None):

    frappe.cache().set("access_token", "empty")

    credentials = get_authorization_code_credentials()

    url = credentials.auth_url
    
    client_id = credentials.client_id
    
    redirect_uri = credentials.callback_url

    state_param = "&state={}".format(enviroment) if enviroment else ""

    auth_url = "{url}&response_type=code&client_id={client_id}&redirect_uri={redirect_uri}{state_param}".format(url =url, client_id=client_id, redirect_uri=redirect_uri, state_param=state_param)
    
    webbrowser.open(auth_url)

@frappe.whitelist()
def get_access_token():

    query_params = frappe.request.args

    credentials = get_authorization_code_credentials()

    url = credentials.access_token_url

    payload = {
        "client_id": credentials.client_id,
        "code": query_params.get("code"),
        "redirect_uri": credentials.callback_url,
        "grant_type": "authorization_code",
        "client_secret": get_secret(credentials, "client_secret"),
        "resource": "https://api.businesscentral.dynamics.com"
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(url, headers=headers, data=payload)

    response_json = json.loads(response.text)

    if "error" in response_json:
        
        frappe.log_error(
            message=summarize_error_response(response_json),
            title="Error en peticion de BC",
        )

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

    credentials = get_authorization_code_credentials()

    url = credentials.access_token_url

    payload = {
        "client_id": credentials.client_id,
        "refresh_token": get_secret(session, "refresh_token"),
        "redirect_uri": credentials.callback_url,
        "grant_type": "refresh_token",
        "client_secret": get_secret(credentials, "client_secret"),
        "resource": "https://api.businesscentral.dynamics.com"
    }


    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(url, headers=headers, data=payload)
    
    response_json = json.loads(response.text)

    if "error" in response_json:
        
        frappe.log_error(
            message=summarize_error_response(response_json),
            title="Error en peticion de BC",
        )
        
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

        return get_secret(session, "access_token")

    return get_refresh_token(session)

def callback():

    if frappe.get_list('qp_auth_session'):

        session = frappe.get_last_doc('qp_auth_session')
        
        if session.expire_date > now_datetime():

            return get_secret(session, "access_token")

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
    client_secret = get_secret(credentials, "client_secret")

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
            "Error obteniendo token Client Credentials: {}".format(
                describe_http_error(response)
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
