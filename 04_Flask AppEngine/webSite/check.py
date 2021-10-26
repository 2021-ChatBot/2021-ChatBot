from firestoreDAO import Firestore

class CheckFootprints:
    def __init__(self, event):
        self.__firestore = Firestore()
        self.infectedFootprints = []
        footprint = self.__firestore.getFootprints(event)
        if len(footprint) is not 0:
            self.check(footprint[0], event['strength'])
        event['infectedFootprints'] = self.infectedFootprints
        self.__firestore.setEvent(event)


    def check(self, footprint, mystrength):
        if mystrength < 1 or len(footprint) == 0:
            return
        self.infectedFootprints.append(footprint)
        self.check(self.__firestore.getsiteFootprint(footprint), mystrength-1)
        self.check(self.__firestore.getmemberFootprint(footprint), mystrength)
