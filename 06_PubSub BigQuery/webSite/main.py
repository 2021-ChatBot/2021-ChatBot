# -*- coding: utf-8 -*-
import os
import re
from flask import Flask, request, render_template, jsonify, url_for, redirect
import json
import time
from datetime import datetime
import threading
import config
from lineAPI import PushMessage
from firestoreDAO import FirestoreDAO
from publish import publish_messages
from copy import deepcopy

firestoreDAO = FirestoreDAO()
line = PushMessage()
app = Flask(__name__)
app.secret_key = os.urandom(24)


# ----------------------------註冊綁定------------------------------------
@app.route("/memberRegister", methods=['POST'])
def memberRegister():
    memberData = request.get_json(force=True)
    member = firestoreDAO.setMember(memberData)
    if "setMember" in member.keys():
        # - pubsub
        member["companyName"] = firestoreDAO.getCompanies({'companyId': config.companyId})[0]['name']
        publishThread = threading.Thread(target=publish_messages, args=({"member" : member},))
        publishThread.start()
    return jsonify(member)


# ----------------------個人資料-----------------------------------------
@app.route("/myData/<memberId>", methods=['GET', 'POST'])
def myData(memberId):
    if request.method == 'GET':
        members = firestoreDAO.getMembers({'id': memberId})
        if members == []:
            return "尚未註冊"
    if request.method == 'POST':
        member = request.form.to_dict()
        member['id'] = memberId
        firestoreDAO.updateMember(member)
        members = firestoreDAO.getMembers({'id': memberId})

    return render_template('myData.html', member=members[0], title="我的個資")


# ----------------------修改個資-----------------------------------------
@app.route("/myForm/<memberId>", methods=['GET'])
def myForm(memberId):
    member = firestoreDAO.getMembers({'id': memberId})[0]
    return render_template('myForm.html', member=member, title="修改個資")


# ----------------------掃碼---------------------------------------------
@app.route("/newFootprint/<memberId>", methods=['GET'])
def newFootprint(memberId):
    return render_template('newFootprint.html', memberId=memberId, title="實聯掃碼")


# ----------------------寫入掃碼足跡紀錄-----------------------------------
@app.route("/newFootprint", methods=['POST'])
def setMyFootprint():
    footprintEvent = json.loads(request.get_data())
    siteIdRegex = re.compile(r'\d\d\d\d \d\d\d\d \d\d\d\d \d\d\d')
    try:
        siteId = siteIdRegex.findall(footprintEvent['siteData'])[0]
        memberId = footprintEvent['memberId']
        importTime = int(time.time() + 28800)
    except:
        return jsonify('這不是實聯制QRcode')
    companies = firestoreDAO.getCompanies()
    for company in companies:
        sites = firestoreDAO.getSites({'companyId': company['id'], 'id': siteId})
        if sites != []:
            message = {
                "lineId": firestoreDAO.getMembers({'id': memberId})[0]['lineId'],
                "messageType": "textTemplate",
                "content": "掃碼成功\n"
                           f"商店: {sites[0]['name']}\n"
                           f"時間: {str(datetime.utcfromtimestamp(importTime).strftime('%Y-%m-%d %H:%M:%S'))}"
            }
            notificationThread = threading.Thread(target=line.pushMessage, args=(message,))
            notificationThread.start()

            # - firestore
            footprint = {
                'memberId': memberId,
                'siteId': siteId,
                'companyId': company['id'],
                'timestamp': importTime
            }

            firestoreDAO.setMyFootprint(footprint)
            footprint['companyName'] = company['name']

            # - pubsub
            publishThread = threading.Thread(target=publish_messages, args=({'footprint': footprint},))
            publishThread.start()

            return jsonify(sites[0]['name'] + '  到店掃碼成功')

    return jsonify('這不是實聯制QRcode')


