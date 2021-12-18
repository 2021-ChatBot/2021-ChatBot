import dialogflowClient as dialogflow
import cloudSqlClient as cloudSql
from linebot import WebhookHandler, LineBotApi
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, TextSendMessage, MessageEvent, TextMessage, TemplateSendMessage, URITemplateAction, CarouselTemplate, CarouselColumn
from config import channelSecret, channelAccessToken, signUpUrl, bindingUrl


# （0） Messages
welcomeMessage = TextSendMessage(text = '歡迎加入 < 智能防疫社群 > ')
backMessage = TextSendMessage(text = '你已經完成註冊綁定\n歡迎回到 < 智能防疫社群 > ')
registerMessage = TemplateSendMessage(
    alt_text='以下有新訊息... ',
    template=CarouselTemplate(
        columns=[
            CarouselColumn(
                thumbnail_image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/McDonald%27s_logo.svg/1200px-McDonald%27s_logo.svg.png',
                title='麥當勞會員系統',
                text='你是新顧客，請註冊',
                actions=[
                    URITemplateAction(
                        label='註冊',
                        uri=signUpUrl
                    ),
                ]
            )
        ]
    )
)

bindingMessage = TemplateSendMessage(
    alt_text='以下有新訊息... ',
    template=CarouselTemplate(
        columns=[
            CarouselColumn(
                thumbnail_image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/McDonald%27s_logo.svg/1200px-McDonald%27s_logo.svg.png',
                title='麥當勞會員系統',
                text='你是舊會員，請綁定',
                actions=[
                    URITemplateAction(
                        label='綁定',
                        uri=bindingUrl
                    ),
                ]
            )
        ]
    )
)

menuMessage = TextSendMessage(text='本系統提供下列功能：\n' \
                                    + '1. 實聯掃碼\n' \
                                    + '2. 我的足跡\n' \
                                    + '3. 我的個資\n' \
                                    + '4. 組織管理\n' \
                                    + '5. 疫調管理\n' \
                                    + '6. 統計報表\n' \
                                    + '請利用主選單，點選需要的服務......')


# （1） Line webhook
handler = WebhookHandler(channelSecret)
lineBotApi = LineBotApi(channelAccessToken)

def linewebhook(request):
    body = request.get_data(as_text=True)
    signature = request.headers.get('X-Line-Signature')
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print('signature error')
    return '200 OK'


# （2） Follow event
@handler.add(FollowEvent)
def handle_follow(event):
    lineId = event.source.user_id
    replyToken = event.reply_token
    if cloudSql.query(lineId, False):
        lineBotApi.reply_message(replyToken, backMessage)
        lineBotApi.push_message(lineId, menuMessage)
    else:
        lineBotApi.reply_message(replyToken, welcomeMessage)
        dialogflowEvent = 'followEvent'
        queryResult = dialogflow.detectIntent(lineId, False, dialogflowEvent)
        handle_queryResult(queryResult, lineId)


# （3） Message event
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    lineId = event.source.user_id
    text = event.message.text
    queryResult = dialogflow.detectIntent(lineId, text, False)
    handle_queryResult(queryResult, lineId)


def handle_queryResult(queryResult, lineId):
    if 'action' in queryResult and queryResult['action'] == "emailCheckAction":
        if queryResult['parameters']['email']:
            email = queryResult['parameters']['email']
            if cloudSql.query(False, email):
                lineBotApi.push_message(lineId, bindingMessage)
            else:
                lineBotApi.push_message(lineId, registerMessage)

    if queryResult['fulfillmentMessages']:
        for n in range(len(queryResult['fulfillmentMessages'])):
            message = TextSendMessage(text=queryResult['fulfillmentMessages'][n]['text']['text'][0])
            lineBotApi.push_message(lineId, message)
