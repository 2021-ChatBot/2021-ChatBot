from firebase_admin import credentials, firestore, initialize_app
from config import Config

config = Config()

cred = credentials.Certificate(config.firebase()['keyFile'])
initialize_app(cred, {'storageBucket': config.firebase()['storageBucket']})


class Firestore:
    def __init__(self):
        self.__db = firestore.client()
        self.siteTable = config.firebase()['siteTable']
        self.memberTable = config.firebase()['memberTable']
        self.eventTable = config.firebase()['eventTable']

    # --------Company--------------
    def getCompany(self, data=None):
        # data{companyId}
        companies = []
        if data:
            doc = self.__db.document(f"companies/{data['companyId']}")
            companies.append(doc.get().to_dict())
        else:
            docs = self.__db.collection("companies").stream()
            siteIdOfName = {}
            for doc in docs:
                siteIdOfName[doc.id] = doc._data['name']
                companies.append({"id": doc.id, "name": doc.to_dict()['name']})
        return companies

    # --------Site--------------
    def setSite(self, data):
        # data{companyId,id,name}
        site_ref = self.__db.document(f"companies/{data['companyId']}/{self.siteTable}/{data['id']}")
        del data["companyId"]
        site_ref.set(data)

    def getSite(self, data):
        # data{companyId,id}
        sites = []
        if "id" in data:
            doc = self.__db.document(f"companies/{data['companyId']}/{self.siteTable}/{data['id']}")
            sites.append(doc.get().to_dict())
        else:
            docs = self.__db.collection(f"companies/{data['companyId']}/{self.siteTable}").stream()
            for doc in docs:
                sites.append(doc._data)
        return sites

    # --------Member--------------
    def updateMember(self, data):
        # data{id,lineId,name,role}
        doc = self.__db.collection("members").document(data['id'])
        doc.update(data)

    def getMember(self, data):
        # data{id,companyId}
        members = []
        if "companyId" in data.keys():
            docs = self.__db.collection(f"companies/{data['companyId']}/members").stream()
            for doc in docs:
                doc = self.__db.collection('members').document(doc.id)
                members.append(doc.get().to_dict())
        elif 'id' not in data:
            docs = self.__db.collection('members').stream()
            for doc in docs:
                members.append(doc._data)
        else:
            doc = self.__db.collection('members').document(data["id"])
            members.append(doc.get().to_dict())
        return members

    # --------Footprint--------------
    def setFootprint(self, data):
        # data{memberId, siteId, companyId, timestamp}
        footprint_ref = self.__db.collection(f"members/{data['memberId']}/footprints")
        footprintId = footprint_ref.add(data)[1].id
        data['id'] = footprintId
        footprint_ref.document(footprintId).update(data)
        site_ref = self.__db.document(f"companies/{data['companyId']}/{self.siteTable}/{data['siteId']}/footprints/{footprintId}")
        site_ref.set(data)

    def getFootprints(self, data):
        footprints = []
        if "infectedTime" in data.keys():
            footprints_ref = self.__db.collection(f"companies/{data['companyId']}/{self.siteTable}/{data['siteId']}/footprints")
            docs = footprints_ref.order_by(u'timestamp').where("timestamp", u">=", data["infectedTime"]).limit(1).get()
        else:
            # data{memberId}
            docs = self.__db.collection(f"{self.memberTable}/{data['memberId']}/footprints").order_by(u'timestamp').stream()
        for doc in docs:
            footprints.append(doc._data)
        return footprints

    def getsiteFootprint(self, data):
        footprints_ref = self.__db.collection(f"companies/{data['companyId']}/{self.siteTable}/{data['siteId']}/footprints")
        footprint = footprints_ref.order_by(u'timestamp').where("timestamp", u">", data["timestamp"]).limit(1).get()
        if len(footprint) == 0:
            return {}
        return footprint[0].to_dict()


    def getmemberFootprint(self, data):
        footprints_ref = self.__db.collection(f"members/{data['memberId']}/footprints")
        footprint = footprints_ref.order_by(u'timestamp').where("timestamp", u">", data["timestamp"]).limit(1).get()
        if len(footprint) == 0:
            return {}
        return footprint[0].to_dict()

    # --------Event--------------
    def setEvent(self, data):
        if "eventId" in data.keys():
            # data{eventId, infectedFootprint}
            for infectedFootprint in data['infectedFootprints']:
                self.__db.document(f"{self.eventTable}/{data['eventId']}/infectedFootprints/{infectedFootprint['id']}").set(infectedFootprint)
        else:
            # data{strength, companyId, infectedTime, siteId}
            eventId = self.__db.collection(self.eventTable).add(data)[1].id
            self.__db.collection(self.eventTable).document(eventId).update({'id': eventId})
            return eventId

    def getEvent(self, data) -> dict:
        # data{eventId}
        infectedFootprints =[]
        event = self.__db.document(f"{self.eventTable}/{data['eventId']}").get().to_dict()
        docs = self.__db.collection(f"{self.eventTable}/{data['eventId']}/infectedFootprints").order_by('timestamp').stream()
        for doc in docs:
            infectedFootprints.append(doc._data)
        event["infectedFootprints"] = infectedFootprints
        return event

