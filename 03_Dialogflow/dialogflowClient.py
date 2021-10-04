import os
import json
from google.cloud import dialogflow
from google.protobuf.json_format import MessageToJson
from config import serviceAccountKey,projectId,languageCode

os.environ ["GOOGLE_APPLICATION_CREDENTIALS"] = serviceAccountKey

def detectIntentTexts(sessionId, texts):

    sessionClient = dialogflow.SessionsClient()
    session = sessionClient.session_path(projectId, sessionId)

    textInput = dialogflow.TextInput(text=texts, language_code=languageCode)
    queryInput = dialogflow.QueryInput(text=textInput)

    response = sessionClient.detect_intent(
        request={"session": session, "query_input": queryInput}
    )
    jsonResponse = MessageToJson(response._pb)
    DictResponse = json.loads(jsonResponse)
    return DictResponse['queryResult']


def eventInput(sessionId, eventName):

    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(projectId, sessionId)

    eventInput = dialogflow.EventInput(name=eventName, language_code=languageCode)
    queryInput = dialogflow.QueryInput(event=eventInput)
    
    response = session_client.detect_intent(
        request={"session": session, "query_input": queryInput}
    )
    jsonResponse = MessageToJson(response._pb)
    DictResponse = json.loads(jsonResponse)
    return DictResponse['queryResult']
