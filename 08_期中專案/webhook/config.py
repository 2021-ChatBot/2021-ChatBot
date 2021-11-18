import os

projectId = "[your project id]"

#（0）Company
WebUrl = "[your app engine url]"

#（1）Line Channel
channelSecret = os.environ ['channelSecret']
channelAccessToken = os.environ ['channelAccessToken']
richmenu_json_path = "richmenu/richmenu.json"
richmenu_png_path = "richmenu/richmenu.png"
originmenu_json_path = "richmenu/origin.json"

#（2）Dialogflow 
languageCode = "zh-TW"
