import os
import re
from flask import Flask, request, render_template, jsonify, redirect
import json
import time
from datetime import datetime
import threading
from config import Config
from pushMessage import Push
from firebaseApi import Firebase
from edgePub import edgePub
from transmission import TransmissionTracker

config = Config()
firebase = Firebase()
push = Push()
app = Flask(__name__)
app.secret_key = os.urandom(24)


# ----------------------個人資料-----------------------------------------
@app.route("/myData", methods=['GET', 'POST'])
def myData():
    memberId = request.values.get('memberId')

    if request.method == 'GET':
        memberData = firebase.getMemberData(memberId)
        title = "我的個資"
        return render_template('myData.html', memberData=memberData, title=title)

    if request.method == 'POST':
        setUpData_dict = {
            'id': memberId,
            'role': request.values['role']
        }
        firebase.putMemberData(setUpData_dict)
        memberData = firebase.getMemberData(memberId)
        title = "角色設定成功"
        return render_template('setUpMyData.html', memberData=memberData, title=title)


# ----------------------掃碼---------------------------------------------
@app.route("/scanQrCode", methods=['GET'])
def scanQrCode():
    memberId = request.values.get('memberId')
    title = "實聯掃碼"
    return render_template('scanQrCode.html', memberId=memberId, title=title)

# ----------------------寫入掃碼足跡紀錄-----------------------------------
@app.route("/recordFootprint", methods=['POST'])
def recordFootprint():
    footprintData = json.loads(request.get_data())
    siteIdRegex = re.compile(r'\d\d\d\d \d\d\d\d \d\d\d\d \d\d\d')
    try:
        siteId = siteIdRegex.findall(footprintData['siteInfo'])[0]
    except:
        return jsonify('這不是實聯制QRcode')
        
    memberId = footprintData['memberId']
    importTime = int(time.time() + 28800)

    siteData = firebase.getSiteData(siteId)
    memberData = firebase.getMemberData(memberId)
    if siteData != None:
        notificationModel = {
            "receiverLineIdList": memberData['lineId'],
            "messages": [
                {
                    "messageType": "textTemplate",
                    "content": "掃碼成功\n"
                               f"商店: {siteData['name']}\n"
                               f"時間: {str(datetime.utcfromtimestamp(importTime).strftime('%Y-%m-%d %H:%M:%S'))}\n"
                    }
            ]
        }
        notificationThread = threading.Thread(target=push.pushMessage, args=(notificationModel,))
        notificationThread.start()

        # - firestore
        footprintModel_dict = {
            'memberId': memberId,
            'lineId': memberData['lineId'],
            'siteId': siteId,
            'companyId': config.companyId,
            'timestamp': importTime
        }
        footPrintId = firebase.postFootprint(footprintModel_dict)

        # - pubsub to bigquery
        bigquery_dict = {
            'footprint': {
                'id': footPrintId,
                'member': footprintModel_dict['memberId'],
                'site': footprintModel_dict['siteId'],
                'timestamp': importTime
            }
        }
        # postFootprintBQ
        bigqueryThread = threading.Thread(target=edgePub, args=(bigquery_dict,))
        bigqueryThread.start()

        return jsonify(siteData['name'] + '  到店掃碼成功')
    else:
        return jsonify('這不是實聯制QRcode')


