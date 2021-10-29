from firestoreDAO import Firestore

class CheckFootprints:
    def __init__(self, event):
        self.__firestore = Firestore()
        event['infectedFootprints'] = []
        footprints = self.__firestore.getFootprints(event)
        if len(footprints) is not 0:
            self.check(footprints[0], event['strength'], event['infectedFootprints'])
        self.__firestore.setEvent(event)


    def check(self, footprint, strength, infectedFootprints):
        if strength > 0 and len(footprint) != 0:
            infectedFootprints.append(footprint)
            # 尋找該商店下一筆足跡
            self.check(self.__firestore.getsiteFootprint(footprint), strength - 1, infectedFootprints)
            # 尋找該成員下一筆足跡
            self.check(self.__firestore.getmemberFootprint(footprint), strength, infectedFootprints)
