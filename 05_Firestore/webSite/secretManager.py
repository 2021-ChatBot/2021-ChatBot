def access_secret_version(resourceId, versionId):
    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
    name = f"{resourceId}/versions/{versionId}"
    response = client.access_secret_version(request={"name": name})
    payload = response.payload.data.decode("UTF-8")
    return payload