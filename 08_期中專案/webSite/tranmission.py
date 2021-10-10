import pandas as pd
import uuid
from firebaseApi import Firebase
from edgePub import edgePub

"""
被誰呼叫:epidemicNotificationResponse 
輸入:memberId, spreadStrength, confirmedTime, companyId 
輸出: getResult
"""
class TransmissionTracker:
    def __init__(self, inputData):
        self.__memberId = inputData["memberId"]
        self.__confirmedTime = inputData["confirmedTime"]
        self.__spreadStrength = inputData["spreadStrength"]
        self.__firebaseApi = Firebase()
        self.eventId = str(uuid.uuid4())
        self.infectedList = []

        # run algorithm
        self.infect_Algo(self.__memberId, self.__confirmedTime, self.__spreadStrength)

        # clean duplicate infected data
        self.infectedList = sorted(pd.DataFrame(self.infectedList).drop_duplicates().to_dict('records'),
                                   key=lambda k: k['timestamp'])
        print(f"infectedList:{self.infectedList}")
        # 將結果寫入Big Query
        if len(self.infectedList)!=0:
            self.insertBigQueryResult()


    def infect_Algo(self, memberId, timestamp, spreadStrength):
        infectedMember = {}
        infected_footprint = ""
        siteId = ""
        memberIndex = 0
        siteIndex = 0
        # ----------------------------調出成員足跡列表----------------------------
        Memberfootprints = self.__firebaseApi.getfootprintsOfMemberByMemberId(memberId)
        print(Memberfootprints)
        Memberfootprints = sorted(Memberfootprints, key=lambda k: k['timestamp'])
        
        MemberInfo = self.__firebaseApi.getMemberDataById(memberId)
        for i in range(len(Memberfootprints)):
            memberIndex = i
            if Memberfootprints[i]["timestamp"] >= timestamp:
                print(MemberInfo)
                infected_footprint = Memberfootprints[i]["id"]
                siteId = Memberfootprints[i]["siteId"]
                infectedMember["memberId"] = memberId
                infectedMember["timestamp"] = timestamp
                infectedMember["siteId"] = Memberfootprints[i]["siteId"]
                infectedMember["name"] = MemberInfo["name"]
                infectedMember["lineId"] = MemberInfo["lineId"]
                
                break

        # ----------------------------調出商店足跡列表----------------------------
        try:
            site_visitList = self.__firebaseApi.getfootprintsOfSiteBySiteId(siteId)
        except Exception:
            site_visitList=[]
        # response = Firebase().getFootprintsBySiteId({"siteId":siteId})
        site_visitList = sorted(site_visitList, key=lambda k: k['timestamp'])

        for i in range(len(site_visitList)):
            if site_visitList[i]['id'] == infected_footprint:
                siteIndex = i
                break
        if len(infectedMember)!=0:
            self.infectedList.append(infectedMember)

        if spreadStrength == 0:
            try:# 往下追蹤成員足跡到底為止
                return self.infect_Algo(memberId=Memberfootprints[memberIndex + 1]['memberId'],
                                        timestamp=Memberfootprints[memberIndex + 1]["timestamp"],
                                        spreadStrength=self.__spreadStrength)
            except IndexError:
                return None
        else:
            try:# 先追蹤商店足跡, 再繼續往下追蹤成員足跡
                return self.infect_Algo(memberId=site_visitList[siteIndex + 1]['lineId'],
                                        timestamp=site_visitList[siteIndex + 1]["timestamp"],
                                        spreadStrength=spreadStrength - 1), \
                       self.infect_Algo(memberId=Memberfootprints[memberIndex + 1]['memberId'],
                                        timestamp=Memberfootprints[memberIndex + 1]["timestamp"],
                                        spreadStrength=self.__spreadStrength - 1)
            except IndexError:
                return None

    def insertBigQueryResult(self):
        data = {
            "event":{
                "eventId": self.eventId,
                "infectedMember": self.__memberId,
                "amount": len(set(pd.DataFrame(self.infectedList)["memberId"].drop_duplicates())) - 1,  # 自己不算
                "strength": self.__spreadStrength,
                "infectedTime": self.__confirmedTime,
            }
        }
        response = edgePub(data)
        print(response)

    def getResult(self) -> list:
        return self.infectedList



