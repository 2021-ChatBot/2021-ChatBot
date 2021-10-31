from firebase_admin import credentials, firestore, initialize_app
from config import keyFile, storageBucket


class FirestoreDAO:
    def __init__(self):
        cred = credentials.Certificate(keyFile)
        initialize_app(cred, {'storageBucket': storageBucket})
        self.__db = firestore.client()

    # --------Company--------------
    def getCompanies(self, company=None) -> list:
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

    def getSites(self, site) -> list:
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
        doc = self.__db.document(f"members/{member['id']}")
        doc.update(member)

    def getMembers(self, company) -> list:
        members = []
        if "companyId" in company.keys():
            docs = self.__db.collection(f"companies/{company['companyId']}/members").stream()
            for doc in docs:
                doc = self.__db.document(f"members/{doc.id}")
                members.append(doc.get().to_dict())
        else:
            doc = self.__db.collection('members').document(company["id"])
            members.append(doc.get().to_dict())
        return members

    # --------Footprint--------------
    def setMyFootprint(self, footprint):
        footprint_ref = self.__db.collection(f"members/{footprint['memberId']}/footprints")
        footprint['id'] = footprint_ref.add(footprint)[1].id
        footprint_ref.document(footprint['id']).update(footprint)
        site_ref = self.__db.document(f"companies/{footprint['companyId']}/sites/{footprint['siteId']}/footprints/{footprint['id']}")
        site_ref.set(footprint)

    def getMyFootprints(self, event) -> list:
        footprints = []
        docs = self.__db.collection(f"members/{event['memberId']}/footprints").order_by(u'timestamp').stream()
        for doc in docs:
            footprints.append(doc._data)
        return footprints

    # --------Event--------------
    def setEvent(self, event) -> str:
        eventId = self.__db.collection('events').add(event)[1].id
        self.__db.collection('events').document(eventId).update({'id': eventId})
        for infectedFootprint in event['infectedFootprints']:
            self.__db.document(f"events/{eventId}/infectedFootprints/{infectedFootprint['id']}").set(infectedFootprint)
        return eventId

    def getEvent(self, event) -> dict:
        infectedFootprints = []
        event = self.__db.document(f"events/{event['eventId']}").get().to_dict()
        docs = self.__db.collection(f"events/{event['id']}/infectedFootprints").order_by('timestamp').stream()
        for doc in docs:
            infectedFootprints.append(doc._data)
        event["infectedFootprints"] = infectedFootprints
        return event

    def checkFootprints(self, event):
        infected = {
            'companyId': event['companyId'],
            'siteId': event['siteId'],
            'memberId': 0,
            'infectedTime': event['infectedTime'],
            'strength': event['strength'],
            'infectedFootprints': []
        }
        try:
            self.check(infected)
        except IndexError:
            pass
        return infected['infectedFootprints']

    def check(self, infected):
        if infected['strength'] > 0:
            if infected['siteId'] != 0:
                footprints_ref = self.__db.collection(f"companies/{infected['companyId']}/sites/{infected['siteId']}/footprints")
                docs = footprints_ref.order_by(u'timestamp').where("timestamp", u">", infected["infectedTime"]).limit(infected['strength']).get()
                footprints = [doc._data for doc in docs]
                infected['siteId'] = 0
                infected['memberId'] = footprints[0]['memberId']
            else:
                footprints_ref = self.__db.collection(f"members/{infected['memberId']}/footprints")
                docs = footprints_ref.order_by(u'timestamp').where("timestamp", u">", infected["infectedTime"]).limit(infected['strength']).get()
                footprints = [doc._data for doc in docs]
                infected['siteId'] = footprints[0]['siteId']
            infected['infectedTime'] = footprints[0]['timestamp']
            infected['strength'] -= 1
            infected['infectedFootprints'].extend(footprints)
            self.check(infected)
