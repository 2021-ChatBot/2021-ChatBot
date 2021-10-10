class FootPrintModel:
    def __init__(self, lineId="1", memberId="1", storeId="1", timestamp=None):
        self.lineId = lineId
        self.memberId = memberId
        self.storeId = storeId
        self.timestamp = timestamp


# -------------------------------------------------------------------------------------
class FootPrintResponse:
    def __init__(self, footPrintModel=None, code=None):
        self.footPrintModel = footPrintModel
        self.result = {
            "code": code,
            "title": None,
            "description": None,
        }
