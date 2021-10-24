import os
import re
from flask import Flask, request, render_template, jsonify, url_for, redirect
import json
import time
import pandas as pd
from datetime import datetime
import threading
from config import Config
from lineAPI import PushMessage
from firestoreDAO import Firestore
from check import CheckFootprints

config = Config()
firestore = Firestore()
line = PushMessage()
app = Flask(__name__)
app.secret_key = os.urandom(24)


# ----------------------個人資料-----------------------------------------
@app.route("/myData/<memberId>",methods=['GET', 'POST'])
def myData(memberId):
    if request.method == 'GET':
        _data = { id : memberId }
        member = firestore.getMember(_data)[0]
    if request.method == 'POST':
        setUpData = request.form.to_dict()
        setUpData['id'] = memberId
        firestore.updateMember(setUpData)
        _data = { id : memberId }
        member = firestore.getMember(_data)[0]
    return render_template('myData.html', member = member, title = "我的個資")
@app.route("/myForm/<memberId>", methods=['GET'])
def myForm(memberId):
    _data = { id: memberId }
    member = firestore.getMember(_data)[0]
    return render_template('myForm.html', member = member, title = "修改個資")
# ----------------------掃碼---------------------------------------------
@app.route("/newFoortprint/<memberId>", methods=['GET'])
def newFootprint(memberId):
    return render_template('newFootprint.html', memberId=memberId, title="實聯掃碼")
# ----------------------寫入掃碼足跡紀錄-----------------------------------
@app.route("/newFootprint", methods=['POST'])
def setMyFootprint():
    footprintData = json.loads(request.get_data())
    siteIdRegex = re.compile(r'\d\d\d\d \d\d\d\d \d\d\d\d \d\d\d')
    try:
        siteId = siteIdRegex.findall(footprintData['siteInfo'])[0]
        memberId = footprintData['memberId']
        importTime = int(time.time() + 28800)
    except:
        return jsonify('這不是實聯制QRcode')
    companies = firestore.getCompany()
    for company in companies:
        _data = { 'companyId' : company['id'] }
        for site in firestore.getSite(_data):
            if site['id'] == siteId :
                siteName = site['name']
                break
    if siteName != None:
        notificationModel = {
            "lineId": firestore.getMember({'id':memberId})[0]['lineId'],
            "messageType": "textTemplate",
            "content": "掃碼成功\n"
                       f"商店: {siteName}\n"
                       f"時間: {str(datetime.utcfromtimestamp(importTime).strftime('%Y-%m-%d %H:%M:%S'))}"
        }
        notificationThread = threading.Thread(target=line.pushMessage, args=(notificationModel,))
        notificationThread.start()

        # - firestore
        footprintModel = {
            'memberId': memberId,
            'siteId': siteId,
            'companyId': company['id'],
            'timestamp': importTime
        }
        firestore.setFootprint(footprintModel)


        return jsonify(siteName + '  到店掃碼成功')
    else:
        return jsonify('這不是實聯制QRcode')
