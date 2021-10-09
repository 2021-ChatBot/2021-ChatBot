import json
import requests
from linebot import LineBotApi

#---------------------richmenu create-----------------------
def create(lineId,channelAccessToken):
    menu = "richmenu"
    jsonPath =  "richmenu/"+ menu +".json"
    imagePath = "richmenu/"+ menu +".png"
    with open(jsonPath, encoding='utf-8') as j:
        jsn = json.load(j)
    richmenuId = upload(jsn,imagePath,channelAccessToken)
    update(lineId,richmenuId,channelAccessToken)
    return richmenuId

#---------------------richmenu upload-----------------------
def upload(jsn,imagePath,channelAccessToken):
    createResponse = requests.post(
        'https://api.line.me/v2/bot/richmenu',
        json=jsn,
        headers={'Authorization': 'Bearer {}'.format(channelAccessToken)}
    )
    richmenuId = json.loads(createResponse.text)['richMenuId']
    richMenuImageFile = open(imagePath, 'rb')
    contentType = 'image/{}'.format(richMenuImageFile.name.split('.')[-1])
    LineBotApi(channelAccessToken).set_rich_menu_image(richmenuId, contentType, richMenuImageFile)
    return richmenuId

#---------------------richmenu update-----------------------
def update(lineId,richmenuId,channelAccessToken):
    header = {'Authorization': 'Bearer ' + channelAccessToken}
    requests.post('https://api.line.me/v2/bot/user/'+lineId+'/richmenu/'+ richmenuId , headers=header)
    return richmenuId


#---------------------richmenu delete-----------------------
def delete(richMenuId,ChannelAccessToken):
    if (richMenuId == 'all'):
        richMenuList = LineBotApi(ChannelAccessToken).get_rich_menu_list()
        for richMenu in richMenuList:
            LineBotApi(ChannelAccessToken).delete_rich_menu(richMenu.rich_menu_id)
        richMenuAliasList = list_richMenu_alias(ChannelAccessToken)
        for richMenuAlias in richMenuAliasList:
            delete_richMenu_alias(richMenuAlias['richMenuAliasId'])
    else:
        LineBotApi(ChannelAccessToken).delete_rich_menu(richMenuId)
        richMenuAliasList = list_richMenu_alias(ChannelAccessToken)
        richMenuAliasToDelete = list(filter(lambda richMenuAlias: richMenuAlias['richMenuId']==richMenuId, richMenuAliasList))[0]
        delete_richMenu_alias(richMenuAliasToDelete['richMenuAliasId'])

def delete_richMenu_alias(aliasId,ChannelAccessToken):
    apiUrl = f'https://api.line.me/v2/bot/richmenu/alias/{aliasId}'
    deleteResponse = requests.delete(
        apiUrl,
        headers={'Authorization': 'Bearer {}'.format(ChannelAccessToken)}
    )

def list_richMenu_alias(ChannelAccessToken):
    listResponse = requests.get(
        'https://api.line.me/v2/bot/richmenu/alias/list',
        headers={'Authorization': 'Bearer {}'.format(ChannelAccessToken)}
    )
    return json.loads(listResponse.text)['aliases']
