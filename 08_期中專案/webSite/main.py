import os
from flask import Flask, request, render_template, jsonify, redirect
import json
import time
import datetime
import threading
from config import Config
from pushMessage import Push
from firebaseApi import Firebase
from edgePub import edgePub
from tranmission import TransmissionTracker

firebase = Firebase()

config = Config()
push = Push()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
# ----------------------個人資料-----------------------------------------
@app.route("/myData",methods=['GET', 'POST'])
def myData():
    lineId = request.values.get('lineId')
    print("---myData----lineId-----------")
    print(lineId)

    if request.method == 'GET':
        memberData = firebase.getMemberDataById(lineId)
        title = "我的個資"
        return render_template('myData.html', memberData = memberData, title = title)

    if request.method == 'POST':
        modifyData = {
            'lineId' : lineId,
            'role' : request.values['role']
        }
        firebase.updateMember(modifyData)
        memberData = firebase.getMemberDataById(lineId)
        title = "個資修改成功"
        return render_template('modifyMyData.html', memberData = memberData, title = title)
# ----------------------掃碼---------------------------------------------
@app.route("/scanQrCode",methods=['GET'])
def scanQrCode():
    lineId = request.values.get('lineId')
    print("---scanQrCode----lineId-----------")
    print(lineId)
    title = "到店掃碼"
    return render_template('scanQrCodeRequest.html', lineId=lineId, title = title)
# ----------------------寫入掃碼足跡紀錄-----------------------------------
@app.route("/footPrintRecord", methods=['POST'])
def recordFootPrint():
    footPrintData = json.loads(request.get_data())
    print(footPrintData)
    siteId = footPrintData['siteId']
    lineId = footPrintData['lineId']
    importTime = int(time.time() + 28800)

    siteData = firebase.getSiteDataById(siteId)

    if siteData != None :
        #- pushmessage
        notificationModel = {
            "receiverLineIdList":lineId,
            "messages": [
                    {
                        "messageType": "textTemplate",
                        "content": "掃碼成功\n" \
                                f"商店名稱: {siteData['siteName']}\n" \
                                f"時間: {str(datetime.datetime.utcfromtimestamp(importTime).strftime('%Y-%m-%d %H:%M:%S'))}\n" \
                    }
            ]
        }
        print(notificationModel)
        # push.pushMessage(notificationModel)
        notificationThread =threading.Thread(target = push.pushMessage, args=(notificationModel,))
        notificationThread.start()

        #- firestore
        footPrintModel_dict = {
            'lineId'   : lineId,
            'memberId' : lineId,
            'siteId'   : siteId,
            'timestamp': importTime,
        }
        footPrintId = firebase.createFootPrint(footPrintModel_dict)

        #- pubsub to bigquery
        bigquery_dict ={
            'footprint': {
                        'id':footPrintId,
                        'member':footPrintModel_dict['memberId'],
                        'site':footPrintModel_dict['siteId'],
                        'timestamp':importTime
            }
        }
        # edgePub(bigquery_dict)
        bigqueryThread =  threading.Thread(target = edgePub, args = (bigquery_dict,))
        bigqueryThread.start()

        return jsonify(siteData['siteName'] + '  到店掃碼成功')
    else:
        return jsonify('無此商家...')
