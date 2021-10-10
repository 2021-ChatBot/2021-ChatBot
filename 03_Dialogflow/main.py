import dialogflowClient as dialogflow
import richMenuController as richMenu
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

# （1） Line webhook
handler = WebhookHandler(channelSecrect)
lineBotApi = LineBotApi(channelAccessToken)
def linewebhook(request):
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body,signature)
    except InvalidSignatureError:
        print("signature error")
    return '200 OK'

# （2） Follow event
@handler.add(FollowEvent)
def handle_follow(event):
    lineId = event.source.user_id
    replyToken = event.reply_token
    text = 'registerMember'
    eventType = 'followEvent'
    richMenu.create(lineId,channelAccessToken)
    dialogflow.detectIntentTexts(lineId, replyToken, text, eventType)
    
    
# （3） Message event
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    lineId = event.source.user_id
    replyToken = event.reply_token
    text = event.message.text
    eventType = 'textEvent'
    dialogflow.detectIntentTexts(lineId, replyToken, text, eventType)


# （4） Postback Event
@handler.add(PostbackEvent)
def handle_postback(event):
    lineId = event.source.user_id
    postbackData = event.postback.data

    if (postbackData == 'scanQRCode'):
        replyMessages = [scanQrCodeMessage]

    elif (postbackData == 'myFootPrint'):
        replyMessages = [myFootPrintMessage]

    elif (postbackData == 'mydata'):
        replyMessages = [myDataMessage] 

    elif (postbackData == 'organizationManagement'):
        replyMessages = [organizationManagementMessage]

    elif (postbackData == 'epidemicManagement'):
        replyMessages = [epidemicManagementMessage]

    elif (postbackData == 'report'):
        replyMessages = [reportMessage]                                                                                                                                            
    lineBotApi.push_message(lineId, replyMessages)