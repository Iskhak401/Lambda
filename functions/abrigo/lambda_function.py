import logging
from collections import defaultdict
from os import environ

import boto3
import requests
from psycopg2 import connect
from psycopg2.extras import RealDictCursor

log = logging.getLogger()
logging.basicConfig(level=logging.INFO, force=True)
# Uncomment the line below in order to debug
# logging.basicConfig(level=logging.DEBUG, force=True)

NO_STATUS = "- No statusss -"


def _get_api_token(cursor, integration_id):
    cursor.execute(f"SELECT key, value FROM integration_details WHERE {integration_id=}")
    integration_details = {row["key"]: row["value"] for row in cursor}

    client = boto3.client("secretsmanager", region_name=environ["REGION"])
    client_secret = client.get_secret_value(SecretId=integration_details["secret_name"]).get("SecretString")
    client_id = integration_details["client_id"]

    response = requests.post(
        "https://auth.sageworks.com/connect/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
    )

    log.info(f"Sageworks Auth response code: {response.status_code}, {client_id=}")
    if response.status_code == requests.status_codes.codes.OK:
        return response.json()["access_token"]
    log.debug(f"Failed Sageworks Auth request: {response.json()}")
    return


def _get_deal_status(customer_id, proposedloan_id, token):
    response = requests.get(
        f"https://api.sageworks.com/v1/proposed-loans?customerId={customer_id}&ids={proposedloan_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    log.info(f"Sageworks Loan status response code: {response.status_code}, {customer_id=}")

    if response.status_code == requests.status_codes.codes.OK:
        data = response.json()
        log.debug(f"--- Sageworks OK response: {data}")
        if data["items"]:
            return data["items"][0]["status"]
    return NO_STATUS


def lambda_handler(event, context):
    db_uri = environ["DATABASE_URI"]
    conn = connect(db_uri)
    log.info("Connected to DB")

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = (
        f"SELECT dp.id, dpd.key, dpd.value, p.integration_id "
        f"FROM deal_programs AS dp "
        f"JOIN deal_program_details dpd on dp.id = dpd.deal_program_id "
        f"JOIN programs p ON dp.program_id = p.id "
        f"JOIN integrations i on p.integration_id = i.id "
        f"JOIN integration_types it on i.integration_type_id = it.id "
        f"WHERE it.name = 'Abrigo' and it.version = '0.1';"
    )
    log.debug(f"--- Query: {query}")
    cursor.execute(query)

    deal_program_details = defaultdict(dict)
    for row in cursor:
        deal_program_details[row["id"]][row["key"]] = row["value"]
        deal_program_details[row["id"]]["integration_id"] = row["integration_id"]
    log.debug(f"--- Deal programs details: {deal_program_details}")

    if deal_program_details:
        update_status_query = "UPDATE deal_programs SET status='{status}' WHERE id='{deal_program_id}'"
        for deal_program_id, details in deal_program_details.items():
            token = _get_api_token(cursor, details["integration_id"])

            if not token:
                log.error("Failed to get token, continue")
                continue

            status = _get_deal_status(
                customer_id=details["abrigo_customer_id"],
                proposedloan_id=details["abrigo_proposedloan_id"],
                token=token,
            )
            if status != NO_STATUS:
                cursor.execute(update_status_query.format(status=status, deal_program_id=deal_program_id))
                conn.commit()
