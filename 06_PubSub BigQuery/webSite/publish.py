from google.cloud import pubsub_v1
import json
from config import topicId, projectId

publisher = pubsub_v1.PublisherClient()


def edgePub(dataModel):
    publisher.publish(publisher.topic_path(projectId, topicId)
                      , data=bytes(json.dumps(dataModel),encoding = "utf8")
                      )