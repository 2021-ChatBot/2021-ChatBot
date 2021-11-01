from config import firestoreKey, companyId, role
from firebase_admin import credentials, firestore, initialize_app

cred = credentials.Certificate(firestoreKey)
app=initialize_app(cred)
dbPath = firestore.client()

def postMember(memberName ,lineId):
    member = {
        "name" : memberName,
        "lineId" : lineId,
        "role" : role
    }
    memberCollection = dbPath.collection('members')
    memberList = list(doc._data for doc in memberCollection.stream())
    for member in memberList:
        if member["lineId"] == lineId:
            return member
    # create member
    memberId = memberCollection.add(member)[1].id
    memberCollection.document(memberId).update({'id' : memberId})
    member['id'] = memberId
    # create memberid in company
    dbPath.document(f"companies/{companyId}/members/{memberId}").set(None)
    
    return member