import requests
import json
import pickle

def handler(url, payload, headers, method = "POST"):

    data=json.dumps(payload)

    try:
            
        response = requests.request(method, url, headers=headers, data=data)
        
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
    


