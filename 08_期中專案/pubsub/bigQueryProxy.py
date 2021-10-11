import bigQueryConfig
from google.oauth2 import service_account
from google.cloud import bigquery
import datetime ,time
import pandas as pd

class BigQueryProxy:
    def __init__(self):
        self.__credentials = service_account.Credentials.from_service_account_file(bigQueryConfig.keyFile) #放bigQuery的key(json檔)
        self.__projectId = bigQueryConfig.projectId #放bigQuery的projectId
        self.__client = bigquery.Client(project = self.__projectId, credentials = self.__credentials) #使用BigQueryAPI，透過金鑰進行身分驗證所需之設定
        self.__datasetId = bigQueryConfig.datasetId
        self.__datasetRef = self.__client.dataset(self.__datasetId) #將datasetId轉成dataset_ref
    #參考:https://cloud.google.com/bigquery/docs/authentication/service-account-file
    
    def __insertRowToBigdata(self,tableId,model): #create
        table_ref = self.__datasetRef.table(tableId) #取得table_ref
        df = pd.DataFrame(model) #將dict轉成dataframe
        job = self.__client.load_table_from_dataframe(df, table_ref) #將dataframe資料存入table
        job.result() # Wait for the job to complete
    #參考:https://cloud.google.com/bigquery/docs/samples/bigquery-load-table-dataframe
    #參考:https://codelabs.developers.google.com/codelabs/cloud-bigquery-python#9

    #根據datamodel的資料及欄位(table)製作dict
    def insertFootprintData(self, footprintModel): 
        tableId = bigQueryConfig.footprintTableId
        footprintData = [{
            'id': footprintModel['id'],
            'member': footprintModel['member'],
            'site': footprintModel['site'],
            'timestamp': datetime.datetime.utcfromtimestamp(footprintModel['timestamp'])
        }]
        self.__insertRowToBigdata(tableId, footprintData)
    def insertMemberData(self, memberModel): 
        tableId = bigQueryConfig.memberTableId
        memberData = [{
            'id': memberModel['id'],
            'name': memberModel['name']
        }]
        self.__insertRowToBigdata(tableId, memberData)
    def insertInfectedData(self, infectedModel):
        tableId = bigQueryConfig.infectedTableId
        infectedData = [{
            'eventId': infectedModel['eventId'],
            'infectedMember': infectedModel['member'],
            'infectedSites': infectedModel['infectedSites'],
            'infectedTime': datetime.datetime.utcfromtimestamp(infectedModel['timestamp']),
            'strength': infectedModel['strength'],
            'amount': infectedModel['amount']
        }]
        self.__insertRowToBigdata(tableId, infectedData)
