import dialogflowClient as dialogflow
import richMenuController as richMenu
from config import channelSecrect, channelAccessToken
from linebot import WebhookHandler, LineBotApi
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, TextSendMessage, MessageEvent, TextMessage, PostbackEvent

# （0） Messages
welcomeMessage = TextSendMessage(text = '歡迎加入 < 智能防疫社群 > ')
registerHandleMessage = TextSendMessage(text = '正在為你註冊綁定')
registerSuccessText = '已完成註冊綁定\n'
headerText = '收到，我將提供您\n'
scanQrCodeMessage = TextSendMessage(text = headerText \
                                        + '實聯掃碼 具體功能')
myFootPrintMessage = TextSendMessage(text = headerText \
                                        + '我的足跡 具體資料')
myDataMessage = TextSendMessage(text = headerText \
                                        + '我的個資 具體資料')
organizationManagementMessage = TextSendMessage(text = headerText \
                                        + '組織管理 具體功能')
epidemicManagementMessage = TextSendMessage(text = headerText \
                                        + '疫調管理 具體功能')
reportMessage = TextSendMessage(text = headerText \
                                        + '統計報表 具體資料')

# （1） Line webhook
handler = WebhookHandler(channelSecrect)
lineBotApi = LineBotApi(channelAccessToken)
def linewebhook(request):
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text = True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("signature error")
    return '200 OK'

# （2） Follow event
@handler.add(FollowEvent)
def handle_follow(event):
    lineId = event.source.user_id
    replyToken = event.reply_token
    richMenu.create(lineId, channelAccessToken)
    lineBotApi.reply_message(replyToken, welcomeMessage)
    eventName = 'followEvent'
    queryResult = dialogflow.detectIntent(lineId, False, eventName)
    handle_queryResult(queryResult, lineId)
    
# （3） Message event
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    lineId = event.source.user_id
    text = event.message.text
    queryResult = dialogflow.detectIntent(lineId, text, False)
    handle_queryResult(queryResult, lineId)

# （4） Postback Event
@handler.add(PostbackEvent)
def handle_postback(event):
    replyToken = event.reply_token
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
    lineBotApi.reply_message(replyToken, replyMessages)

def handle_queryResult(queryResult, lineId):
    pushMessages = []
    if 'action' in queryResult and queryResult['action'] == "registerAction":
        lineBotApi.push_message(lineId, registerHandleMessage)
        memberName = queryResult['parameters']['person']['name']
        member = postMemberFlow(lineId, memberName)
        message = TextSendMessage(
            text = registerSuccessText  + 'memberId=' + member['id'] + '\n' \
                                        + 'name=' + member['name'] + '\n' \
                                        + 'lineId=' + member['lineId']
        )
        pushMessages.append(message)
        lineBotApi.push_message(lineId, pushMessages)
    else:
        for text in range(len(queryResult['fulfillmentMessages'])):
            message = TextSendMessage(text = queryResult['fulfillmentMessages'][text]['text']['text'][0])
            pushMessages.append(message)
        lineBotApi.push_message(lineId, pushMessages)

def postMemberFlow(lineId, name):
    member = {'id': '007', 'lineId': lineId, 'name': name}
    return member