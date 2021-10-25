class Config():
    def __init__(self) :
        self.channelAccessToken = '[your channelAccessToken]'
        self.__firebase_keyFile = '[your firebaseKey.json]'
        self.companyId = '[your companyId]' 
        
    def firebase(self):
        data = {
            'keyFile' : self.__firebase_keyFile,
            'storageBucket' : '[your projectID.appspot.com]',
            'memberTable'   : 'members',
            'siteTable'     : 'sites',
            'eventTable'    : 'events'
        }
        return data
