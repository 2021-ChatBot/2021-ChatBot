from firebase_admin import credentials, firestore, initialize_app
from config import keyFile, storageBucket


class CheckFootprints:
    def __init__(self, event):
        cred = credentials.Certificate(keyFile)
        initialize_app(cred, {'storageBucket': storageBucket})
        self.__db = firestore.client()
        infected = {
            'companyId': event['companyId'],
            'siteId': event['siteId'],
            'memberId': 0,
            'infectedTime': event['infectedTime'],
            'strength': event['strength'],
            'infectedFootprints' : []
        }
        try:
            self.check(infected)
        except IndexError:
            pass
        event['infectedFootprints'] = infected['infectedFootprints']

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
