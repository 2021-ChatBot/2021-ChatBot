from google.cloud import pubsub_v1
from google.oauth2 import service_account
from config import pubsubKey,projectId,edgePubTopicId
import json

credentials=service_account.Credentials.from_service_account_file(pubsubKey)
publisher = pubsub_v1.PublisherClient(credentials=credentials)


def edgePub(dataModel):
    publisher.publish(publisher.topic_path(projectId, edgePubTopicId)
                        , data = bytes(json.dumps(dataModel), encoding = "utf8")
                    )


