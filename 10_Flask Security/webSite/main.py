# -*- coding: utf-8 -*-
import os
import re
import json
import time
import uuid

from datetime import datetime, timedelta
import threading
from copy import deepcopy

from config import *
from checker import check
from lineAPI import PushMessage
from apiClient import requestAPI
from publish import publish_messages

from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask.json import JSONEncoder
from flask_sqlalchemy import SQLAlchemy
from flask_security.utils import hash_password
from flask_security import (
        Security,
        RoleMixin,
        UserMixin,
        SQLAlchemyUserDatastore,
        login_required,
        login_user,
        auth_required,
        current_user,
        roles_accepted,
        roles_required,
        logout_user,
)

line = PushMessage()

# Cloud SQL
url = 'mysql+pymysql://'+USER_NAME+':'+PASSWORD+'@localhost/'+DBNAME+'?unix_socket=/cloudsql/'+CONNECT_NAME

# Create app
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["SQLALCHEMY_DATABASE_URI"] = url
app.json_encoder = JSONEncoder
for i in flaskConfig:
    app.config[i] = flaskConfig[i]

# Create database connection object
db = SQLAlchemy(app)

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    lineId = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    fs_uniquifier =	db.Column(db.String(255))
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

# Setup Flask-Security
userDatabase = SQLAlchemyUserDatastore(db, User, Role)
app.security = Security(app, userDatabase)
# ----------------------------------------------------------------------
def getUserData(user):
    member = {}
    attrs = ("id", "email", "name", "lineId")
    for attr in attrs:
        member[attr] = getattr(user, attr)
    member["role"] = user.roles[0].name
    return member
# ----------------------------------------------------------------------
@app.route("/index", methods=['GET'])
def index():
    return render_template("index.html")
# ----------------------------------------------------------------------
@app.route("/", methods=['GET'])
def liff():
    return render_template("liff.html",liffId = liffId)
# ----------------------成員註冊-----------------------------------------
@app.route("/signUp", methods=['GET', 'POST'])
def signUp():
    if request.method == 'GET':
        return render_template("signUp.html",liffId = liffId)
    if request.method == 'POST':
        userData = request.form.to_dict()
        lineIdQuery = User.query.filter_by(lineId = userData['lineId']).first()
        try:
            if lineIdQuery != None and userData['lineId'] != "":
                return render_template("signUpFail.html", title="註冊失敗 您已經重複註冊") 
            user = userDatabase.create_user(
                id=str(uuid.uuid4()), email=userData['email'], password=hash_password(userData['password']),
                name=userData['name'], lineId=userData['lineId'], roles=["customer"]
            )
            db.session.commit()
            login_user(user)
            member = getUserData(user)
            # - pubsub                
            member["companyName"] = requestAPI("GET", "/company/" + companyId)['name']
            publishThread = threading.Thread(target=publish_messages, args=({"member": member},))
            publishThread.start()
            if userData['lineId'] != "" :
                message = {
                    "lineId": member['lineId'],
                    "messageType": "textTemplate",
                    "content": "註冊綁定成功\n"
                            f"name: {member['name']}\n"
                            f"email: {member['email']}\n"
                            f"lineId: {member['lineId']}\n\n"
                            f"本系統提供下列功能：\n"
                            f"1. 實聯掃碼\n"
                            f"2. 我的足跡\n"
                            f"3. 我的個資\n"
                            f"4. 組織管理\n"
                            f"5. 疫調管理\n"
                            f"6. 統計報表\n"
                            f"請利用主選單，點選需要的服務......"
                }
                notificationThread = threading.Thread(target=line.pushMessage, args=(message,))
                notificationThread.start()

            return render_template("signUpSucess.html",member = member, title="註冊成功")
        except:
            return render_template("signUpFail.html", title="註冊失敗") 

