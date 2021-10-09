import dialogflowClient as dialogflow
import richMenuController as richmenu
from config import channelSecrect,channelAccessToken
from linebot import WebhookHandler, LineBotApi
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, TextSendMessage, MessageEvent, TextMessage, PostbackEvent

# （0） Messages
welcomeMessage = TextSendMessage(text='歡迎加入 < 智能防疫社群 > ')
menuMessage = TextSendMessage(text='請利用主選單，點選您所需要的服務...')
headerMessage = '收到，我將提供您\n'
scanQrCodeMessage = TextSendMessage(text = headerMessage \
                                        + '實聯掃碼 具體功能')
myFootPrintMessage = TextSendMessage(text = headerMessage \
                                        + '我的足跡 具體資料')
myDataMessage = TextSendMessage(text = headerMessage \
                                        + '我的個資 具體資料')
organizationManagementMessage = TextSendMessage(text = headerMessage \
                                        + '組織管理 具體功能')
epidemicManagementMessage = TextSendMessage(text = headerMessage \
                                        + '疫調管理 具體功能')
reportMessage = TextSendMessage(text = headerMessage \
                                        + '統計報表 具體資料')
errorMessage = TextSendMessage(text='哦，這超出我的能力範圍......')


# （1） Line webhook
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


# （2） Follow event
@handler.add(FollowEvent)
def handle_follow(event):
    lineId = event.source.user_id
    richmenuId = richmenu.create(lineId,channelAccessToken)
    sessionId = lineId
    registerMemberEvent = "registerMember"
    responseFromDialogflow = dialogflow.eventInput(sessionId,registerMemberEvent)
    replyMessages = []
    for text in range(len(responseFromDialogflow['fulfillmentMessages'])):
        message = TextSendMessage(text=responseFromDialogflow['fulfillmentMessages'][text]['text']['text'][0])
        replyMessages.append(message)
    line.reply_message(event.reply_token,replyMessages)
    

# （3） Message event
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    sessionId = event.source.user_id
    text = event.message.text
    responseFromDialogflow = dialogflow.detectIntentTexts(sessionId,text)
    responseFromDialogflow = dialogflow.checkAction(responseFromDialogflow,sessionId)  
    replyMessages = []
    for text in range(len(responseFromDialogflow['fulfillmentMessages'])):
        message = TextSendMessage(text=responseFromDialogflow['fulfillmentMessages'][text]['text']['text'][0])
        replyMessages.append(message)   
    line.reply_message(event.reply_token, replyMessages)


# （4） Postback event
@handler.add(PostbackEvent)
def handle_postback(event):
    command = event.postback.data
    if (command == 'scanQRCode'):
        replyMessages = [scanQrCodeMessage]        
    elif (command == 'myFootPrint'):
        replyMessages = [myFootPrintMessage]        
    elif (command == 'myData'):
        replyMessages = [myDataMessage]       
    elif (command == 'organizationManagement'):
        replyMessages = [organizationManagementMessage]
    elif (command == 'epidemicManagement'):
        replyMessages = [epidemicManagementMessage]        
    elif (command == 'report'):
        replyMessages = [reportMessage]
    line.reply_message(event.reply_token, replyMessages)
