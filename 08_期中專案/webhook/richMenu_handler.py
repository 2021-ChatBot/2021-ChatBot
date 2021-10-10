import json
import requests
from linebot import LineBotApi
import chatBotConfig 
from config import app_engine_url

# please fill your chatbot channel access token in the below variable

class Linebot():
    def __init__(self):
        self.__channel_access_token = chatBotConfig.channel_access_token
        self.__lineBotApi = LineBotApi(self.__channel_access_token)

    "====================="
    def create_richMenuOfUser(self,lineId):
        jsonPath = chatBotConfig.richmenu_json_path
        imagePath = chatBotConfig.richmenu_png_path
        jsonFile = open(jsonPath, encoding='utf-8')
        menuJsonObject = json.load(jsonFile)
        for area in menuJsonObject["areas"]:
            if area["action"]["type"] == "uri" :
                area["action"]["uri"] = app_engine_url + area["action"]["uri"] + "lineId=" + lineId

        print(menuJsonObject)
        richMenuId = self.create_richMenu(imagePath, menuJsonObject)
        return richMenuId
    "====================="
    def create_richMenu(self, imagePath, menuJsonObject): 
        createResponse = requests.post(
            'https://api.line.me/v2/bot/richmenu',
            json=menuJsonObject,
            headers={'Authorization': 'Bearer {}'.format(self.__channel_access_token)}
        )
        print(createResponse.text)
        richMenuId = json.loads(createResponse.text)['richMenuId']
        print('Create rich menu completed !')

        # upload image of the rich menu
        richMenuImageFile = open(imagePath, 'rb')
        contentType = 'image/{}'.format(richMenuImageFile.name.split('.')[-1])
        self.__lineBotApi.set_rich_menu_image(richMenuId, contentType, richMenuImageFile)
        print('Upload image completed !')
        print('All Finish...... Rich menu ID is {} !!'.format(richMenuId))
        return richMenuId
    "====================="
    def update_richMenu(self, lineId, richMenuId):
        headers={'Authorization': 'Bearer {}'.format(self.__channel_access_token)}
        requests.post('https://api.line.me/v2/bot/user/' + lineId + '/richmenu/' + richMenuId , headers=headers)  
        print(f'Success to update rich menu of {lineId} !')    