# ----------------------------User掃碼足跡紀錄-----------------------------
@app.route("/myFootprints/<memberId>", methods=['GET'])
def getMyFootprint(memberId):
    _data = {'memberId' : memberId}
    footprints = firestore.getFootprints(_data)
    footprints.sort(key=lambda k: (k.get('timestamp', 0)))

    footprintsData = []
    S_IdToName = {}
    C_IdToName = {}

    if footprints != []:
        companies = firestore.getCompany()
        for company in companies:
            C_IdToName[company['id']] = company['name']
            _data = {'companyId': company['id'] }
            for site in firestore.getSite(_data):
                S_IdToName[site['id']] = site['name']

        for footprint in footprints:
            footprint['timestamp'] = str(
                datetime.utcfromtimestamp(footprint['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))

            footprintsData.append(
                {
                    'companyName': C_IdToName[ footprint['companyId'] ],
                    'siteName': S_IdToName[ footprint['siteId'] ],
                    'timestamp': footprint['timestamp']
                }
            )

    return render_template('myFootprints.html', footprintsData=footprintsData, title="足跡列表")

# ----------------------------data studio-----------------------------
@app.route("/getReport/<memberId>", methods=['GET'])
def getReport(memberId):
    return render_template('dataStudio.html')

# ----------------------------疫情調查設定-----------------------------
@app.route("/checkFootprints/<memberId>", methods=['GET'])
def checkFootprints(memberId):
    sitesData = {}
    companies = firestore.getCompany()

    for company in companies:
        _data = { 'companyId': company['id'] }
        for site in firestore.getSite(_data):
            sitesData.update({f"{company['id']}-{site['id']}": f'{company["name"]} {site["name"]}'})

    return render_template('checkFootprints.html', sitesData=sitesData, title="疫情調查")


# ----------------------------疫情調查結果-----------------------------
@app.route("/infectedFootprints", methods=['POST'])
def infectedFootprints():
    event = request.form.to_dict()
    event['companyId'], event['siteId'] = event['siteId'].split('-')
    event['strength'] = int(event['strength'])
    event['infectedTime'] = time.mktime(datetime.strptime(request.values['infectedTime'], "%Y-%m-%dT%H:%M:%S").timetuple()) + 28800
    event['eventId'] = firestore.setEvent(event)
    CheckFootprints(event)
    infectedFootprints = firestore.getEvent(event)['infectedFootprints']
    print(f"infectedFootprints:{infectedFootprints}")
    # line push message------------------------------------------------------
    notifylist = {}
    S_IdToName = {}
    C_IdToName = {}
    companies = firestore.getCompany()
    for company in companies:
        C_IdToName[company['id']] = company['name']
        _data = {'companyId': company['id']}
        for site in firestore.getSite(_data):
            S_IdToName[site['id']] = site['name']
            

    for infectedMember in infectedFootprints:
        #----------------------------------------
        infectedMember['siteName'] = S_IdToName[ infectedMember['siteId'] ]
        infectedMember['companyName'] = C_IdToName[ infectedMember['companyId']]
        _data = {'id': infectedMember['memberId'] }
        infectedMember['name'] = firestore.getMember(_data)[0]['name']
        infectedMember['infectedTime'] = str(datetime.utcfromtimestamp(infectedMember['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))
        #----------------------------------------
        if infectedMember['name'] not in notifylist.keys():
            _data = {'id': infectedMember['memberId']}
            infectedMemberlineId = firestore.getMember(_data)[0]["lineId"]
            notifylist[ infectedMember['name'] ] = {"content": "", "lineId": infectedMemberlineId}
        notifylist[ infectedMember['name'] ]["content"] += f"\n\n感染地點: {infectedMember['siteName']}\n感染時間: {infectedMember['infectedTime']}"

    for member in notifylist.keys():
        notificationModel = {
            "lineId": notifylist[member]['lineId'],
            "messageType": "textTemplate",
            "content": f"{member}，您已遭感染，請盡速就醫！"
                       + notifylist[member]['content']
        }

        notificationThread = threading.Thread(target=line.pushMessage, args=(notificationModel,))
        notificationThread.start()
    # -----------------------------------------------------------------------
    _data = {
        'companyId' : event['companyId'],
        'id' : event['siteId']
    }
    siteName = firestore.getSite(_data)[0]["name"]
    result = {
        'eventId': event['eventId'],
        'strength': str(request.values['strength']),
        "infectedTime": str(request.values['infectedTime']).replace("T", " "),
        "amount": len(set([member['memberId'] for member in infectedFootprints])),
        "name": siteName
    }
    infectedFootprints = sorted(infectedFootprints, key = lambda i: (i['name'], i['timestamp']))
    return render_template('infectedFootprints.html', infectedList=infectedFootprints, result=result, title="疫情調查")


# ----------------------------組織管理-----------------------------
@app.route("/myCompany", methods=['GET'])
def myCompany():
    companies = firestore.getCompany()
    C_IdOfName = {}
    companyData = {}
    for company in companies:
        C_IdOfName[company["id"]] = company["name"]
    _data = { 'companyId' : config.companyId }
    companyData["sitesData"] = firestore.getSite(_data)
    companyData["membersData"] = firestore.getMember(_data)
    return render_template('myCompany.html', companyData=companyData, C_IdOfName=C_IdOfName, companyId=config.companyId, title='我的企業')


# ----------------------------------------------------------------
@app.route("/getCompanyData", methods=['POST'])
def getCompanyData():
    companyId = request.get_json()["companyId"]
    companyData = {}
    _data = {'companyId': companyId}
    companyData["sitesData"] = firestore.getSite(_data)
    companyData["membersData"] = firestore.getMember(_data)
    print(companyData)
    return companyData
    # companyData->{"sitesData":[], "membersData":[]}

# ----------------------------增修商店------------------------------------
@app.route("/mySite/<companyId>/<siteId>", methods=['GET'])
def mySite(companyId, siteId):
    print(companyId, siteId)
    _data = {'companyId': companyId}
    company = firestore.getCompany(_data)[0]
    site = {}
    if siteId !="_":
        _data = {'companyId': companyId, 'id':siteId}
        site = firestore.getSite(_data)[0]

    return render_template('mySite.html', company=company, site=site, title='增修商店')

# ----------------------------增修商店------------------------------------
@app.route("/mySite", methods=['POST'])
def newSite():
    setUpData = request.form.to_dict()
    firestore.setSite(setUpData)
    return redirect(url_for('myCompany'))


port = int(os.environ.get('PORT', 8001))
if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    app.run(host='127.0.0.1', port=port, debug=True)
