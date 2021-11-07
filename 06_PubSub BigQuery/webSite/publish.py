from google.cloud import pubsub_v1
import json
from config import topicId, projectId

publisher = pubsub_v1.PublisherClient()

def publish_messages(messages):
    publisher.publish(publisher.topic_path(projectId, topicId)
                      , data=bytes(json.dumps(messages), encoding="utf8")
                      )
