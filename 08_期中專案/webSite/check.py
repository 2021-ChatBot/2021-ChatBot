from firestoreDAO import Firestore


class CheckFootprints:
    def __init__(self, event):
        self.__firestore = Firestore()
        self.infectedFootprints = []
        footprint = self.__firestore.getFootprints(event)[0]
        footprint['strength'] = event['strength']
        self.check(footprint)
        event['infectedFootprints'] = self.infectedFootprints
        self.__firestore.setEvent(event)

    def check(self, data):
        if data['strength'] == 1:
            for memberfootprint in self.__firestore.getmemberFootprints(data):
                if memberfootprint['timestamp'] >= data['timestamp']:
                    memberfootprint.pop('strength', None)
                    self.infectedFootprints.append(memberfootprint)
        else:
            mystrength = data['strength']
            for footprint in self.__firestore.getsiteFootprints(data):
                if mystrength >= 1 :
                    footprint.pop('strength', None)
                    self.infectedFootprints.append(footprint)
                    footprint['strength'] = data['strength'] - 1
                    self.check(footprint)
                    mystrength -= 1
