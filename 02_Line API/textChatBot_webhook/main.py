from chatBotConfig import channel_secret, channel_access_token
from linebot import WebhookHandler, LineBotApi
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, TextSendMessage, MessageEvent, TextMessage

handler = WebhookHandler(channel_secret)
line_bot_api = LineBotApi(channel_access_token)

# (0) Messages
welcomeMessage = TextSendMessage(text='歡迎加入 < 智能防疫社群 > ')
menuMessage = TextSendMessage(text='本系統提供下列功能：\n' \
                                    + '1. 實聯掃碼\n' \
                                    + '2. 我的足跡\n' \
                                    + '3. 我的個資\n' \
                                    + '4. 組織管理\n' \
                                    + '5. 疫調管理\n' \
                                    + '6. 統計報表\n' \
                                    + '請輸入所需選項......')
headerMessage = '稍後，我將提供您\n'
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
errorMessage = TextSendMessage(text='很抱歉，我沒有提供這項服務')


# (1) Webhook
def lineWebhook(request):
    # get X-Line-Signature header value
    signature = request.headers.get('X-Line-Signature')

    # get request body as text
    body = request.get_data(as_text=True)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        print(e)

    return '200 OK'


# (2) Follow Event
@handler.add(FollowEvent)
def handle_follow(event):
    replyMessages = [welcomeMessage, menuMessage]
    line_bot_api.reply_message(event.reply_token, replyMessages)




# (3) Message Event
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    lineId = event.source.user_id
    command = event.message.text
    lineIdMessage = TextSendMessage(text='LineId: '+ lineId)

    if (command in ['1', '實聯', '掃碼', '實聯掃碼']):
        replyMessages = [lineIdMessage, scanQrCodeMessage]
        
    elif (command in ['2', '足跡', '我的足跡']):
        replyMessages = [lineIdMessage, myFootPrintMessage]

    elif (command in ['3', '個資', '我的個資']):
        replyMessages = [lineIdMessage, myDataMessage]

    elif (command in ['4', '組織', '組織管理']):
        replyMessages = [lineIdMessage, organizationManagementMessage]
        
    elif (command in ['5', '疫調', '疫調管理']):
        replyMessages = [lineIdMessage, epidemicManagementMessage]

    elif (command in ['6', '報表', '統計報表']):
        replyMessages = [lineIdMessage, reportMessage]

    else:
        replyMessages = [errorMessage, menuMessage]
                                                                                    
    line_bot_api.reply_message(event.reply_token, replyMessages)
