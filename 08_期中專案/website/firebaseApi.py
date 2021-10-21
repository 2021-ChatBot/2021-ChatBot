from firebase_admin import credentials, firestore, initialize_app
from config import Config

config = Config()
cred = credentials.Certificate(config.firebase()['keyFile'])
initialize_app(cred, {'storageBucket': config.firebase()['storageBucket']})


class Firebase:
    
    def __init__(self, companyId=config.companyId):
        self.__companyId = companyId
        self.__firestore = firestore.client()
        self.__myDb = self.__firestore.collection(config.firebase()['projectName']).document(
            config.firebase()['dbName'])
        self.__sitesCollection = self.__myDb.collection("companies").document(self.__companyId).collection(
            config.firebase()['siteTable'])
        self.__membersCollection = self.__myDb.collection(config.firebase()['memberTable'])


    # --------members--------------
    def getMemberData(self, memberId=None, companyId=None):
        if memberId == None and companyId == None:
            # get all member data from members
            membersData = list(doc._data for doc in self.__membersCollection.stream())
            return membersData  # list
        elif companyId != None:
            membersData = []
            try:
                for member in self.__myDb.collection("companies").document(companyId).collection(
                        config.firebase()['memberTable']).stream():
                    memberData = self.__membersCollection.document(member.id).get().to_dict()
                    membersData.append(memberData)
            except:
                pass
            return membersData  # list
        else:
            # get single member data from members
            memberData = self.__membersCollection.document(memberId).get().to_dict()
            return memberData  # dict


    def putMemberData(self, memberData):
        memberId = memberData['id']
        self.__membersCollection.document(memberId).update(memberData)


    # --------sites----------------
    def getSiteData(self, siteId=None, companyId=None):
        if siteId == None:
            sitesData = list(doc._data for doc in self.__myDb.collection("companies").document(companyId).collection(config.firebase()['siteTable']).stream())
            return sitesData  # list
        else:
            siteData = self.__myDb.collection("companies").document(companyId).collection(config.firebase()['siteTable']).document(siteId).get().to_dict()
            return siteData  # dict


    # --------footprints-----------
    def getFootprintsData(self, memberId=None, siteId=None, companyId=None):
        footprintsData = []
        if memberId != None:
            footprintsData = list(
                doc._data for doc in self.__membersCollection.document(memberId).collection('footprints').stream())
        elif siteId != None and companyId is not None:
            footprintsData = list(
                doc._data for doc in self.__myDb.collection("companies").document(companyId).collection(config.firebase()['siteTable']).document(siteId).collection('footprints').stream())
        return footprintsData  # list


    def postFootprint(self, footPrintModel):
        memberId = footPrintModel['memberId']
        siteId = footPrintModel['siteId']
        footprintId = self.__sitesCollection.document(siteId).collection('footprints').add(footPrintModel)[1].id
        self.__sitesCollection.document(siteId).collection('footprints').document(footprintId).update({'id': footprintId})
        footPrintModel['id'] = footprintId
        self.__membersCollection.document(memberId).collection('footprints').document(footprintId).set(footPrintModel)
        return footprintId


    # --------companies------------
    def getCompaniesData(self, companyId=None):
        companyDataList = []
        if companyId is None:
            for company in self.__myDb.collection("companies").stream():
                siteIdOfName = {}
                for site in self.__myDb.collection("companies").document(company.id).collection(config.firebase()['siteTable']).stream():
                    siteIdOfName[site.id] = site._data['name']
                companyDataList.append({"id": company.id, "name": company._data['name'], "sites": siteIdOfName})
            return companyDataList
        elif type(companyId) is str:
            company = self.__myDb.collection("companies").document(companyId)

            siteIdOfName = {}
            for site in company.collection(config.firebase()['siteTable']).stream():
                siteIdOfName[site.id] = site._data['name']
            return {"id": companyId, "name": company.get().to_dict()['name'], "sites": siteIdOfName}
        else:
            # empty dictionary
            return companyDataList
            # companyDataList -> [{"id" : "companyId" , "name" : "companyName", "sites" : {"siteId" : "siteName"}}]
        
    


    
