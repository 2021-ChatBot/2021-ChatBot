from google.cloud import pubsub_v1
from google.oauth2 import service_account
from config import Config
import json

edgePubConfig = Config().edgePub()

credentials=service_account.Credentials.from_service_account_file(edgePubConfig["keyFile"])
publisher = pubsub_v1.PublisherClient(credentials=credentials)
projectId = edgePubConfig["projectId"]



def edgePub(dataModel):
    publisher.publish(publisher.topic_path(projectId, edgePubConfig["topicId"])
                        , data = bytes(json.dumps(dataModel), encoding = "utf8")
                    )


