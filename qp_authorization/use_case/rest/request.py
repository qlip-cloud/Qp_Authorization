import json

import frappe
import requests

from qp_authorization.use_case.rest.safe_logging import (
    build_request_log,
    sanitize_url,
)


def handler(url, payload, headers, method="POST", timeout=None):

    data = json.dumps(payload)

    try:

        response = requests.request(
            method, url, headers=headers, data=data, timeout=timeout
        )

        if response.status_code >= 400:

            log_request_failure(
                url, method, payload, headers, response=response
            )

        if not response.text:

            return {}, response.status_code

        return json.loads(response.text), response.status_code

    except requests.exceptions.Timeout as error:

        log_request_failure(url, method, payload, headers, error=error)

        return {
            "Message": "Lo sentimos, ha habido un error en la transmisión de datos.",
            "errorInterno": "timeout en peticion",
        }, 500

    except requests.exceptions.RequestException as error:

        log_request_failure(url, method, payload, headers, error=error)

        return {
            "Message": "Lo sentimos, ha habido un error en la transmisión de datos.",
            "errorInterno": "error de red",
        }, 500

    except json.JSONDecodeError as error:

        log_request_failure(url, method, payload, headers, error=error)

        return {
            "Message": "Lo sentimos, ha habido un error en la transmisión de datos.",
            "errorInterno": "respuesta no es JSON valido",
        }, 500

    except Exception as error:

        log_request_failure(url, method, payload, headers, error=error)

        return {
            "Message": "Lo sentimos, ha habido un error en la transmisión de datos.",
            "errorInterno": "error interno",
        }, 500


def log_request_failure(url, method, payload, headers, response=None, error=None):
    """Log structural request metadata only; never headers, bodies or secrets."""

    message = build_request_log(
        method=method,
        url=url,
        payload=payload,
        headers=headers,
        response=response,
        error=error,
    )

    title = ("Error al procesar peticion " + sanitize_url(url))[:140]

    frappe.log_error(message=message, title=title)