# ----------------------------User掃碼足跡紀錄-----------------------------
@app.route("/myFootprint", methods=['GET'])
def myFootprint():
    memberId = request.values.get('memberId')
    companyIdOfName, siteIdOfName = firebase.getCompaniesData()
    footprintsDataOfUser = firebase.getFootprintsData(memberId=memberId)
    footprintsDataOfUser.sort(key=lambda k: (k.get('timestamp', 0)))

    footPrintsData_list = []
    for footprintData in footprintsDataOfUser:
        if footprintData != None:
            siteId = footprintData['siteId']
            companyId = footprintData['companyId']
            footprintData['timestamp'] = str(
                datetime.datetime.utcfromtimestamp(footprintData['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))

            footPrintsData_list.append(
                {
                    'companyName': companyIdOfName[companyId],
                    'siteName': siteIdOfName[siteId],
                    'timestamp': footprintData['timestamp']
                }
            )
    title = "足跡列表"
    return render_template('footprintList.html', footPrintsData_list=footPrintsData_list, title=title)


# ----------------------------data studio-----------------------------
@app.route("/epidemicReport", methods=['GET'])
def getReport():
    return render_template('dataStudio.html')


# ----------------------------疫調通報組態設定-----------------------------
@app.route("/epidemicSurvey", methods=['GET'])
def epidemicSurvey():
    membersData = firebase.getMemberData()
    return render_template('epidemicSurvey.html', membersData=membersData, title="疫情調查")


# ----------------------------疫調通報結果-----------------------------
@app.route("/checkFootprintFlow", methods=['POST'])
def checkFootprintFlow():
    memberData = firebase.getMemberData(request.values['memberId'])
    inputData = {
        'memberId': request.values['memberId'],
        'spreadStrength': int(request.values['spreadStrength']),
        'confirmedTime': time.mktime(
            datetime.strptime(request.values['confirmedTime'], "%Y-%m-%dT%H:%M:%S").timetuple()) + 28800,
    }

    checker = TransmissionTracker(inputData)
    eventId = checker.eventId
    infectedList = checker.getResult()

    # - pubsub to bigquery
    if len(infectedList) != 0:
        # postCheckEventBQ
        bigqueryThread = threading.Thread(target=edgePub, args=(checker.insertBigQueryResult(),))
        bigqueryThread.start()
    else:
        result = {
            'spreadStrength': str(request.values['spreadStrength']),
            'eventId': eventId,
            "timestamp": str(request.values['confirmedTime']).replace("T", " "),
            "name": memberData['name']
        }
        return render_template('quarantineList.html', infectedList=infectedList, result=result, title="疫情調查")

    companyIdOfName, siteIdOfName = firebase.getCompaniesData()
    for infectedMember in infectedList:
        infectedMember['siteName'] = siteIdOfName[infectedMember['siteId']]
        infectedMember['companyName'] = companyIdOfName[infectedMember['companyId']]
        infectedMember['timestamp'] = str(
            datetime.utcfromtimestamp(infectedMember['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))
        notificationModel = {
            "receiverLineIdList": infectedMember['lineId'],
            "messages": [
                {
                    "messageType": "textTemplate",
                    "content": f"{infectedMember['name']}，您已遭感染，請盡速就醫！\n"
                               f"感染地點: {infectedMember['siteName']}\n"
                               f"感染時間: {infectedMember['timestamp']}"
                }
            ]
        }
        notificationThread = threading.Thread(target=push.pushMessage, args=(notificationModel,))
        notificationThread.start()
    result = {
        'spreadStrength': str(request.values['spreadStrength']),
        'eventId': eventId,
        "timestamp": str(request.values['confirmedTime']).replace("T", " "),
        "name": memberData['name']
    }

    return render_template('quarantineList.html', infectedList=infectedList, result=result, title="疫情調查")


# ----------------------------組織管理-----------------------------
@app.route("/organizationManagement", methods=['GET'])
def organizationManagement():
    companyIdOfName, siteIdOfName = firebase.getCompaniesData()
    return render_template('organizationManagement.html', companyData=companyIdOfName, title='組織管理')


# -----------------------getOtherCompanyData----------------------
@app.route("/getCompanyData", methods=['POST'])
def getCompanyData():
    companyId = request.get_json()["companyId"]
    companyData = {}
    sitesData = Firebase(companyId).getSiteData()
    companyData["sitesData"] = sitesData
    membersData = Firebase(companyId).getMembersDataOfCompany()
    companyData["membersData"] = membersData

    return companyData
