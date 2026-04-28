import requests
import json
import pickle
import frappe
def handler(url, payload, headers, method = "POST"):

    data= json.dumps(payload)

    try:
        
        response = requests.request(method, url, headers=headers, data=data)

        mensaje = f"""
            response: {response}
            response.text: {response.text}
            response.status_code: {response.status_code}
            response.reason: {response.reason}
            response.headers: {response.headers}
        """
        frappe.log_error(message=mensaje, title= f"Error al procesar peticion {url}")
        
        return json.loads(response.text), response.status_code
        
    except requests.exceptions.Timeout as e:
        
        frappe.log_error(message=str(e), title= f"Error al procesar peticion {url}")

        return {
            "Message": "Lo sentimos, ha habido un error en la transmisión de datos.",
            "errorInterno": "timeout en peticion"
        }, 500

    except requests.exceptions.RequestException as e:
        
        frappe.log_error(message=str(e), title= f"Error al procesar peticion {url}")

        return {
            "Message": "Lo sentimos, ha habido un error en la transmisión de datos.",
            "errorInterno": str(e)
        }, 500
        
    except json.JSONDecodeError as e:
        
        frappe.log_error(message=str(e), title= f"Error al procesar peticion {url}")

        return {
            "Message": "Lo sentimos, ha habido un error en la transmisión de datos.",
            "errorInterno": str(e.doc)
        }, 500
    except Exception as e:
        
        frappe.log_error(message=str(e), title= f"Error al procesar peticion {url}")

        return {
            "Message": "Lo sentimos, ha habido un error en la transmisión de datos.",
            "errorInterno": str(e)
        }, 500