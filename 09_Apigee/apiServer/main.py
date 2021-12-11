# -*- coding: utf-8 -*-
import os
from copy import deepcopy
from flask import Flask, request, jsonify
import threading
from firestoreDAO import FirestoreDAO
from publish import publish_messages

firestoreDAO = FirestoreDAO()
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.secret_key = os.urandom(24)


# ----------------------member-----------------------------------------
@app.route("/member", methods=['POST'])
def member():
    # ----------------------註冊綁定--------------------------------
    if request.method == 'POST':
        memberData = request.get_json(force=True)
        # memberData -> {'lineId': lineId, 'companyId' : companyId}
        companyId = memberData['companyId']
        del memberData['companyId']
        member = firestoreDAO.setMember(memberData)

        # - pubsub
        member["companyName"] = firestoreDAO.getCompany(companyId)['name']
        publishThread = threading.Thread(target=publish_messages, args=({"member": member},))
        publishThread.start()

        return jsonify({'response': member['id']})

# ----------------------footprint-----------------------------------------
@app.route("/footprint/<companyId>/<memberId>", methods=['GET'])
@app.route("/footprint", methods=['POST'])
def footprint(companyId=None, memberId=None):
    # ----------------------我的足跡--------------------------------
    if request.method == 'GET':
        footprints = firestoreDAO.getMyFootprints({'companyId' : companyId, 'id': memberId})
        return jsonify({'response': footprints})

    # ----------------------實聯掃碼--------------------------------
    if request.method == 'POST':
        footprintData = request.get_json(force=True)
        # footprintData -> {'memberId': memberId, 'siteId': siteId, 'companyId': companyId, 'timestamp': timestamp}
        footprint = firestoreDAO.setMyFootprint(footprintData)

        # - pubsub
        footprint["companyName"] = firestoreDAO.getCompany(footprintData['companyId'])['name']
        publishThread = threading.Thread(target=publish_messages, args=({'footprint': footprint},))
        publishThread.start()
        return jsonify({'response': 'success'})


# ----------------------company-----------------------------------------
@app.route("/company/<companyId>", methods=['GET'])
def company(companyId=None):
    if request.method == 'GET':
        myCompany = firestoreDAO.getCompany(companyId)
        return jsonify({'response': myCompany})


# ----------------------site-----------------------------------------
@app.route("/site/<companyId>/<siteId>", methods=['GET'])
@app.route("/site/<companyId>", methods=['GET'])
@app.route("/site", methods=['POST'])
def site(companyId=None, siteId=None):
    if request.method == 'GET':
        if siteId == None:
            sites = firestoreDAO.getSites({'companyId':companyId})
        else:
            sites = firestoreDAO.getSites({'companyId' : companyId, 'id': siteId})
        return jsonify({'response': sites})

    if request.method == 'POST':
        siteData = request.get_json(force=True)
        # siteData -> {'id': siteId, 'name': name, 'companyId':companyId}
        sites = firestoreDAO.getSites(siteData)
        firestoreDAO.setSite(siteData)
        if sites == []:
            # - pubsub
            siteData['companyName'] = firestoreDAO.getCompany(siteData['companyId'])['name']
            publishThread = threading.Thread(target=publish_messages, args=({'site': siteData},))
            publishThread.start()
        return jsonify({'response': 'success'})


# ----------------------setEvent-----------------------------------------
@app.route("/event", methods=['POST'])
def setEvent():
    eventData = request.get_json(force=True)
    eventData['eventId'] = firestoreDAO.setEvent(eventData)
    eventData['infectedFootprints'] = firestoreDAO.checkFootprints(eventData)
    firestoreDAO.setEvent(deepcopy(eventData))
    return jsonify({'response': eventData})


port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='127.0.0.1', port=port)
