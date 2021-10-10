from firebase_admin import credentials, firestore, initialize_app
from config import Config

config = Config()


cred = credentials.Certificate(config.firebase()['keyFile'])
initialize_app(cred, {'storageBucket': config.firebase()['storageBucket']})

class Firebase:
    def __init__(self):

        self.__firestore = firestore.client()
        self.__myDb = self.__firestore.collection(config.firebase()['projectName']).document(config.firebase()['dbName'])
        self.__sitesCollection = self.__myDb.collection(config.firebase()['siteTable'])
        self.__membersCollection = self.__myDb.collection(config.firebase()['memberTable'])

    def createMember(self, memberModel):
        memberId = memberModel['lineId']
        member = self.__membersCollection.document(memberId).get().to_dict()
        if member == None:
            self.__membersCollection.document(memberId).set(memberModel)
            self.__membersCollection.document(memberId).update({'id': memberId})
        return memberId

    def updateMember(self, memberModel):
        memberId = memberModel['lineId']
        self.__membersCollection.document(memberId).update(memberModel)
        return memberId
        
    def listfootprintsIdOfMember(self, memberId):
        footPrintIdsOfmember = list(doc.id for doc in self.__membersCollection.document(memberId).collection('footprints').stream())
        return footPrintIdsOfmember

    def getMemberDataById(self, memberId):
        memberData = self.__membersCollection.document(memberId).get().to_dict()
        return memberData

    def getAllMemberData(self):
        memberList =self.__membersCollection.stream()
        memberDataList = []
        for doc in memberList:
            memberDataList.append(doc.to_dict())
            # print(f'{doc.id} => {doc.to_dict()}')
        return memberDataList

    def createFootPrint(self, footPrintModel):
        memberId = footPrintModel['memberId']
        siteId = footPrintModel['siteId']
        response = self.__sitesCollection.document(siteId).collection('footprints').add(footPrintModel)[1]
        self.__sitesCollection.document(siteId).collection('footprints').document(response.id).update({'id': response.id})
        self.__membersCollection.document(memberId).collection('footprints').document(response.id).set(footPrintModel)
        self.__membersCollection.document(memberId).collection('footprints').document(response.id).update({'id': response.id})
        return response.id

    def getfootprintsOfMemberByMemberId(self,memberId):
        footprintList = []
        allFootprint = self.__membersCollection.document(memberId).collection('footprints').get()
        for footprint in allFootprint:
            footprintList.append(footprint.to_dict())
        return footprintList

    def getfootprintsOfSiteBySiteId(self,siteId):
        print(siteId)
        footprintList = []
        allFootprint = self.__sitesCollection.document(siteId).collection('footprints').get()
        for footprint in allFootprint:
            footprintList.append(footprint.to_dict())
        return footprintList
        
    def getAllSites(self):
        sitesList = []
        sites = self.__sitesCollection.get()
        for site in sites:
            sitesList.append(site.to_dict())
        return sitesList

    def getSiteDataById(self,siteId):
        siteData = self.__sitesCollection.document(siteId).get().to_dict()
        return siteData
