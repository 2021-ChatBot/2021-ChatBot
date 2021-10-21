import bigQueryConfig
from google.oauth2 import service_account
from google.cloud import bigquery
from datetime import datetime
import pandas as pd

class BigQueryProxy:
    def __init__(self):
        self.__credentials = service_account.Credentials.from_service_account_file(bigQueryConfig.keyFile)
        self.__projectId = bigQueryConfig.projectId
        self.__client = bigquery.Client(project = self.__projectId, credentials = self.__credentials)
        self.__datasetId = bigQueryConfig.datasetId
        self.__datasetRef = self.__client.dataset(self.__datasetId)
    
    def __insertRowToBigdata(self,tableId,model):
        table_ref = self.__datasetRef.table(tableId)
        df = pd.DataFrame(model)
        job = self.__client.load_table_from_dataframe(df, table_ref)
        job.result()

    def insertFootprintData(self, footprintModel): 
        tableId = bigQueryConfig.footprintTableId
        footprintData = [{
            'id': footprintModel['id'],
            'member': footprintModel['member'],
            'site': footprintModel['site'],
            'timestamp': datetime.utcfromtimestamp(footprintModel['timestamp'])
        }]
        self.__insertRowToBigdata(tableId, footprintData)
    
    def insertMemberData(self, memberModel): 
        tableId = bigQueryConfig.memberTableId
        memberData = [{
            'id': memberModel['id'],
            'name': memberModel['name'],
        }]
        self.__insertRowToBigdata(tableId, memberData)

    def insertInfectedData(self, infectedModel):
        tableId = bigQueryConfig.infectedTableId
        infectedData = [{
            'eventId': infectedModel['eventId'],
            'companyName': infectedModel['companyName'],
            'infectedSiteName': infectedModel['infectedSiteName'],
            'infectedSites': infectedModel['infectedSites'],
            'infectedTime': datetime.utcfromtimestamp(infectedModel['timestamp']),
            'strength': infectedModel['strength'],
            'amount': infectedModel['amount'],
            'infectedfootprints': infectedModel['infectedfootprints']
        }]
        self.__insertRowToBigdata(tableId, infectedData)
    

    def updateMember(self, memberModel):
        update = 'UPDATE `{}` '.format(bigQueryConfig.projectId + "." + bigQueryConfig.datasetId + "." + bigQueryConfig.memberTableId)
        updateValue = 'SET {} = "{}" '.format("role",memberModel["role"])
        updateCondition = 'WHERE id = "{}"'.format(memberModel["id"])
        self.__client.query(update + updateValue + updateCondition)
        return {"code":"200","message":"success"}