# ----------------------------User掃碼足跡紀錄-----------------------------
@app.route("/myFootprints/<memberId>", methods=['GET'])
def getMyFootprint(memberId):
    myFootprints = []
    for footprint in firestoreDAO.getMyFootprints({'memberId': memberId}):
        myFootprints.append(
            {
                'companyName': firestoreDAO.getCompanies({'companyId': footprint['companyId']})[0]['name'],
                'siteName': firestoreDAO.getSites({'companyId': footprint['companyId'], 'id': footprint['siteId']})[0]['name'],
                'timestamp': str(datetime.utcfromtimestamp(footprint['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))
            }
        )
    return render_template('myFootprints.html', myFootprints=myFootprints, title="足跡列表")


# ----------------------------data studio-----------------------------
@app.route("/report/<memberId>", methods=['GET'])
def report(memberId):
    member = firestoreDAO.getMembers({'id': memberId})[0]
    if member != []:
        if member['role'] == "customer":
            myreport = config.reportForCustomer
        elif member['role'] == "manager":
            myreport = config.reportForManager
    else:
        myreport = None
    return render_template('dataStudio.html', report=myreport)


# ----------------------------疫情調查設定-----------------------------
@app.route("/checkFootprints/<memberId>", methods=['GET'])
def checkFootprints(memberId):
    sitesOfCompany = {}
    companies = firestoreDAO.getCompanies()
    for company in companies:
        for site in firestoreDAO.getSites({'companyId': company['id']}):
            sitesOfCompany[f"{company['id']}-{site['id']}"] = f"{company['name']} {site['name']}"
    return render_template('checkFootprints.html', sitesOfCompany=sitesOfCompany, title="疫情調查")


# ----------------------------疫情調查結果-----------------------------
@app.route("/infectedFootprints", methods=['POST'])
def infectedFootprints():
    event = request.form.to_dict()
    event['companyId'], event['siteId'] = event['siteOfCompany'].split('-')
    del event['siteOfCompany']
    event['strength'] = int(event['strength'])
    event['infectedTime'] = time.mktime(datetime.strptime(request.values['infectedTime'], "%Y-%m-%dT%H:%M:%S").timetuple())
    event['eventId'] = firestoreDAO.setEvent(event)
    event['infectedFootprints'] = firestoreDAO.checkFootprints(event)
    firestoreDAO.setEvent(deepcopy(event))

    # line push message------------------------------------------------------
    infectedText = {}
    for footprint in event['infectedFootprints']:
        footprint['siteName'] = firestoreDAO.getSites({'companyId': footprint['companyId'], 'id': footprint['siteId']})[0]['name']
        footprint['companyName'] = firestoreDAO.getCompanies({'companyId': footprint['companyId']})[0]['name']
        footprint['memberName'] = firestoreDAO.getMembers({'id': footprint['memberId']})[0]['name']
        footprint['infectedTime'] = str(datetime.utcfromtimestamp(footprint['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))

        if footprint['memberName'] not in infectedText.keys():
            lineId = firestoreDAO.getMembers({'id': footprint['memberId']})[0]["lineId"]
            infectedText[footprint['memberName']] = {"content": "", "lineId": lineId}
        infectedText[footprint['memberName']]["content"] += f"\n\n感染地點: {footprint['siteName']}\n感染時間: {footprint['infectedTime']}"

    for memberName in infectedText.keys():
        message = {
            "lineId": infectedText[memberName]['lineId'],
            "messageType": "textTemplate",
            "content": f"{memberName}，您已遭感染，請盡速就醫！" + infectedText[memberName]['content']
        }

        notificationThread = threading.Thread(target=line.pushMessage, args=(message,))
        notificationThread.start()
    # -----------------------------------------------------------------------
    result = {
        'eventId': event['eventId'],
        'strength': str(request.values['strength']),
        "infectedTime": str(request.values['infectedTime']).replace("T", " "),
        "amount": len(set([member['memberId'] for member in event['infectedFootprints']])),
        "siteName": firestoreDAO.getSites({'companyId': event['companyId'], 'id': event['siteId']})[0]["name"],
        "footprints": sorted(event['infectedFootprints'], key=lambda i: (i['memberName'], i['timestamp']))
    }

    return render_template('infectedFootprints.html', result=result, title="疫情調查")


# ----------------------------我的企業-----------------------------
@app.route("/myCompany/<memberId>", methods=['GET'])
@app.route("/myCompany", methods=['GET'])
def myCompany(memberId=None):
    companies = firestoreDAO.getCompanies()
    sites = firestoreDAO.getSites({'companyId': config.companyId})
    members = firestoreDAO.getMembers({'companyId': config.companyId})
    for member in members:
        if member['role'] == "customer":
            member['role'] = "顧客"
        else:
            member['role'] = "管理者"
    result = {
        'sites': sites,
        'members': members,
        'companies': companies,
        'myCompanyId': config.companyId
    }
    return render_template('myCompany.html', result=result, title='我的企業')


# ----------------------------------------------------------------
@app.route("/getCompany", methods=['POST'])
def getCompany():
    companyData = {}
    companyId = request.get_json()["companyId"]
    companyData['sites'] = firestoreDAO.getSites({'companyId': companyId})
    companyData['members'] = firestoreDAO.getMembers({'companyId': companyId})
    for member in companyData['members']:
        if member['role'] == "customer":
            member['role'] = "顧客"
        else:
            member['role'] = "管理者"
    return companyData


# ----------------------------增修商店------------------------------------
@app.route("/mySite/<companyId>", methods=['GET'])
@app.route("/mySite/<companyId>/<siteId>", methods=['GET'])
def mySite(companyId, siteId=None):
    company = firestoreDAO.getCompanies({'companyId': companyId})[0]
    site = {}
    if siteId != None:
        site = firestoreDAO.getSites({'companyId': companyId, 'id': siteId})[0]
    result = {
        'company': company,
        'site': site
    }
    return render_template('mySite.html', result=result, title='增修商店')


# ----------------------------增修商店------------------------------------
@app.route("/mySite", methods=['POST'])
def newSite():
    site = request.form.to_dict()
    sites = firestoreDAO.getSites(site)

    # inert newSite
    if sites == []:
        # - pubsub
        site['companyName'] = firestoreDAO.getCompanies({'companyId': site['companyId']})[0]['name']
        publishThread = threading.Thread(target=publish_messages, args=({'site': site},))
        publishThread.start()
    firestoreDAO.setSite(site)

    return redirect(url_for('myCompany'))


port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='127.0.0.1', port=port)
