class Config():
    def __init__(self) :
        self.channelAccessToken = '[your channelAccessToken]'
        self.__firestore_keyFile = '[your firestoreKey.json]'
        self.companyId = '[your companyId]' 
        
    def firebase(self):
        data = {
            'keyFile' : self.__firestore_keyFile,
            'storageBucket' : '[your projectID.appspot.com]',
        }
        return data