# ----------------------------User掃碼足跡紀錄-----------------------------
@app.route("/myFootprint", methods=['GET'])
def myFootprint():
    lineId = request.values.get('lineId')
    print("---myFootprint----lineId-----------")
    print(lineId)

    siteIdToName = {}
    sitesData = firebase.getAllSites()
    for siteData in sitesData:
        siteIdToName[ siteData["id"] ] = siteData["siteName"]
        
    footPrintsData_list = []
    footPrintsDataOfUser = firebase.getfootprintsOfMemberByMemberId(lineId)
    for footPrintsData in footPrintsDataOfUser :
        if footPrintsData != None:
            siteId = footPrintsData['siteId']
            footprintdict = {'siteName':siteIdToName[siteId], 'timestamp':footPrintsData['timestamp']}
            footPrintsData_list.append(footprintdict)
    footPrintsData_list.sort(key=lambda k: (k.get('timestamp', 0)))
    for footPrintsData in footPrintsData_list:
        footPrintsData['timestamp'] = str(datetime.datetime.utcfromtimestamp(footPrintsData['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))
    title = "足跡列表"
    return render_template('footPrintlistResponse.html', footPrintsData_list = footPrintsData_list, title=title)
# ----------------------------data studio-----------------------------
@app.route("/epidemicReport", methods=['GET'])
def epidemicReport():
    lineId = request.values.get('lineId')
    print("---myFootprint----lineId-----------")
    print(lineId)

    device = request.headers.get('User-Agent')
    if 'Line' in device:
        return render_template('dataStudio.html')
    else:
        return redirect('https://datastudio.google.com/reporting/f294ac40-782d-4cc1-ba16-d16eb67ddec9')
# ----------------------------疫調通報組態設定-----------------------------
@app.route("/epidemicSuvery", methods=['GET'])
def requestEpidemicNotification():
    lineId = request.values.get('lineId')
    print("---epidemicSuvery----lineId-----------")
    print(lineId)

    memberDataList = firebase.getAllMemberData()
    return render_template('epidemicNotificationRequest.html', memberDataList=memberDataList)
# ----------------------------疫調通報結果-----------------------------
@app.route("/epidemicNotificationResponse", methods=['POST'])
def EpidemicNotification():
    memberData = firebase.getMemberDataById(request.values['memberId'])
    inputData = {
        'memberId': request.values['memberId'],
        'spreadStrength': int(request.values['spreadStrength']),
        'confirmedTime': time.mktime(datetime.datetime.strptime(request.values['confirmedTime'], "%Y-%m-%dT%H:%M:%S").timetuple())+28800,
    }
    print(inputData)

    epidemicNotificationResponse = TransmissionTracker(inputData)
    print(epidemicNotificationResponse)
    eventId = epidemicNotificationResponse.eventId
    infectedList = epidemicNotificationResponse.getResult()

    if infectedList ==[]:
        result = {
            'spreadStrength': str(request.values['spreadStrength']),
            'eventId': eventId,
            "timestamp":str(request.values['confirmedTime']).replace("T", " "),
            "name":memberData['name']
        }
        return render_template('epidemicNotificationResponse.html', infectedList=infectedList, result=result)


    siteIdToName = {}
    sitesData = firebase.getAllSites()

    for siteData in sitesData:
        siteIdToName[ siteData["id"] ] = siteData["siteName"]
    confirm_member = True
    for infectedMember in infectedList:
        infectedMember['siteName'] = siteIdToName[infectedMember['siteId']]
        infectedMember['timestamp'] = str(datetime.datetime.utcfromtimestamp(infectedMember['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))
        if confirm_member:
            notificationModel = {
                "receiverLineIdList":infectedMember['lineId'],
                "messages": [
                        {
                            "messageType": "textTemplate",
                            "content": f"{infectedMember['name']}，您已確診，請盡速就醫！\n" \
                                    f"確診時間: {infectedMember['timestamp']}\n" \
                                    f"傳播力道: {inputData['spreadStrength']}"
                        }
                ]
            }
            print(notificationModel)
            # push.pushMessage(notificationModel)
            notificationThread =threading.Thread(target = push.pushMessage, args=(notificationModel,))
            notificationThread.start()
            confirm_member = False
        else : 
            notificationModel = {
                "receiverLineIdList":infectedMember['lineId'],
                "messages": [
                        {
                            "messageType": "textTemplate",
                            "content": f"{infectedMember['name']}，您已受感染，請隔離14天！\n" \
                                    f"感染商店: {infectedMember['name']}\n" \
                                    f"感染時間: {infectedMember['timestamp']}\n" \
                                    f"傳播力道: {inputData['spreadStrength']}"
                        }
                ]
            }
            print(notificationModel)
            # push.pushMessage(notificationModel)
            notificationThread =threading.Thread(target = push.pushMessage, args=(notificationModel,))
            notificationThread.start()
    result = {
        'spreadStrength': str(request.values['spreadStrength']),
        'eventId': eventId,
        "timestamp":str(request.values['confirmedTime']).replace("T", " "),
        "name":memberData['name']
    }

    return render_template('epidemicNotificationResponse.html', infectedList=infectedList, result=result)
# ----------------------------商店列表-----------------------------
@app.route("/siteList",methods=['GET', 'POST'])
def siteList():
    lineId = request.values.get('lineId')
    print("---siteList----lineId-----------")
    print(lineId)
    if request.method == 'GET':
        sitesData = firebase.getAllSites()
        title = "商店列表"
        return render_template('siteList.html', sitesData=sitesData, lineId=lineId, title = title)

    if request.method == 'POST':
        QRcodeModel = {
            "siteName":request.values["siteName"],
            "siteId":request.values["siteId"],
            "qrCode_base64":request.values["qrCode_base64"],
        }
        title = "QRcode"
        return render_template("QRcodeOfSite.html",QRcodeModel=QRcodeModel, title =title)
@app.route("/memberList",methods=['GET'])
def memberList():
    lineId = request.values.get('lineId')
    print("---memberList----lineId-----------")
    print(lineId)
    memberDataList = firebase.getAllMemberData()
    return render_template("memberList.html", memberDataList=memberDataList, lineId=lineId)
# ----------------------------組織管理-----------------------------
@app.route("/organizationManagement",methods=['GET'])
def organizationManagement():
    lineId = request.values.get('lineId')
    print("---organizationManagement----lineId-----------")
    print(lineId)
    title='組織管理'
    return render_template('menu.html', title=title)
#========================================================#
port = int(os.environ.get('PORT', 8001))
if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True

    app.run(host='127.0.0.1', port=port, debug=True)