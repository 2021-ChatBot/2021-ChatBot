from linebot import LineBotApi
from linebot.models import TextSendMessage
from config import secretResourceId, version
from secretManager import access_secret_version


channelAccessToken = access_secret_version(secretResourceId, version)

class PushMessage:
    def __init__(self, channelToken=channelAccessToken):
        self.lineBotApi = LineBotApi(channelToken)

    def pushMessage(self, inputModel):
        if inputModel['messageType'] == 'textTemplate':
            templateMessage = TextSendMessage(text=inputModel['content'])
            self.lineBotApi.push_message(inputModel['lineId'], [templateMessage])
