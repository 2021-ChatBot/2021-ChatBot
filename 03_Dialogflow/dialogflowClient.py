import os
import json
from linebot import LineBotApi
from linebot.models import TextSendMessage
from google.cloud import dialogflow
from google.protobuf.json_format import MessageToJson
from config import serviceAccountKey,projectId,languageCode,channelAccessToken

os.environ ['GOOGLE_APPLICATION_CREDENTIALS'] = serviceAccountKey
lineBotApi = LineBotApi(channelAccessToken)

def detectIntentTexts(lineId,replyToken,text,eventType):

    # Set session
    sessionClient = dialogflow.SessionsClient()
    session = sessionClient.session_path(projectId, lineId)

    # Detect intent
    if eventType == 'followEvent':
        eventInput = dialogflow.EventInput(name=text, language_code=languageCode)
        queryInput = dialogflow.QueryInput(event=eventInput)
    elif eventType == 'textEvent':
        textInput = dialogflow.TextInput(text=text, language_code=languageCode)
        queryInput = dialogflow.QueryInput(text=textInput)
    response = sessionClient.detect_intent(
        request={"session": session, "query_input": queryInput}
    )
    jsonResponse = MessageToJson(response._pb)
    DictResponse = json.loads(jsonResponse)
    
    # Check action
    if 'action' in DictResponse['queryResult'] and DictResponse['queryResult']['action'] == "registerAction":
        dialogflowEvent = 'RegisterSuccess'
        eventType = 'followEvent'
        detectIntentTexts(lineId,replyToken,dialogflowEvent,eventType)

    # Line reply messaage
    else:
        replyMessages = []
        for text in range(len(DictResponse['queryResult']['fulfillmentMessages'])):
            message = TextSendMessage(text=DictResponse['queryResult']['fulfillmentMessages'][text]['text']['text'][0])
            replyMessages.append(message)
        lineBotApi.reply_message(replyToken,replyMessages)
