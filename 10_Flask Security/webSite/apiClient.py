import json
import requests
from config import apiKey, apiUrl, companyId
from flask import abort

def requestAPI(method="POST", route="", data={}, headers={"x-api-key": apiKey}):
    url = apiUrl + route 
    if method == "GET":
        response = requests.get(url=url, headers=headers)
    elif method == "POST":
        response = requests.post(url=url, json=data, headers=headers)
    elif method == "PUT":
        response = requests.put(url=url, json=data, headers=headers)

    if response.status_code == 401:
        return abort(response.status_code, f'抱歉，你無權限使用{route}的API.')
    elif response.status_code != 200 :
        return abort(response.status_code, response.text)
        
    print(response.text)
    result = json.loads(response.text)["response"]
    return result