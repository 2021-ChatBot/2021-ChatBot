import dialogflowClient as dialogflow
import cloudSqlClient as cloudSql
from linebot import WebhookHandler, LineBotApi
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, TextSendMessage, MessageEvent, TextMessage, TemplateSendMessage, URITemplateAction, CarouselTemplate, CarouselColumn
from config import channelSecret, channelAccessToken, LiffUrl


# （0） Messages
welcomeMessage = TextSendMessage(text = '歡迎加入 < 智能防疫社群 > ')
backMessage = TextSendMessage(text = '你已經完成註冊綁定\n歡迎回到 < 智能防疫社群 > ')
bindHandleMessage = TextSendMessage(text = '正在為你綁定')
bindSuccessText = '已為你完成綁定\n'
registerMessage = TemplateSendMessage(
        alt_text='以下有新訊息... ',
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/McDonald%27s_logo.svg/1200px-McDonald%27s_logo.svg.png',
                    text='麥當勞會員系統',
                    actions=[
                        URITemplateAction(
                            label='註冊',
                            uri=LiffUrl
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
                lineBotApi.push_message(lineId, bindHandleMessage)
                cloudSql.updateLineId(lineId, email)
                member = cloudSql.query(lineId, email)
                messages = []
                bindSuccessMessage = TextSendMessage(
                    text = bindSuccessText + 'name='   + member['name'] + '\n' \
                                           + 'email='  + email          + '\n' \
                                           + 'lineId=' + lineId
                )
                lineBotApi.push_message(lineId, bindSuccessMessage)
                lineBotApi.push_message(lineId, menuMessage)
            else:
                lineBotApi.push_message(lineId, registerMessage)

    if queryResult['fulfillmentMessages']:
        for n in range(len(queryResult['fulfillmentMessages'])):
            message = TextSendMessage(text=queryResult['fulfillmentMessages'][n]['text']['text'][0])
            lineBotApi.push_message(lineId, message)