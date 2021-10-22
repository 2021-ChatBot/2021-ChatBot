import pandas as pd
import uuid
from firebaseApi import Firebase


class TransmissionTracker:
    def __init__(self, inputData):
        self.__companyId = inputData["companyId"]
        self.__siteId = inputData["siteId"]
        self.__confirmedTime = inputData["confirmedTime"]
        self.__spreadStrength = inputData["spreadStrength"]
        self.__firebaseApi = Firebase()
        self.eventId = str(uuid.uuid4())
        self.infectedList = []
        memberId = ""

        site_visitList = self.__firebaseApi.getFootprintsData(siteId=self.__siteId, companyId=self.__companyId)

        site_visitList = sorted(site_visitList, key=lambda k: k['timestamp'])

        for i in range(len(site_visitList)):
            if site_visitList[i]['timestamp'] >= self.__confirmedTime:
                memberId = site_visitList[i]['memberId']
                break

        if memberId != "":
            # run algorithm
            self.checkFootprints(memberId, self.__confirmedTime, self.__spreadStrength, self.__companyId)

            # clean duplicate infected data
            self.infectedList = sorted(pd.DataFrame(self.infectedList).drop_duplicates().to_dict('records'),
                                       key=lambda k: k['timestamp'])

    def checkFootprints(self, memberId, timestamp, spreadStrength, companyId):
        infectedMember = {}
        infected_footprint = ""
        siteId = ""
        memberIndex = 0
        siteIndex = 0
        # ----------------------------調出成員足跡列表----------------------------
        Memberfootprints = self.__firebaseApi.getFootprintsData(memberId=memberId)
        Memberfootprints = sorted(Memberfootprints, key=lambda k: k['timestamp'])

        MemberInfo = self.__firebaseApi.getMemberData(memberId=memberId)

        for i in range(len(Memberfootprints)):
            memberIndex = i
            if Memberfootprints[i]["timestamp"] >= timestamp:
                infected_footprint = Memberfootprints[i]["id"]
                siteId = Memberfootprints[i]["siteId"]
                infectedMember["memberId"] = memberId
                infectedMember["timestamp"] = timestamp
                infectedMember["siteId"] = Memberfootprints[i]["siteId"]
                infectedMember["companyId"] = Memberfootprints[i]["companyId"]
                infectedMember["name"] = MemberInfo["name"]
                break

        # ----------------------------調出商店足跡列表----------------------------
        try:
            site_visitList = self.__firebaseApi.getFootprintsData(siteId=siteId, companyId=companyId)
        except Exception:
            site_visitList = []
        site_visitList = sorted(site_visitList, key=lambda k: k['timestamp'])

        for i in range(len(site_visitList)):
            if site_visitList[i]['id'] == infected_footprint:
                siteIndex = i
                break
        if len(infectedMember) != 0:
            self.infectedList.append(infectedMember)

        if spreadStrength == 0:
            try:  # 往下追蹤成員足跡到底為止
                return self.checkFootprints(memberId=Memberfootprints[memberIndex + 1]['memberId'],
                                            timestamp=Memberfootprints[memberIndex + 1]["timestamp"],
                                            spreadStrength=self.__spreadStrength,
                                            companyId=Memberfootprints[memberIndex + 1]['companyId'])
            except IndexError:
                return None
        else:
            try:  # 先追蹤商店足跡, 再繼續往下追蹤成員足跡
                return self.checkFootprints(memberId=site_visitList[siteIndex + 1]['memberId'],
                                            timestamp=site_visitList[siteIndex + 1]["timestamp"],
                                            spreadStrength=spreadStrength - 1,
                                            companyId=Memberfootprints[memberIndex + 1]['companyId']), \
                       self.checkFootprints(memberId=Memberfootprints[memberIndex + 1]['memberId'],
                                            timestamp=Memberfootprints[memberIndex + 1]["timestamp"],
                                            spreadStrength=self.__spreadStrength - 1,
                                            companyId=Memberfootprints[memberIndex + 1]['companyId'])
            except IndexError:
                return None

    def insertBigQueryResult(self):
        return {
            "event": {
                "eventId": self.eventId,
                "infectedSites": len(set(pd.DataFrame(self.infectedList)["siteId"].drop_duplicates())),
                "amount": len(set(pd.DataFrame(self.infectedList)["memberId"].drop_duplicates())),
                "strength": self.__spreadStrength,
                "timestamp": self.__confirmedTime,
                "companyName": self.__companyId,
                "infectedSiteName": self.__firebaseApi.getSiteData(siteId=self.__siteId, companyId=self.__companyId)["name"],
                "infectedfootprints": len(self.infectedList)
            }
        }

    def getResult(self) -> list:
        # infectedList = [
        #   {
        #       "companyId" : "string",
        #       "siteId" : "string",
        #       "memberId" : "string",
        #       "name" : "string",
        #       "timestamp" : "int,
        #   }
        # ]
        return sorted(self.infectedList, key=lambda k: (k['name'], k['timestamp']))
