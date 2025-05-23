import requests
import json
import pickle
import frappe
def handler(url, payload, headers, method = "POST"):

    data=json.dumps(payload)

    try:
            
        response = requests.request(method, url, headers=headers, data=data)
        message = response.text + "\n" + data + "\n" + url
        
        frappe.log_error(message=message, title="assertResponse")
    
        return json.loads(response.text), response.status_code
        
        
    except requests.exceptions.Timeout:

        return {
            "Message": "Lo sentimos, ha habido un error en la transmisión de datos.",
            "errorInterno": "timeout en peticion"
        }, 500

    except requests.exceptions.RequestException as e:

        return {
            "Message": "Lo sentimos, ha habido un error en la transmisión de datos.",
            "errorInterno": str(e)
        }, 500
    
    except Exception as e:

        return {
            "Message": "Lo sentimos, ha habido un error en la transmisión de datos.",
            "errorInterno": str(e)
        }, 500
    


