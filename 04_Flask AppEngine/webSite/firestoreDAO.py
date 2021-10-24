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
            doc = self.__db.collection("companies").document(data["companyId"])
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
        site_ref = self.__db.collection("companies").document(data["companyId"]).collection(self.siteTable).document(data["id"])
        del data["companyId"]
        site_ref.set(data)

    def getSite(self, data):
        # data{companyId,id}
        sites = []
        if "id" in data:
            doc = self.__db.collection("companies").document(data["companyId"]).collection(self.siteTable).document(data["id"])
            sites.append(doc.get().to_dict())
        else:
            docs = self.__db.collection("companies").document(data["companyId"]).collection(self.siteTable).stream()
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
            docs = self.__db.collection('companies').document(data['companyId']).collection('members').stream()
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
        footprint_ref = self.__db.collection('members').document(data["memberId"]).collection('footprints')
        footprintId = footprint_ref.add(data)[1].id
        data['id'] = footprintId
        footprint_ref.set(data)
        site_ref = self.__db.collection('companies').document(data['companyId']).collection(self.siteTable).document(data['siteId']).collection('footprints').document(footprintId)
        site_ref.set(data)

    def getFootprints(self, data):
        footprints = []
        if "infectedTime" in data.keys():
            footprints_ref = self.__db.collection('companies').document(data['companyId']).collection(self.siteTable).document(data['siteId']).collection('footprints')
            docs = footprints_ref.order_by(u'timestamp').where("timestamp", u">=", data["infectedTime"]).get()
        else:
            # data{memberId}
            docs = self.__db.collection(self.memberTable).document(data["memberId"]).collection('footprints').order_by(u'timestamp').stream()

        for doc in docs:
            footprints.append(doc._data)
        return footprints

    def getsiteFootprints(self, data):
        footprints = []
        footprints_ref = self.__db.collection('companies').document(data['companyId']).collection(self.siteTable).document(data['siteId']).collection('footprints')
        docs = footprints_ref.order_by(u'timestamp').where("timestamp", u">=", data["timestamp"]).get()
        for doc in docs:
            footprints.append(doc._data)
        return footprints

    def getmemberFootprints(self, data):
        footprints = []
        footprints_ref = self.__db.collection('members').document(data['memberId']).collection('footprints')
        docs = footprints_ref.order_by(u'timestamp').where("timestamp", u">=", data["timestamp"]).get()
        for doc in docs:
            footprints.append(doc._data)
        return footprints

    # --------Event--------------
    def setEvent(self, data):
        if "eventId" in data.keys():
            # data{eventId, infectedFootprint}
            self.__db.collection(self.eventTable).document(data['eventId']).collection("infectedFootprints").document(data['infectedFootprints']['id']).set(data['infectedFootprints'])
        else:
            # data{strength, companyId, infectedTime, siteId}
            eventId = self.__db.collection(self.eventTable).add(data)[1].id
            self.__db.collection(self.eventTable).document(eventId).update({'id': eventId})
            return eventId

    def getEvent(self, data):
        # data{eventId}
        event = self.__db.collection(self.eventTable).document(data["eventId"]).get().to_dict()
        infectedFootprints = list(doc._data for doc in self.__db.collection(self.eventTable).document(data["eventId"]).collection("infectedFootprints").stream())
        event["infectedFootprints"] = sorted(infectedFootprints, key=lambda k: k['timestamp'])
        return event
