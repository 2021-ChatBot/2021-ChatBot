from firebase_admin import firestore, initialize_app


class FirestoreDAO:
    def __init__(self):
        initialize_app()
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
            if doc._data != None:
                sites.append(doc.to_dict())
        else:
            docs = self.__db.collection(f"companies/{site['companyId']}/sites").stream()
            for doc in docs:
                sites.append(doc._data)
        return sites

    # --------Member--------------
    def createMember(self, myMember):
        myMember['role'] = 'customer'
        companyId = myMember['companyId']
        del myMember['companyId']
        memberCollection = self.__db.collection("members")
        memberList = list(doc._data for doc in memberCollection.stream())
        for member in memberList:
            if member["lineId"] == myMember['lineId']:
                return member


        # create member
        memberId = memberCollection.add(myMember)[1].id
        memberCollection.document(memberId).update({'id': memberId})

        # create memberid in company
        self.__db.document(f"companies/{companyId}/members/{memberId}").set(None)
        return {
            "name": myMember['name'],
            "lineId": myMember['lineId'],
            "id": memberId
        }

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
        return footprint

    def getMyFootprints(self, event) -> list:
        footprints = []
        docs = self.__db.collection(f"members/{event['memberId']}/footprints").order_by(u'timestamp').stream()
        for doc in docs:
            footprints.append(doc._data)
        return footprints

    # --------Event--------------
    def setEvent(self, event) -> str:
        infectedFootprints = event["infectedFootprints"]
        del event["infectedFootprints"]
        eventId = self.__db.collection('events').add(event)[1].id
        self.__db.collection('events').document(eventId).update({'id': eventId})
        for infectedFootprint in infectedFootprints:
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

    # --------Check--------------
    def checkFootprints(self, event):
        infected = {
            'companyId': event['companyId'],
            'siteId': event['siteId'],
            'memberId': 0,
            'infectedTime': event['infectedTime'],
            'strength' : event['strength'],
            'myStrength' : event['strength'],
        }
        self.infectedFootprints = []
        self.check(infected)
        return self.infectedFootprints

    def check(self, infected):
        if infected['myStrength'] > 0:
            if infected['siteId'] != 0:
                footprints_ref = self.__db.collection(f"companies/{infected['companyId']}/sites/{infected['siteId']}/footprints")
                docs = footprints_ref.order_by(u'timestamp').where("timestamp", u">", infected["infectedTime"]).limit(infected['myStrength']).get()
                footprints = [doc._data for doc in docs]
            elif infected['memberId'] != 0:
                footprints_ref = self.__db.collection(f"members/{infected['memberId']}/footprints")
                docs = footprints_ref.order_by(u'timestamp').where("timestamp", u">", infected["infectedTime"]).limit(infected['myStrength']).get()
                footprints = [doc._data for doc in docs]
            for footprint in footprints:
                infected['infectedTime'] = footprint['timestamp']
                infected['myStrength'] -= 1
                if infected['siteId'] != 0:
                    infected['memberId'] = footprint['memberId']
                    infected['siteId'] = 0
                elif infected['memberId'] != 0:
                    infected['siteId'] = footprint['siteId']
                    infected['memberId'] = 0

                self.check(infected)

                if footprint not in self.infectedFootprints:
                    self.infectedFootprints.append(footprint)
                infected['myStrength'] = infected['strength'] - 1
                if infected['myStrength'] == 0:
                    infected['strength'] -= 1