import os
from flask import Flask, request, render_template, jsonify
import json
import time
import datetime
from config import Config
from pushMessage import Push

config = Config()
push = Push()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

#----------------------掃碼-----------------------------------------------
@app.route("/scanQrCode",methods=['GET'])
def scanQrCode():
    lineId = request.values.get('lineId')
    print("---scanQrCode----lineId-----------")
    print(lineId)
    title = "到店掃碼"
    return render_template('scanQrCodeRequest.html', lineId=lineId, title = title)
# ----------------------------掃碼足跡紀錄-----------------------------
@app.route("/footPrintRecord", methods=['POST'])
def recordFootPrint():
    footPrintData = json.loads(request.get_data())
    print(footPrintData)
    siteId = footPrintData['siteId']
    lineId = footPrintData['lineId']
    importTime = int(time.time() + 28800)
    print(siteId)
    if siteId in config.site.keys():
        siteName = config.site[siteId]
        # pushmessage
        notificationModel = {
            "receiverLineIdList":lineId,
            "messages": [
                    {
                        "messageType": "textTemplate",
                        "content": "掃碼成功\n" \
                                f"商店名稱: {siteName}\n" \
                                f"時間: {str(datetime.datetime.utcfromtimestamp(importTime).strftime('%Y-%m-%d %H:%M:%S'))}\n" \
                    }
            ]
        }
        print(notificationModel)
        push.pushMessage(notificationModel)
        return jsonify(siteName + '  到店掃碼成功')
    else:
        return jsonify('無此商家...')

# ----------------------------我的傳播組態設定-----------------------------
@app.route("/mySpreadRequest", methods=['GET'])
def requestMySpread():
    lineId = request.values.get('lineId')
    print("---mySpreadRequest----lineId-----------")
    print(lineId)

    return render_template('mySpreadRequest.html', lineId = lineId)
# ----------------------------我的傳播結果-----------------------------
@app.route("/mySpreadResponse", methods=['POST'])
def responseMySpread():
    confirmedTime = request.values['confirmedTime'].replace('T', ' ')
    inputData = {
        'lineId': request.values['lineId'],
        'spreadStrength': int(request.values['spreadStrength']),
        'confirmedTime':  confirmedTime,
    }
    print(inputData)
    print(confirmedTime)

    # pushmessage
    receiverLineIdList = inputData["lineId"]
    notificationModel = {
        "receiverLineIdList":receiverLineIdList,
        "messages": [
                {
                    "messageType": "textTemplate",
                    "content": "您已確診，請盡速就醫！\n" \
                            f"確診時間: {str(inputData['confirmedTime'])}\n" \
                            f"傳播力道: {inputData['spreadStrength']}\n" \

                }
        ]
    }
    print(notificationModel)
    push.pushMessage(notificationModel)

    title = '我的傳播'
    return render_template('mySpreadResponse.html', mySpreadResponse = inputData, title = title)
#========================================================#
port = int(os.environ.get('PORT', 8000))
if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True

    app.run(threaded=True, host='127.0.0.1', port=port, debug=True)