# ----------------------成員綁定-----------------------------------------
@app.route("/binding", methods=['GET', 'POST'])
@auth_required()
@roles_accepted("customer", "manager", "admin")
def binding():
    if request.method == 'GET':
        member = getUserData(current_user)
        return render_template("binding.html",member = member,liffId = liffId)

    elif request.method == 'POST':
        lineId = request.form.to_dict()['lineId']
        current_user.lineId = lineId
        db.session.commit()
        member = getUserData(current_user)
        message = {
            "lineId": lineId,
            "messageType": "textTemplate",
            "content": "綁定成功\n"
                    f"name: {member['name']}\n"
                    f"email: {member['email']}\n"
                    f"lineId: {member['lineId']}\n\n"
                    f"本系統提供下列功能：\n"
                    f"1. 實聯掃碼\n"
                    f"2. 我的足跡\n"
                    f"3. 我的個資\n"
                    f"4. 組織管理\n"
                    f"5. 疫調管理\n"
                    f"6. 統計報表\n"
                    f"請利用主選單，點選需要的服務......"
        }
        notificationThread = threading.Thread(target=line.pushMessage, args=(message,))
        notificationThread.start()

        return redirect(url_for('index'))
# ----------------------個人資料-----------------------------------------
@app.route("/myData", methods=['GET', 'POST'])
@auth_required()
@roles_accepted("customer", "manager", "admin")
def myData():
    member = getUserData(current_user)
    if request.method == 'GET': 
        return render_template('myData.html', member=member, title="我的個資")
    if request.method == 'POST':
        userData = request.form.to_dict()
        if member['role'] != userData['role']:   
            userDatabase.remove_role_from_user(current_user, member['role']) 
            userDatabase.add_role_to_user(current_user, userData['role'])
        db.session.commit()
        return redirect("/myData")  

# ----------------------修改個資-----------------------------------------
@app.route("/myForm", methods=['GET'])
@auth_required()
@roles_accepted("customer", "manager", "admin")
def myForm():
    member = getUserData(current_user)
    return render_template('myForm.html', member=member, title="修改個資")

# ----------------------掃碼---------------------------------------------
@app.route("/newFootprint", methods=['GET'])
@auth_required()
@roles_required("customer")
def newFootprint():
    return render_template('newFootprint.html', title="實聯掃碼")

# ----------------------寫入掃碼足跡紀錄-----------------------------------
@app.route("/newFootprint", methods=['POST'])
@auth_required()
@roles_required("customer")
def setMyFootprint():
    footprintData = json.loads(request.get_data())
    siteIdRegex = re.compile(r'\d\d\d\d \d\d\d\d \d\d\d\d \d\d\d')
    member = getUserData(current_user)
    try:
        siteId = siteIdRegex.findall(footprintData['siteData'])[0]
        importTime = int(time.time() + 28800)
    except:
        return jsonify('這不是實聯制QRcode')
    site = requestAPI("GET", "/site/"+ companyId + "/" + siteId)
    if site != None:
        message = {
            "lineId": member['lineId'],
            "messageType": "textTemplate",
            "content": "掃碼成功\n"
                       f"商店: {site['name']}\n"
                       f"時間: {str(datetime.utcfromtimestamp(importTime).strftime('%Y-%m-%d %H:%M:%S'))}"
        }
        notificationThread = threading.Thread(target=line.pushMessage, args=(message,))
        notificationThread.start()

        # - firestore
        footprint = {
            'memberId': member['id'],
            'siteId': siteId,
            'companyId': companyId,
            'timestamp': importTime
        }
        footprint['id'] = requestAPI("POST", "/footprint", footprint)['id']

        # - pubsub
        footprint["companyName"] = requestAPI("GET", "/company/" + companyId)['name']
        publishThread = threading.Thread(target=publish_messages, args=({'footprint': footprint},))
        publishThread.start()
        return jsonify(site['name'] + '  到店掃碼成功')
    return jsonify('這不是實聯制QRcode')


