import sqlalchemy
from config import dbName, dbUser, dbPassword, connectionName, usersTableName

driverName = 'mysql+pymysql'
queryString = dict({"unix_socket": "/cloudsql/{}".format(connectionName)})
db = sqlalchemy.create_engine(
    sqlalchemy.engine.url.URL(
    drivername=driverName,
    username=dbUser,
    password=dbPassword,
    database=dbName,
    query=queryString,
    ),
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,
    pool_recycle=1800
)

def updateLineId(lineId, email):
    stmt = sqlalchemy.text(
        "UPDATE {} SET lineId='{}' WHERE email='{}';".format(usersTableName, lineId, email)
    )
    try:
        db.connect().execute(stmt)
    except Exception as e:
        return 'Error: {}'.format(str(e))
    return 'ok'


def query(lineId , email):
    members = db.connect().execute(
        "SELECT name, email, lineId FROM user;"
    ).fetchall()

    if lineId and email:
        for member in members:
            if member['lineId'] == lineId and member['email'] == email:
                return member
    if lineId:
        for member in members:
            if member['lineId'] == lineId:
                return True
    if email:
        for member in members:
            if member['email'] == email:
                return True

    return False