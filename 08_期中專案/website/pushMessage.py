from linebot import LineBotApi
from linebot.models import TextSendMessage
from config import Config
config = Config()

class Push:
    def __init__(self, channelToken = config.channelAccessToken):
        self.line_bot_api = LineBotApi(channelToken)

    def getTextTemplateMessage(self, content, emojis=None):
        textTemplate = TextSendMessage(text=content, emojis=emojis)
        return textTemplate
        
    def pushMessage(self, inputModel):
        templateMessages = []
        for message in inputModel['messages']:
            if (message['messageType'] == 'textTemplate'):
                templateMessage = self.getTextTemplateMessage(message['content'])
            
            templateMessages.append(templateMessage)
        self.line_bot_api.push_message(inputModel['receiverLineIdList'], templateMessages)