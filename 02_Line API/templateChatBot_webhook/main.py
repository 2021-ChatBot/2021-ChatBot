from chatBotConfig import channel_secret, channel_access_token
from linebot import WebhookHandler, LineBotApi
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, TextSendMessage, MessageEvent, TextMessage, TemplateSendMessage, MessageTemplateAction, CarouselTemplate, CarouselColumn

handler = WebhookHandler(channel_secret)
line_bot_api = LineBotApi(channel_access_token)

# (0) Messages
welcomeMessage = TextSendMessage(text='歡迎加入 < 智能防疫社群 > ')
menuMessage = TextSendMessage(text='請點選下列選項，告訴我您所需要的服務...')
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

templateMessage = TemplateSendMessage(
        alt_text='以下有新訊息... ',
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url='https://firebasestorage.googleapis.com/v0/b/ntut-chatbot.appspot.com/o/2021%E8%AA%B2%E7%A8%8B%E5%B0%88%E6%A1%88%2F2_LineMessageApi%2Fcustomer.png?alt=media&token=db25ab98-bb27-4db2-bbae-d4d395cd354d',
                    title='個人選項專區',
                    text='請點選下列功能',
                    actions=[
                        MessageTemplateAction(
                            label='實聯掃碼',
                            text='實聯掃碼'
                        ),
                        MessageTemplateAction(
                            label='我的足跡',
                            text='我的足跡'
                        ),
                        MessageTemplateAction(
                            label='我的個資',
                            text='我的個資'
                        ),
                    ]
                ),
                CarouselColumn(
                    thumbnail_image_url='https://firebasestorage.googleapis.com/v0/b/ntut-chatbot.appspot.com/o/2021%E8%AA%B2%E7%A8%8B%E5%B0%88%E6%A1%88%2F2_LineMessageApi%2Fmanager.png?alt=media&token=6d0a44af-bfd1-44f0-aced-e9d42c8d0c5d',
                    title='管理者選項專區',
                    text='請點選下列功能',
                    actions=[
                        MessageTemplateAction(
                            label='組織管理',
                            text='組織管理'
                        ),
                        MessageTemplateAction(
                            label='疫調管理',
                            text='疫調管理'
                        ),
                        MessageTemplateAction(
                            label='統計報表',
                            text='統計報表'
                        ),
                    ]
                )
            ]
        )
)


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
    replyMessages = [welcomeMessage, menuMessage, templateMessage]
    line_bot_api.reply_message(event.reply_token, replyMessages)




# (3) Message Event
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    lineId = event.source.user_id
    command = event.message.text
    lineIdMessage = TextSendMessage(text='LineId: ' + lineId)

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

    elif (command in ['選單']):
        replyMessages = [lineIdMessage, templateMessage]
    else:
        replyMessages = [errorMessage, menuMessage, templateMessage]
                                                                                    
    line_bot_api.reply_message(event.reply_token, replyMessages)
