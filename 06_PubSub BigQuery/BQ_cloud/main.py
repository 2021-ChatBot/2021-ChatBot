from bigQueryProxy import BigQueryProxy
import base64
import json


def bigQueryProxy(request, context):
    action = BigQueryProxy()
    pubsub_message = base64.b64decode(request["data"]).decode('utf-8')
    dataModel = json.loads(pubsub_message)
    print(dataModel.keys())
    if 'footprint' in dataModel.keys():
        action.insertFootprint(dataModel["footprint"])
        return {"code": "200", "message": "success"}
    elif 'event' in dataModel.keys():
        action.insertInfected(dataModel["event"])
        return {"code": "200", "message": "success"}


