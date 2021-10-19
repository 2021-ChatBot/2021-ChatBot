class Config():
    def __init__(self) :
        self.channelAccessToken = '[your channelAccessToken]'
        self.__firebase_keyFile = '[your firebaseKey.json]'
        self.__pubSub_keyFile = '[your pubsubKey.json]'
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

    def edgePub(self):
        data = {
            'keyFile'   : self.__pubSub_keyFile,
            'projectId' : '[your projectId]',
            'topicId'   : 'pubsub'
        }
        return data
