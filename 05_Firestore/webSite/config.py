class Config():
    def __init__(self) :
        self.channelAccessToken = '[your channelAccessToken]'
        self.__firebase_keyFile = '[your firebaseKey.json]'
        self.companyId = '[your companyId]' 
        
    def firebase(self):
        data = {
            'keyFile' : self.__firebase_keyFile,
            'storageBucket' : '[your projectID.appspot.com]',
            'projectName'   : '[your project name]',
            'dbName'        : '[your firestore dbName]',
            'memberTable'   : 'members',
            'siteTable'     : 'sites',
        }
        return data

