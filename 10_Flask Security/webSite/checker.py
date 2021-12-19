from config import companyId
from apiClient import requestAPI

def check(infected):
    if infected['myStrength'] > 0:
        if infected['siteId'] != 0:
            footprints = requestAPI("GET", f"/infected/{companyId}/{infected['siteId']}/{infected['memberId']}/{infected['infectedTime']}/{infected['myStrength']}")
        elif infected['memberId'] != 0:
            footprints = requestAPI("GET", f"/infected/{companyId}/{infected['siteId']}/{infected['memberId']}/{infected['infectedTime']}/{infected['myStrength']}")
        for footprint in footprints:
            infected['infectedTime'] = footprint['timestamp']
            infected['myStrength'] -= 1
            if infected['siteId'] != 0:
                infected['memberId'] = footprint['memberId']
                infected['siteId'] = 0
            elif infected['memberId'] != 0:
                infected['siteId'] = footprint['siteId']
                infected['memberId'] = 0

            check(infected)
            if footprint not in infected['infectedFootprints']:
                infected['infectedFootprints'].append(footprint)

            infected['myStrength'] = infected['strength'] - 1
            if infected['myStrength'] == 0:
                infected['strength'] -= 1