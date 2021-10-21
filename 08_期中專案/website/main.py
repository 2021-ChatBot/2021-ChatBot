import os
import re
from flask import Flask, request, render_template, jsonify
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
        memberData = firebase.getMemberData(memberId=memberId)
        title = "我的個資"
        return render_template('myData.html', memberData=memberData, title=title)

    if request.method == 'POST':
        setUpData_dict = {
            'id': memberId,
            'role': request.values['role']
        }
        firebase.putMemberData(setUpData_dict)
        memberData = firebase.getMemberData(memberId=memberId)
        return render_template('setUpMyData.html', memberData=memberData, title="角色設定成功")


# ----------------------掃碼---------------------------------------------
@app.route("/scanQrCode", methods=['GET'])
def scanQrCode():
    memberId = request.values.get('memberId')
    return render_template('scanQrCode.html', memberId=memberId, title="實聯掃碼")


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
    for sitesData in firebase.getCompaniesData():
        if siteId in sitesData['sites']:
            siteData = sitesData['sites']
            break

    memberData = firebase.getMemberData(memberId=memberId)
    if siteData != None:
        notificationModel = {
            "lineId": memberData['lineId'],
            "messageType": "textTemplate",
            "content": "掃碼成功\n"
                       f"商店: {siteData[siteId]}\n"
                       f"時間: {str(datetime.utcfromtimestamp(importTime).strftime('%Y-%m-%d %H:%M:%S'))}"
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
        footprintId = firebase.postFootprint(footprintModel_dict)

        # - pubsub to bigquery
        bigquery_dict = {
            'footprint': {
                'id': footprintId,
                'member': footprintModel_dict['memberId'],
                'site': footprintModel_dict['siteId'],
                'timestamp': importTime
            }
        }
        # postFootprintBQ
        bigqueryThread = threading.Thread(target=edgePub, args=(bigquery_dict,))
        bigqueryThread.start()

        return jsonify(siteData[siteId] + '  到店掃碼成功')
    else:
        return jsonify('這不是實聯制QRcode')


# ----------------------------User掃碼足跡紀錄-----------------------------
@app.route("/myFootprint", methods=['GET'])
def myFootprint():
    memberId = request.values.get('memberId')
    companyDataList = firebase.getCompaniesData()
    footprintsDataOfUser = firebase.getFootprintsData(memberId=memberId)
    footprintsDataOfUser.sort(key=lambda k: (k.get('timestamp', 0)))

    footPrintsData_list = []
    for footprintData in footprintsDataOfUser:
        if footprintData != None:
            for i in range(len(companyDataList)):
                if footprintData['siteId'] in companyDataList[i]['sites'].keys():
                    siteId = footprintData['siteId']

                    footprintData['timestamp'] = str(
                        datetime.utcfromtimestamp(footprintData['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))

                    footPrintsData_list.append(
                        {
                            'companyName': companyDataList[i]['name'],
                            'siteName': companyDataList[i]['sites'][siteId],
                            'timestamp': footprintData['timestamp']
                        }
                    )
    return render_template('footprintList.html', footPrintsData_list=footPrintsData_list, title="足跡列表")


# ----------------------------組織管理-----------------------------
@app.route("/organizationManagement", methods=['GET'])
def organizationManagement():
    companyDataList = firebase.getCompaniesData()
    companyIdOfName = {}
    for company in companyDataList:
        companyIdOfName[company["id"]] = company["name"]
    companyData = {}
    sitesData = firebase.getSiteData(companyId=config.companyId)
    companyData["sitesData"] = sitesData
    membersData = firebase.getMemberData(companyId=config.companyId)
    companyData["membersData"] = membersData
    return render_template('organizationManagement.html', companyData=companyData, companyIdOfName=companyIdOfName, companyId=config.companyId, title='組織管理')


# -----------------------getOtherCompanyData----------------------
@app.route("/getCompanyData", methods=['POST'])
def getCompanyData():
    companyId = request.get_json()["companyId"]
    companyData = {}
    sitesData = firebase.getSiteData(companyId=companyId)
    companyData["sitesData"] = sitesData
    membersData = firebase.getMemberData(companyId=companyId)
    companyData["membersData"] = membersData
    return companyData
    # companyData->{"sitesData":[], "membersData":[]}


# ----------------------------疫情調查設定-----------------------------
@app.route("/epidemicSurvey", methods=['GET'])
def epidemicSurvey():
    companyDataList = firebase.getCompaniesData()
    sitesData = {}
    for company in companyDataList:
        sitesids = {}
        sitesids.update(company["sites"])
        for siteId in company["sites"].keys():
            sitesData.update({f"{company['id']}-{siteId}": f'{company["name"]} {sitesids[siteId]}'})

    return render_template('epidemicSurvey.html', sitesData=sitesData, title="疫情調查")


# ----------------------------疫情調查結果-----------------------------
@app.route("/checkFootprintFlow", methods=['POST'])
def checkFootprintFlow():
    companyId, siteId = request.values['siteId'].split('-')
    inputData = {
        'companyId': companyId,
        'siteId': siteId,
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
            "name": firebase.getSiteData(siteId=siteId)["name"]
        }
        return render_template('quarantineList.html', infectedList=infectedList, result=result, title="疫情調查")

    notifylist = {}
    for infectedMember in infectedList:
        infectedMember['siteName'] = firebase.getSiteData(siteId=infectedMember['siteId'], companyId=companyId)["name"]
        infectedMember['companyName'] = firebase.getCompaniesData(infectedMember['companyId'])["name"]
        infectedMemberlineId = firebase.getMemberData(memberId=infectedMember['memberId'])["lineId"]
        infectedMember['timestamp'] = str(
            datetime.utcfromtimestamp(infectedMember['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))
        if infectedMember["name"] not in notifylist.keys():
            notifylist[infectedMember["name"]] = {"content": "", "lineId": infectedMemberlineId}
        notifylist[infectedMember["name"]]["content"] += f"\n\n感染地點: {infectedMember['siteName']}\n" \
                                                         f"感染時間: {infectedMember['timestamp']}"

    for member in notifylist.keys():
        notificationModel = {
            "lineId": notifylist[member]['lineId'],
            "messageType": "textTemplate",
            "content": f"{member}，您已遭感染，請盡速就醫！"
                       + notifylist[member]['content']
        }

        notificationThread = threading.Thread(target=push.pushMessage, args=(notificationModel,))
        notificationThread.start()
    result = {
        'spreadStrength': str(request.values['spreadStrength']),
        'eventId': eventId,
        "timestamp": str(request.values['confirmedTime']).replace("T", " "),
        "amount": len(set(pd.DataFrame(infectedList)["memberId"].drop_duplicates())),
        "name": memberData['name']
    }

    return render_template('quarantineList.html', infectedList=infectedList, result=result, title="疫情調查")
    

# ----------------------------data studio-----------------------------
@app.route("/epidemicReport", methods=['GET'])
def getReport():
    return render_template('dataStudio.html')
