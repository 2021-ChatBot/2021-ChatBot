import requests
members = {
    "[Bruce's memberId]" : {'name':"Bruce", 'email':'bruce@gmail.com', 'role':'manager'},
    "[Allen's memberId]" : {'name':"Allen", 'email':'allen@gmail.com', 'role':'customer'},
    "[Cherry's memberId]" : {'name':"Cherry",'email':'cherry@gmail.com', 'role':'manager'}
    }
domain = "[url]/myData/"

for memberId, memberData in members.items():
    response = requests.post(url = domain + memberId, data = memberData)
