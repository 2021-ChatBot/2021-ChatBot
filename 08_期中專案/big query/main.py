from bigQueryProxy import BigQueryProxy
import base64
import json

def bigQueryProxy(request,context):

    action = BigQueryProxy()
    pubsub_message = base64.b64decode(request["data"]).decode('utf-8')
    dataModel = json.loads(pubsub_message)

    if 'footprint' in dataModel.keys():
        action.insertFootprintData(dataModel["footprint"])
        return {"code":"200","message":"success"}
    elif 'member' in dataModel.keys():
        action.insertMemberData(dataModel["member"])
        return {"code":"200","message":"success"}
    elif 'event' in dataModel.keys():
        action.insertInfectedData(dataModel["event"])
        return {"code":"200","message":"success"}
    elif 'update' in dataModel.keys():
        action.updateMember(dataModel["update"])
        return {"code":"200","message":"success"}
    else:
        return {'code':'404','message':"error"}
