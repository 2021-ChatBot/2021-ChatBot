import os

#（1）Line Channel
channelSecret = os.environ ['channelSecret']
channelAccessToken = os.environ ['channelAccessToken']
signUpUrl = "[your sign up url]"
bindingUrl = "[your binding url]"

#（2）Dialogflow 
projectId = "[your project id]"
languageCode = "zh-TW"

#（3）Cloud SQL
usersTableName = "user"
dbName = "[your database name]"
dbUser = "[your user name]"
dbPassword = "[your database passward]"
connectionName = "[your database connection name]"
