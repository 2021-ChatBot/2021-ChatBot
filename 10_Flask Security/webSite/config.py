from secretManager import access_secret_version

# ( 0 ) Firestore
companyId = "[your company id]"
version = '1' # 若secret沒有更新的情況下，version為1
# ( 1 ) APIgateway
apiKey = access_secret_version("[your API gateway Key resource id]", version)
apiUrl = access_secret_version("[your API gateway url resource id]", version)

# ( 2 ) Line Channel
liffIdForSignUp = access_secret_version("[your liffId for signUp resource id]", version)
liffIdForBinding = access_secret_version("[your liffId for binding resource id]", version)
channelAccessToken = access_secret_version("[your channelAccessToken resource id]", version)

# ( 3 ) Data Studio report URL
report = "[your data studio embedded url]"

# ( 4 ) Flask 
flaskConfig={
    'DEBUG' : False,
    'SECRET_KEY' : access_secret_version("[your SECRET_KEY resource id", version),
    'SECURITY_PASSWORD_HASH' : "argon2",
    'SECURITY_PASSWORD_SALT' : access_secret_version("[your SECURITY_PASSWORD_SALT resource id]", version),
    'SQLALCHEMY_TRACK_MODIFICATIONS' : True,
    'SQLALCHEMY_ENGINE_OPTIONS' : {"pool_pre_ping": True}
}

# ( 4 ) Cloud SQL
CONNECT_NAME = access_secret_version("[your CONNECT_NAME resource id]", version)
DBNAME = access_secret_version("[your DBNAME resource id]", version)
USER_NAME = "user"
PASSWORD = access_secret_version("[your PASSWORD resource id]", version)

# ( 4 ) Pub / Sub
pubsub_projectId = "[your pubsub_project Id]"
topicId = "[your topic Id]"
pub_key = "[your pudsub_key path]"