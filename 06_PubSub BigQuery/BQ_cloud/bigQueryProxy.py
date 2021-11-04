from bigQueryConfig import *
from google.cloud import bigquery
import pandas as pd
from datetime import datetime


class BigQueryProxy:
    def __init__(self):
        self.__client = bigquery.Client(project=projectId)
        self.__datasetRef = bigquery.DatasetReference(projectId, datasetId) # 將datasetId轉成__datasetRef

    def insertInfected(self, event):
        tableName = projectId + '.' + datasetId + "." + infectedTableName
        infectedFootprints = []
        for footprint in event['infectedFootprints']:
            struct = 'STRUCT("{}","{}","{}","{}",CAST("{}" AS TIMESTAMP))'.format(footprint['id'], footprint['companyId'], footprint['siteId'], footprint['memberId'], datetime.utcfromtimestamp(footprint['timestamp']))
            infectedFootprints.append(struct)

        query = f"INSERT INTO `{tableName}` (eventId,infectedSiteId,strength,infectedTimestamp,infectedFootprints) "+\
                'VALUES ("{}","{}", CAST("{}"AS INT),"{}",{})'.format(event["eventId"], event["siteId"], event["strength"], datetime.utcfromtimestamp(event["infectedTime"]), str(infectedFootprints).replace("'", ""))

        job = self.__client.query(query)
        job.result()  # Wait for the job to complete

    def insertFootprint(self, model):
        table_ref = self.__datasetRef.table(footprintTableName)  # 取得table_ref
        df = pd.DataFrame([model])  # 將dict轉成dataframe
        job = self.__client.load_table_from_dataframe(df, table_ref)  # 將dataframe資料存入table
        job.result()  # Wait for the job to complete