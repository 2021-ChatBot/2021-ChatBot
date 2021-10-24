from firestoreDAO import Firestore

class CheckFootprints:
    def __init__(self, event):
        self.__firestore = Firestore()
        self.check(event)


    def check(self, event):
        if event['strength'] >= 0:
            count = event['strength']
            siteFootprints = self.__firestore.getFootprints(event)
            for sitefootprint in siteFootprints:
                if count >= 0:
                    event['infectedFootprints'] = sitefootprint
                    print(f"event['infectedFootprints']:{event['infectedFootprints']}")
                    self.__firestore.setEvent(event)
                    del event['infectedFootprints']

                    memberfootprints = self.__firestore.getFootprints(sitefootprint)

                    try:
                        event["infectedTime"] = memberfootprints[0]['timestamp']
                        event["siteId"] = memberfootprints[0]['siteId']
                    except IndexError:
                        pass

                    if event['strength'] > 0:
                        event['strength'] -= 1

                        self.check(event)

                    count -= 1