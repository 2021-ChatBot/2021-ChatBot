import json
import requests
def apiCaller(method = "POST", headers = {} , data = {}, url = ""):
    if method == "POST":
        response = requests.post(json=data, url=url)
    elif method == "GET":
        response = requests.get(params=data, url=url)
    response = json.loads(response.text)["response"]
    return response


