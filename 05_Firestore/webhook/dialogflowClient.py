import os
import json
from google.cloud import dialogflow
from google.protobuf.json_format import MessageToJson
from config import projectId, languageCode

def detectIntent(sessionId, text, event):

    sessionClient = dialogflow.SessionsClient()
    session = sessionClient.session_path(projectId, sessionId)

    if event:
        eventInput = dialogflow.EventInput(name = event, language_code = languageCode)
        queryInput = dialogflow.QueryInput(event = eventInput)

    if text:
        textInput = dialogflow.TextInput(text = text, language_code = languageCode)
        queryInput = dialogflow.QueryInput(text = textInput)

    response = sessionClient.detect_intent(
        request={"session": session, "query_input": queryInput}
    )
    
    jsonResponse = MessageToJson(response._pb)
    DictResponse = json.loads(jsonResponse)

    return DictResponse['queryResult']