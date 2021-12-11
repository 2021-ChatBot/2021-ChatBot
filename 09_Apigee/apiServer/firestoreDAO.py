import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
from publish import publish_messages
import threading


class FirestoreDAO:
    def __init__(self):
        initialize_app()
        self.__db = firestore.client()

    # --------Company--------------
    def getCompany(self, companyId) -> dict:
        company_ref = self.__db.document(f"companies/{companyId}")
        company = company_ref.get().to_dict()
        return company

    # --------Site--------------
    def setSite(self, site):
        site_ref = self.__db.document(f"companies/{site['companyId']}/sites/{site['id']}")
        site_ref.set(site)
        return site

    def getSites(self, site={}) -> list:
        sites = []
        if "id" in site:
            doc = self.__db.document(f"companies/{site['companyId']}/sites/{site['id']}").get()
            if doc.to_dict() != None:
                sites.append(doc.to_dict())
        else:
            docs = self.__db.collection(f"companies/{site['companyId']}/sites").stream()
            sites = list(doc.to_dict() for doc in docs)
        return sites

    # --------Member--------------
    def setMember(self, myMember) -> dict:
        # myMember -> {'lineId': lineId, 'companyId' : companyId}
        memberId = self.__db.collection("members").add(myMember)[1].id
        self.__db.document(f"members/{memberId}").update({'id': memberId})
        # create memberId in company
        self.__db.document(f"companies/{myMember['companyId']}/members/{memberId}").set(None)
        return {
            "lineId": myMember['lineId'],
            "id": memberId
        }

    def updateMember(self, member):
        doc = self.__db.document(f"members/{member['id']}")
        doc.update(member)

    def getMembers(self, myMember={}) -> list:
        members = []
        if 'id' in myMember:
            doc = self.__db.document(f"members/{myMember['id']}").get()
            if doc.to_dict() != None:
                members.append(doc.to_dict())
        elif 'email' in myMember:
            memberList = list(doc.to_dict() for doc in self.__db.collection('members').stream())
            for member in memberList:
                if member['email'] == myMember['email']:
                    members.append(member)
                    break
        else:
            memberIDs = list(doc.id for doc in self.__db.collection(f'companies/{myMember["companyId"]}/members').stream())
            for doc in self.__db.collection('members').stream():
                if doc.id in memberIDs:
                    members.append(doc.to_dict())
        return members

    # --------Footprint--------------
    def setMyFootprint(self, footprint):
        footprint_ref = self.__db.collection(f"members/{footprint['memberId']}/footprints")
        footprint['id'] = footprint_ref.add(footprint)[1].id
        footprint_ref.document(footprint['id']).update(footprint)
        site_ref = self.__db.document(f"companies/{footprint['companyId']}/sites/{footprint['siteId']}/footprints/{footprint['id']}")
        site_ref.set(footprint)
        return footprint

    def getMyFootprints(self, member) -> list:
        docs = self.__db.collection(f"members/{member['id']}/footprints").order_by(u'timestamp').stream()
        footprints = list(doc.to_dict() for doc in docs if member["companyId"] == doc.to_dict()["companyId"])
        return footprints

    # --------Event--------------
    def setEvent(self, event) -> str:
        if 'eventId' not in event.keys():
            eventId = self.__db.collection('events').add(None)[1].id
        else:
            infectedFootprints = event["infectedFootprints"]
            eventId = event['eventId']
            del event["infectedFootprints"]
            self.__db.document(f'events/{eventId}').update(event)
            for infectedFootprint in infectedFootprints:
                self.__db.document(f"events/{eventId}/infectedFootprints/{infectedFootprint['id']}").set(infectedFootprint)
        return eventId

    # --------Check--------------
    def checkFootprints(self, event):
        self.event = event
        infected = {
            'companyId': event['companyId'],
            'siteId': event['siteId'],
            'memberId': 0,
            'infectedTime': event['infectedTime'],
            'strength': event['strength'],
            'myStrength': event['strength'],
        }
        self.infectedFootprints = []
        self.check(infected)
        return self.infectedFootprints

    def check(self, infected):
        if infected['myStrength'] > 0:
            if infected['siteId'] != 0:
                footprints_ref = self.__db.collection(f"companies/{infected['companyId']}/sites/{infected['siteId']}/footprints")
                docs = footprints_ref.order_by(u'timestamp').where("timestamp", u">", infected["infectedTime"]).limit(infected['myStrength']).get()
                footprints = [doc.to_dict() for doc in docs]
            elif infected['memberId'] != 0:
                # 合併同一使用者在不同企業的足跡
                member = self.__db.document(f"members/{infected['memberId']}").get().to_dict()
                members = []
                for doc in self.__db.collection('members').stream():
                    print(doc.to_dict())
                    if doc.to_dict() and member:
                        if doc.to_dict()['lineId'] == member['lineId']:
                            members.append(doc.to_dict())
                footprints = []
                for sameMember in members:
                    footprints_ref = self.__db.collection(f"members/{sameMember['id']}/footprints")
                    docs = footprints_ref.order_by(u'timestamp').where("timestamp", u">", infected["infectedTime"]).limit(infected['myStrength']).get()
                    footprints.extend([doc.to_dict() for doc in docs])
                footprints = sorted(footprints, key=lambda i: i['timestamp'])
                footprints = footprints[:infected['myStrength'] + 1]

            for footprint in footprints:
                infected['infectedTime'] = footprint['timestamp']
                infected['myStrength'] -= 1
                if infected['siteId'] != 0:
                    infected['memberId'] = footprint['memberId']
                    infected['siteId'] = 0
                elif infected['memberId'] != 0:
                    infected['companyId'] = footprint['companyId']
                    infected['siteId'] = footprint['siteId']
                    infected['memberId'] = 0

                self.check(infected)

                if footprint not in self.infectedFootprints:
                    self.infectedFootprints.append(footprint)
                    # - publish message
                    infectedFootprint = {
                        "eventId": self.event["eventId"],
                        "companyName": self.__db.document(f"companies/{footprint['companyId']}").get().to_dict()["name"],
                        "siteId": footprint["siteId"],
                        "memberId": footprint["memberId"],
                        "footprintId": footprint["id"],
                        "strength": self.event["strength"],
                        "eventTimestamp": self.event["infectedTime"],
                        "footprintTimestamp": footprint["timestamp"]
                    }
                    publishThread = threading.Thread(target=publish_messages, args=({'infected': infectedFootprint},))
                    publishThread.start()

                infected['myStrength'] = infected['strength'] - 1
                if infected['myStrength'] == 0:
                    infected['strength'] -= 1
