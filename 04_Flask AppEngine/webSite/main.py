import os
import re
from flask import Flask, request, render_template, jsonify, url_for, redirect
import json
import time
from datetime import datetime
import threading
import config
from lineAPI import PushMessage
from firestoreDAO import Firestore
from check import CheckFootprints


firestore = Firestore()
line = PushMessage()
app = Flask(__name__)
app.secret_key = os.urandom(24)


# ----------------------個人資料-----------------------------------------
@app.route("/myData/<memberId>", methods=['GET', 'POST'])
def myData(memberId):
    if request.method == 'GET':
        member = firestore.getMembers({'id': memberId})[0]
    if request.method == 'POST':
        member = request.form.to_dict()
        member['id'] = memberId
        firestore.updateMember(member)
        member = firestore.getMembers({'id': memberId})[0]
    return render_template('myData.html', member=member, title="我的個資")


@app.route("/myForm/<memberId>", methods=['GET'])
def myForm(memberId):
    member = firestore.getMembers({'id': memberId})[0]
    return render_template('myForm.html', member=member, title="修改個資")


# ----------------------掃碼---------------------------------------------
@app.route("/newFootprint/<memberId>", methods=['GET'])
def newFootprint(memberId):
    return render_template('newFootprint.html', memberId=memberId, title="實聯掃碼")


