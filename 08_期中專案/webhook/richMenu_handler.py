import json
import requests
from config import *


def create_richMenu(lineId, linebotapi, timeflag=True, memberId=""):
    jsonPath = richmenu_json_path
    imagePath = richmenu_png_path
    originPath = originmenu_json_path

    if timeflag:
        jsonFile = open(originPath, encoding='utf-8')
    else:
        jsonFile = open(jsonPath, encoding='utf-8')

    menuJsonObject = json.load(jsonFile)

    for area in menuJsonObject["areas"]:
        if area["action"]["type"] == "uri":
            area["action"]["uri"] = WebUrl + area["action"]["uri"] + "memberId=" + memberId

    createResponse = requests.post(
        'https://api.line.me/v2/bot/richmenu',
        json=menuJsonObject,
        headers={'Authorization': 'Bearer {}'.format(channelAccessToken)}
    )

    # get richmenu id
    richMenuId = json.loads(createResponse.text)['richMenuId']
    print('Create rich menu completed !')

    # upload image of the rich menu
    richMenuImageFile = open(imagePath, 'rb')
    contentType = 'image/{}'.format(richMenuImageFile.name.split('.')[-1])
    linebotapi.set_rich_menu_image(richMenuId, contentType, richMenuImageFile)
    print('Upload image completed !')
    print('All Finish...... Rich menu ID is {} !!'.format(richMenuId))

    # bind richmenu with member
    headers = {'Authorization': 'Bearer {}'.format(channelAccessToken)}
    requests.post('https://api.line.me/v2/bot/user/' + lineId + '/richmenu/' + richMenuId, headers=headers)

    print(f'Success to update rich menu of {lineId} !')
