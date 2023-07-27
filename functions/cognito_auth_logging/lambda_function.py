import logging
from os import environ

from psycopg2 import connect

log = logging.getLogger()
logging.basicConfig(level=logging.INFO, force=True)
# Uncomment the line below in order to debug
# logging.basicConfig(level=logging.DEBUG, force=True)


def lambda_handler(event, context):
    db_uri = environ["DATABASE_URI"]
    query = (
        f"INSERT INTO logins (user_id) "
        f"SELECT id from users "
        f"WHERE email='{event['request']['userAttributes']['email']}';"
    )

    with connect(db_uri) as conn:
        log.info("Connected to DB")
        with conn.cursor() as cursor:
            cursor.execute(query)
            log.info("Record inserted")

    return event
