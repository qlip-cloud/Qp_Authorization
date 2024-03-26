import requests
import json
import pickle

def handler(url, payload, headers, method = "POST"):

    data=json.dumps(payload)

    response = requests.request(method, url, headers=headers, data = data)

    #valida si da timeout

    return json.loads(response.text), response.status_code



