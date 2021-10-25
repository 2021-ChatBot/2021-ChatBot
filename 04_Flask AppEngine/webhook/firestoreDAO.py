from config import firebaseKey,memberTableName, companyId
from firebase_admin import credentials, firestore, initialize_app

cred = credentials.Certificate(firebaseKey)
app=initialize_app(cred)
dbPath = firestore.client()

def postMember(memberName ,lineId):
    member = {
        "name" : memberName,
        "lineId" : lineId,
        "role" : "customer"
    }
    memberCollection = dbPath.collection(memberTableName)
    memberList = list(doc._data for doc in memberCollection.stream())
    for memberdata in memberList:
        print(memberdata)
        if memberdata["lineId"] == lineId:
            return memberdata
    # create memberdata in members
    memberId = memberCollection.add(member)[1].id
    memberCollection.document(memberId).update({'id' : memberId})

    # create memberid in company
    dbPath.collection("companies").document(companyId).collection("members").document(memberId).set(None)

    return {
        "name" : memberName,
        "lineId" : lineId,
        "id" : memberId
    }
