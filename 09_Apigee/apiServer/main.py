import os
from firebase_admin import firestore, initialize_app
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.secret_key = os.urandom(24)

initialize_app()
db = firestore.client()


# --------Company--------------
@app.route("/company/<companyId>", methods=['GET'])
def getCompany(companyId):
    company_ref = db.document(f"companies/{companyId}")
    company = company_ref.get().to_dict()
    return jsonify({'response': company})


# --------Site--------------
@app.route("/site", methods=['POST'])
def setSite():
    site = request.get_json(force=True)
    # site -> {"companyId":companyId,"id":siteId,"name":siteName}
    site_ref = db.document(f"companies/{site['companyId']}/sites/{site['id']}")
    del site['companyId']
    site_ref.set(site)
    return jsonify({'response': site})


@app.route("/site/<companyId>", methods=['GET'])
def getSites(companyId):
    docs = db.collection(f"companies/{companyId}/sites").stream()
    sites = list(doc.to_dict() for doc in docs)
    return jsonify({'response': sites})


@app.route("/site/<companyId>/<siteId>", methods=['GET'])
def getSite(companyId, siteId):
    doc = db.document(f"companies/{companyId}/sites/{siteId}").get()
    site = doc.to_dict()
    return jsonify({'response': site})


# --------Member--------------
@app.route("/member", methods=['POST'])
def setMember():
    member = request.get_json(force=True)
    # member -> {'id' : memberId, 'companyId' : companyId}
    db.document(f"companies/{member['companyId']}/members/{member['id']}").set(None)
    return jsonify({'response': member})


# --------Footprint--------------
@app.route("/footprint", methods=['POST'])
def setMyFootprint():
    footprint = request.get_json(force=True)
    # footprint -> {"companyId":companyId},"siteId":siteId,"memberId":memberId,"timestamp":timestamp}
    footprint_ref = db.collection(f"companies/{footprint['companyId']}/members/{footprint['memberId']}/footprints")
    footprint['id'] = footprint_ref.add(footprint)[1].id
    footprint_ref.document(footprint['id']).update(footprint)

    site_ref = db.document(f"companies/{footprint['companyId']}/sites/{footprint['siteId']}/footprints/{footprint['id']}")
    site_ref.set(footprint)
    return jsonify({'response': footprint})


@app.route("/footprint/<companyId>/<memberId>", methods=['GET'])
def getMyFootprints(companyId, memberId):
    docs = db.collection(f"companies/{companyId}/members/{memberId}/footprints").order_by(u'timestamp').stream()
    footprints = list(doc._data for doc in docs)
    return jsonify({'response': footprints})


# --------Event--------------
@app.route("/event", methods=['POST'])
def setEvent():
    event = request.get_json(force=True)
    # event -> {"companyId":companyId, "siteId" : siteId, "infectedTime" : infectedTime, "strength":strength,"infectedFootprints":infectedFootprints}
    infectedFootprints = event["infectedFootprints"]
    del event["infectedFootprints"]
    event["eventId"] = db.collection('events').add(None)[1].id
    db.collection('events').document(event["eventId"]).update(event)
    for infectedFootprint in infectedFootprints:
        db.document(f"events/{event['eventId']}/infectedFootprints/{infectedFootprint['id']}").set(infectedFootprint)
    return jsonify({'response': event['eventId']})


# --------Check--------------
@app.route("/infected/<companyId>/<siteId>/<memberId>/<infectedTime>/<strength>", methods=['GET'])
def getInfectedFootprints(companyId, siteId, memberId, infectedTime, strength):
    if int(siteId) != 0:
        footprints_ref = db.collection(f"companies/{companyId}/{siteId}/footprints")
    elif int(memberId) != 0:
        footprints_ref = db.collection(f"companies/{companyId}/members/{memberId}/footprints")
    docs = footprints_ref.order_by(u'timestamp').where("timestamp", u">", int(infectedTime)).limit(int(strength)).get()
    footprints = [doc.to_dict() for doc in docs]
    return jsonify({'response': footprints})


port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='127.0.0.1', port=port)
