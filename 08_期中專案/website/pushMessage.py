from linebot import LineBotApi
from linebot.models import TextSendMessage
from config import Config

config = Config()


class Push:
    def __init__(self, channelToken=config.channelAccessToken):
        self.line_bot_api = LineBotApi(channelToken)

    def pushMessage(self, inputModel):
        if inputModel['messageType'] == 'textTemplate':
            templateMessage = TextSendMessage(text=inputModel['content'])
            print(inputModel['lineId'], templateMessage)
            self.line_bot_api.push_message(inputModel['lineId'], [templateMessage])
