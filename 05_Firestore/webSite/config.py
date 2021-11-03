import secretManager

# ( 0 ) Line Channel
secretResourceId = '[your secret resource id]'
versionId = '1'
channelAccessToken = secretManager.access_secret_version(secretResourceId, versionId)

# ( 1 ) Firestore
companyId = '[your company id]' 
