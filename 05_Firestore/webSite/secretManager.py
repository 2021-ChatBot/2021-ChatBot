from google.cloud import secretmanager

def access_secret_version(resourceId, version):

    client = secretmanager.SecretManagerServiceClient()
    name = f"{resourceId}/versions/{version}"
    response = client.access_secret_version(request={"name": name})

    payload = response.payload.data.decode("UTF-8")
    return payload