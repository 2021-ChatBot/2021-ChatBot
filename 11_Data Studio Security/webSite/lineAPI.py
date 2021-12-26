from linebot import LineBotApi
from linebot.models import TextSendMessage
from config import channelAccessToken

class PushMessage:
    def __init__(self, channelToken=channelAccessToken):
        self.lineBotApi = LineBotApi(channelToken)

    def pushMessage(self, inputModel):
        if inputModel['messageType'] == 'textTemplate':
            templateMessage = TextSendMessage(text=inputModel['content'])
            self.lineBotApi.push_message(inputModel['lineId'], [templateMessage])
