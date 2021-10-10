from config import * 
import firebase_admin
from firebase_admin import credentials
config = Config()
cred = credentials.Certificate(config.firebase()['keyFile'])
app=firebase_admin.initialize_app(cred, {'storageBucket': config.firebase()['storageBucket']})