# ----------------------寫入掃碼足跡紀錄-----------------------------------
@app.route("/newFootprint", methods=['POST'])
def setMyFootprint():
    footprint = json.loads(request.get_data())
    siteIdRegex = re.compile(r'\d\d\d\d \d\d\d\d \d\d\d\d \d\d\d')
    try:
        siteId = siteIdRegex.findall(footprint['siteInfo'])[0]
        memberId = footprint['memberId']
        importTime = int(time.time() + 28800)
    except:
        return jsonify('這不是實聯制QRcode')
    companies = firestore.getCompanies()
    for company in companies:
        sites = firestore.getSites({'companyId': company['id'], 'id': siteId})
        if sites[0] != None:
            message = {
                "lineId": firestore.getMembers({'id': memberId})[0]['lineId'],
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
            firestore.setMyFootprint(footprint)

            return jsonify(sites[0]['name'] + '  到店掃碼成功')

    return jsonify('這不是實聯制QRcode')


# ----------------------------User掃碼足跡紀錄-----------------------------
@app.route("/myFootprints/<memberId>", methods=['GET'])
def getMyFootprint(memberId):
    footprints = []

    for footprint in firestore.getMyFootprints({'memberId': memberId}):
        footprints.append(
            {
                'companyName': firestore.getCompanies({'companyId': footprint['companyId']})[0]['name'],
                'siteName': firestore.getSites({'companyId': footprint['companyId'], 'id': footprint['siteId']})[0]['name'],
                'timestamp': str(datetime.utcfromtimestamp(footprint['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))
            }
        )
    return render_template('myFootprints.html', footprints=footprints, title="足跡列表")


# ----------------------------data studio-----------------------------
@app.route("/report/<memberId>", methods=['GET'])
def report(memberId):
    return render_template('dataStudio.html')


# ----------------------------疫情調查設定-----------------------------
@app.route("/checkFootprints/<memberId>", methods=['GET'])
def checkFootprints(memberId):
    sites = {}
    companies = firestore.getCompanies()
    for company in companies:
        for site in firestore.getSites({'companyId': company['id']}):
            sites.update({f"{company['id']}-{site['id']}": f'{company["name"]} {site["name"]}'})
    return render_template('checkFootprints.html', sites=sites, title="疫情調查")


# ----------------------------疫情調查結果-----------------------------
@app.route("/infectedFootprints", methods=['POST'])
def infectedFootprints():
    event = request.form.to_dict()
    event['companyId'], event['siteId'] = event['siteId'].split('-')
    event['strength'] = int(event['strength'])
    event['infectedTime'] = time.mktime(datetime.strptime(request.values['infectedTime'], "%Y-%m-%dT%H:%M:%S").timetuple()) + 28800
    CheckFootprints(event)
    event['eventId'] = firestore.setEvent(event)
    infectedFootprints = event['infectedFootprints']
    # line push message------------------------------------------------------
    infectedText = {}

    for infectedMember in infectedFootprints:
        infectedMember['siteName'] = firestore.getSites({'companyId': infectedMember['companyId'], 'id': infectedMember['siteId']})[0]['name']
        infectedMember['companyName'] = firestore.getCompanies({'companyId': infectedMember['companyId']})[0]['name']
        infectedMember['name'] = firestore.getMembers({'id': infectedMember['memberId']})[0]['name']
        infectedMember['infectedTime'] = str(datetime.utcfromtimestamp(infectedMember['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))
        if infectedMember['name'] not in infectedText.keys():
            infectedMemberlineId = firestore.getMembers({'id': infectedMember['memberId']})[0]["lineId"]
            infectedText[infectedMember['name']] = {"content": "", "lineId": infectedMemberlineId}
        infectedText[infectedMember['name']]["content"] += f"\n\n感染地點: {infectedMember['siteName']}\n感染時間: {infectedMember['infectedTime']}"

    for member in infectedText.keys():
        message = {
            "lineId": infectedText[member]['lineId'],
            "messageType": "textTemplate",
            "content": f"{member}，您已遭感染，請盡速就醫！" + infectedText[member]['content']
        }

        notificationThread = threading.Thread(target=line.pushMessage, args=(message,))
        notificationThread.start()
    # -----------------------------------------------------------------------
    result = {
        'eventId': event['eventId'],
        'strength': str(request.values['strength']),
        "infectedTime": str(request.values['infectedTime']).replace("T", " "),
        "amount": len(set([member['memberId'] for member in infectedFootprints])),
        "name": firestore.getSites({'companyId': event['companyId'], 'id': event['siteId']})[0]["name"]
    }
    infectedFootprints = sorted(infectedFootprints, key=lambda i: i['name'])
    return render_template('infectedFootprints.html', infectedList=infectedFootprints, result=result, title="疫情調查")


# ----------------------------我的企業-----------------------------
@app.route("/myCompany/<memberId>", methods=['GET'])
@app.route("/myCompany", methods=['GET'])
def myCompany(memberId=None):
    companies = firestore.getCompanies()
    company = {}
    company["sites"] = firestore.getSites({'companyId': config.companyId})
    company["members"] = firestore.getMembers({'companyId': config.companyId})
    for member in company["members"]:
        if member['role'] == "customer":
            member['role'] = "顧客"
        else:
            member['role'] = "管理者"
    return render_template('myCompany.html', company=company, companies=companies, companyId=config.companyId, title='我的企業')


# ----------------------------------------------------------------
@app.route("/getCompany", methods=['POST'])
def getCompany():
    companyId = request.get_json()["companyId"]
    company = {}
    company["sites"] = firestore.getSites({'companyId': companyId})
    company["members"] = firestore.getMembers({'companyId': companyId})
    for member in company["members"]:
        if member['role'] == "customer":
            member['role'] = "顧客"
        else:
            member['role'] = "管理者"
    return company


# ----------------------------增修商店------------------------------------
@app.route("/mySite/<companyId>", methods=['GET'])
@app.route("/mySite/<companyId>/<siteId>", methods=['GET'])
def mySite(companyId, siteId=None):
    company = firestore.getCompanies({'companyId': companyId})[0]
    site = {}
    if siteId != None:
        site = firestore.getSites({'companyId': companyId, 'id': siteId})[0]

    return render_template('mySite.html', company=company, site=site, title='增修商店')


# ----------------------------增修商店------------------------------------
@app.route("/mySite", methods=['POST'])
def newSite():
    site = request.form.to_dict()
    firestore.setSite(site)
    return redirect(url_for('myCompany'))


port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='127.0.0.1', port=port)
