from firebase_admin import credentials, firestore, initialize_app
from config import Config

config = Config()


cred = credentials.Certificate(config.firebase()['keyFile'])
initialize_app(cred, {'storageBucket': config.firebase()['storageBucket']})

class Firebase:
    def __init__(self, companyId = config.companyId):
        self.__companyId = companyId
        self.__firestore = firestore.client()
        self.__myDb = self.__firestore.collection(config.firebase()['projectName']).document(config.firebase()['dbName'])
        self.__sitesCollection = self.__myDb.collection("companies").document(self.__companyId).collection(config.firebase()['siteTable'])
        self.__membersCollection = self.__myDb.collection(config.firebase()['memberTable'])

    # --------members--------------
    def getMemberData(self, memberId = None):
        if memberId == None :
            membersData = list(doc._data for doc in self.__membersCollection.stream())
            return membersData #list
        else :
            memberData = self.__membersCollection.document(memberId).get().to_dict()
            return memberData #dict
    def getMembersDataOfCompany(self):
        membersData = []
        try:
            for member in self.__myDb.collection("companies").document(self.__companyId).collection(config.firebase()['memberTable']).stream():
                memberData = self.__membersCollection.document(member.id).get().to_dict()
                membersData.append(memberData)
        except:
            pass
        return membersData #list
    def putMemberData(self, memberData):
        memberId = memberData['id']
        self.__membersCollection.document(memberId).update(memberData)

    # --------sites----------------
    def getSiteData(self,siteId = None):
        if siteId == None:
            sitesData = list(doc._data for doc in self.__sitesCollection.stream())
            return sitesData #list
        else:
            siteData = self.__sitesCollection.document(siteId).get().to_dict()
            return siteData #dict
    # --------footprints-----------
    def getFootprintsData(self, memberId=None, siteId=None):
        if memberId != None :
            footprintsData = list(doc._data for doc in self.__membersCollection.document(memberId).collection('footprints').stream())
        elif siteId != None : 
            footprintsData = list(doc._data for doc in self.__sitesCollection.document(siteId).collection('footprints').stream())
        return footprintsData #list

    def postFootprint(self, footPrintModel):
        memberId = footPrintModel['memberId']
        siteId = footPrintModel['siteId']
        response = self.__sitesCollection.document(siteId).collection('footprints').add(footPrintModel)[1]
        self.__sitesCollection.document(siteId).collection('footprints').document(response.id).update({'id': response.id})
        self.__membersCollection.document(memberId).collection('footprints').document(response.id).set(footPrintModel)
        self.__membersCollection.document(memberId).collection('footprints').document(response.id).update({'id': response.id})
        return response.id
    # --------companies------------ 

    def getCompaniesData(self):
        companyIdOfName = {}
        siteIdOfName = {}
        for company in self.__myDb.collection("companies").stream():
            companyIdOfName[company.id] = company._data['name']
            for site in self.__myDb.collection("companies").document(company.id).collection(config.firebase()['siteTable']).stream():
                siteIdOfName[site.id] = site._data['name']
        return companyIdOfName, siteIdOfName #dict, dict
        
    


    
