import dialogflowClient as dialogflow
from config import channelSecrect,channelAccessToken
from linebot import WebhookHandler, LineBotApi
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, TextSendMessage, MessageEvent, TextMessage

# （0） Line webhook
handler = WebhookHandler(channelSecrect)
line = LineBotApi(channelAccessToken)
def linewebhook(request):
    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Line-Signature")
    try:
        handler.handle(body,signature)
    except InvalidSignatureError:
        print("signature error")
    return '200 OK'

# （1） Follow event
@handler.add(FollowEvent)
def handle_follow(event):
    sessionId = event.source.user_id
    welcomeEvent = "Welcome"
    response = dialogflow.eventInput(sessionId,welcomeEvent)
    replyMessages = []
    for text in range(len(response['fulfillmentMessages'])):
        message = TextSendMessage(text=response['fulfillmentMessages'][text]['text']['text'][0])
        replyMessages.append(message)
    line.reply_message(event.reply_token,replyMessages)
    
# （2） Message event
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    # （2-1） Dialogflow：input
    sessionId = event.source.user_id
    text = event.message.text
    response = dialogflow.detectIntentTexts(sessionId,text)

    # （2-2） Dialogflow：Check action
    if 'action' in response:
        if response['action'] == "askName" and response['parameters']['any']!="":
            followUpEvent = "RegisterSuccess"
            response = dialogflow.eventInput(sessionId,followUpEvent)
        elif response['action'] == "askAge" and response['parameters']['age']!="":
            age = int(response['parameters']['age']['amount'])
            if age >= 18:
                followUpEvent = "ageEligible"
            else:
                followUpEvent = "ageNotEligible"
            response = dialogflow.eventInput(sessionId,followUpEvent)

    # （2-3） Dialogflow：output
    replyMessages = []
    for text in range(len(response['fulfillmentMessages'])):
        message = TextSendMessage(text=response['fulfillmentMessages'][text]['text']['text'][0])
        replyMessages.append(message)   
    line.reply_message(event.reply_token, replyMessages)
