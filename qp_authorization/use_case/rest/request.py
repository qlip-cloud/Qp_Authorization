import requests
import json
import pickle
import frappe
def handler(url, payload, headers, method = "POST"):

    data= json.dumps(payload)

    try:
        
        response = requests.request(method, url, headers=headers, data=data)

        mensaje = f"""
            data: {data} \n
            response: {response} \n
            response.text: {response.text} \n 
            response.status_code: {response.status_code} \n
            response.reason: {response.reason} \n 
            response.headers: {response.headers} \n
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