# ----------------------------User掃碼足跡紀錄-----------------------------
@app.route("/myFootprints", methods=['GET'])
@auth_required()
@roles_required("customer")
def myFootprints():
    member = getUserData(current_user)
    companyName = requestAPI("GET", "/company/" + companyId)['name']
    footprints = requestAPI("GET", "/footprint/" + companyId + "/" + member['id'])
    for footprint in footprints:
        footprint['companyName'] = companyName
        footprint['siteName'] = requestAPI("GET", "/site/" + companyId + "/" + footprint['siteId'])['name']
        footprint['timestamp'] = str(datetime.utcfromtimestamp(footprint['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))
    return render_template('myFootprints.html', footprints=footprints, title="足跡列表")
    
# ----------------------------我的企業-----------------------------
@app.route("/myCompany", methods=['GET'])
@auth_required()
@roles_required("manager")
def myCompany():
    company = requestAPI("GET", "/company/" + companyId)
    sites = requestAPI("GET", "/site/"+ companyId)
    users = User.query.filter().all()
    members = []
    for user in users:
        member = getUserData(user) 
        members.append(member)
    result = {
        'sites': sites,
        'members': members,
        'company': company
    }
    return render_template('myCompany.html', result=result, title='我的企業')

# ----------------------------增修商店------------------------------------
@app.route("/mySite", methods=['GET'])
@app.route("/mySite/<siteId>", methods=['GET'])
@auth_required()
@roles_required("manager")
def mySite(siteId=None):
    result = {
        'company': requestAPI("GET", "/company/" + companyId),
        'site': None,
    }
    if siteId != None:
        result['site'] = requestAPI("GET", "/site/" + companyId + "/" + siteId)  
    return render_template('mySite.html', result=result, title='增修商店')

# ----------------------------增修商店------------------------------------
@app.route("/mySite", methods=['POST'])
@auth_required()
@roles_required("manager")
def newSite():
    site = request.form.to_dict()
    site['companyId'] = companyId
    exist = requestAPI("GET", "/site/" + companyId + "/" + site['id']) 
    if exist == None: 
        # - pubsub
        site['companyName'] = requestAPI("GET", "/company/" + companyId)['name']
        publishThread = threading.Thread(target=publish_messages, args=({'site': site},))
        publishThread.start()
        del site['companyName']
    requestAPI("POST", "/site", site)
    return redirect(url_for('myCompany'))


# ----------------------------疫情調查設定-----------------------------
@app.route("/checkFootprints", methods=['GET'])
@auth_required()
@roles_required("admin")
def checkFootprints():
    companyName = requestAPI("GET", "/company/" + companyId)['name']
    sites = requestAPI("GET", "/site/" + companyId)
    return render_template('checkFootprints.html', sites=sites, companyName=companyName, title="疫情調查")


# ----------------------------疫情調查結果-----------------------------
@app.route("/infectedFootprints", methods=['POST'])
@auth_required()
@roles_required("admin")
def infectedFootprints():
    event = request.form.to_dict()
    event['companyId'] = companyId
    event['strength'] = int(event['strength'])
    event['infectedTime'] = int(time.mktime(datetime.strptime(request.values['infectedTime'], "%Y-%m-%dT%H:%M:%S").timetuple()))
    
    infected = deepcopy(event)
    infected['memberId'] = 0
    infected['myStrength'] = event['strength']
    infected['infectedFootprints'] = []
    
    check(infected)
    event['infectedFootprints'] = infected['infectedFootprints']   
    event['eventId'] = requestAPI("POST", "/event" , event)

    # line push message------------------------------------------------------
    infectedText = {}
    companyName = requestAPI("GET", "/company/" + companyId)['name']
    for footprint in event['infectedFootprints']:
        # - pubsub
        infectedFootprint = {
            "eventId": event['eventId'],
            "companyName": companyName,
            "siteId": footprint["siteId"],
            "memberId": footprint["memberId"],
            "footprintId": footprint["id"],
            "strength": event["strength"],
            "eventTimestamp": event["infectedTime"],
            "footprintTimestamp": footprint["timestamp"]
        }
        publishThread = threading.Thread(target=publish_messages, args=({'infected': infectedFootprint},))
        publishThread.start()

        #---        
        footprint['siteName'] = requestAPI("GET","/site/" + companyId + "/" + footprint['siteId'])['name']
        footprint['companyName'] = companyName
        # SQL get member name
        footprint['memberName'] = User.query.filter_by(id = footprint['memberId']).first().name
        footprint['infectedTime'] = str(datetime.utcfromtimestamp(footprint['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))

        if footprint['memberName'] not in infectedText.keys():
            # SQL get member lineId
            lineId = User.query.filter_by(id = footprint['memberId']).first().lineId
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
        "siteName": requestAPI("GET", "/site/" + companyId + "/" + event['siteId'])["name"],
        "footprints": sorted(event['infectedFootprints'], key=lambda i: (i['memberName'], i['timestamp']))
    }
    return render_template('infectedFootprints.html', result=result, title="疫情調查")

# ----------------------------data studio-----------------------------
@app.route("/report", methods=['GET'])
@auth_required()
@roles_accepted("manager", "admin")
def myReport():
    return render_template('dataStudio.html', report=report)


port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='127.0.0.1', port=port)
