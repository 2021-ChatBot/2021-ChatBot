from firebase_admin import credentials, firestore, initialize_app
from config import keyFile, storageBucket


cred = credentials.Certificate(keyFile)
initialize_app(cred, {'storageBucket': storageBucket})

class Firestore:
    def __init__(self):
        self.__db = firestore.client()

    # --------Company--------------
    def getCompany(self, company=None):
        companies = []
        if company:
            doc = self.__db.document(f"companies/{company['companyId']}")
            companies.append(doc.get().to_dict())
        else:
            docs = self.__db.collection("companies").stream()
            siteIdOfName = {}
            for doc in docs:
                siteIdOfName[doc.id] = doc._data['name']
                companies.append({"id": doc.id, "name": doc.to_dict()['name']})
        return companies

    # --------Site--------------
    def setSite(self, site):
        site_ref = self.__db.document(f"companies/{site['companyId']}/sites/{site['id']}")
        del site["companyId"]
        site_ref.set(site)

    def getSite(self, site) -> list:
        sites = []
        if "id" in site:
            doc = self.__db.document(f"companies/{site['companyId']}/sites/{site['id']}").get()
            if doc != None:
                sites.append(doc.to_dict())
        else:
            docs = self.__db.collection(f"companies/{site['companyId']}/sites").stream()
            for doc in docs:
                sites.append(doc._data)
        return sites


    # --------Member--------------
    def updateMember(self, member):
        doc = self.__db.collection("members").document(member['id'])
        doc.update(member)

    def getMember(self, company):
        members = []
        if "companyId" in company.keys():
            docs = self.__db.collection(f"companies/{company['companyId']}/members").stream()
            for doc in docs:
                doc = self.__db.collection('members').document(doc.id)
                members.append(doc.get().to_dict())
        elif 'id' not in company:
            docs = self.__db.collection('members').stream()
            for doc in docs:
                members.append(doc._data)
        else:
            doc = self.__db.collection('members').document(company["id"])
            members.append(doc.get().to_dict())
        return members

    # --------Footprint--------------
    def setMyFootprint(self, footprint):
        footprint_ref = self.__db.collection(f"members/{footprint['memberId']}/footprints")
        footprintId = footprint_ref.add(footprint)[1].id
        footprint['id'] = footprintId
        footprint_ref.document(footprintId).update(footprint)
        site_ref = self.__db.document(f"companies/{footprint['companyId']}/sites/{footprint['siteId']}/footprints/{footprintId}")
        site_ref.set(footprint)

    def getMyFootprints(self, event):
        footprints = []
        docs = self.__db.collection(f"members/{event['memberId']}/footprints").order_by(u'timestamp').stream()
        for doc in docs:
            footprints.append(doc._data)
        return footprints

    # --------Event--------------
    def setEvent(self, event):
        if "eventId" in event.keys():
            for infectedFootprint in event['infectedFootprints']:
                self.__db.document(f"events/{event['eventId']}/infectedFootprints/{infectedFootprint['id']}").set(infectedFootprint)
        else:
            eventId = self.__db.collection("events").add(event)[1].id
            self.__db.collection("events").document(eventId).update({'id': eventId})
            return eventId

    def getEvent(self, event) -> dict:
        infectedFootprints =[]
        event = self.__db.document(f"events/{event['eventId']}").get().to_dict()
        docs = self.__db.collection(f"events/{event['id']}/infectedFootprints").order_by('timestamp').stream()
        for doc in docs:
            infectedFootprints.append(doc._data)
        event["infectedFootprints"] = infectedFootprints
        return event

