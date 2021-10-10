class Config():
    def __init__(self) :
        self.channelAccessToken = "[Your Channel AccessToken]"
        self.__firebase_keyFile = "[Path/to/your/firebaseKey.json]"
        self.__pubSub_keyFile = '[Path/to/your/pubsubKey.json]'
        
    def firebase(self):
        data = {
            'keyFile' : self.__firebase_keyFile,
            'storageBucket' : '[Your_Project_ID].appspot.com',
            'projectName'   : '[Your_Project_Name]',
            'dbName'        : '[Your_DB_Name]',
            'memberTable'   : 'members',
            'siteTable'     : 'sites',
        }
        return data

    def edgePub(self):
        data = {
            'keyFile'   : self.__pubSub_keyFile,
            'projectId' : '[Your Project ID]',
            'topicId'   : 'pubsub'
        }
        return data
