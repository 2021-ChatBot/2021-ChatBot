from google.cloud import pubsub_v1
import json
from config import topicId, projectId, pub_key
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(pub_key)
publisher = pubsub_v1.PublisherClient(credentials=credentials)

def publish_messages(messages):
    publisher.publish(publisher.topic_path(projectId, topicId)
                      , data=bytes(json.dumps(messages), encoding="utf8")
                      )
