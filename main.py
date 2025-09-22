import json
import os
import logging
import boto3
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.getenv("AWS_REGION", "{REGION}")
TABLE_NAME = os.getenv("TABLE_NAME", "ProductPurchases")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Triggered by SQS. Expects records with MessageBody containing JSON purchase data.
    Writes each record to DynamoDB.
    """
    logger.info("Event: %s", json.dumps(event))
    for record in event.get("Records", []):
        body = record.get("body")
        if not body:
            logger.warning("Record missing body")
            continue

        try:
            data = json.loads(body)
        except Exception:
            logger.exception("Invalid JSON in body")
            continue

        # Ensure a primary key exists
        if "ProductPurchaseKey" not in data:
            data["ProductPurchaseKey"] = str(uuid4())

        # Optional: normalize timestamp
        data.setdefault("TimeOfPurchase", datetime.utcnow().isoformat())

        logger.info("Putting item: %s", json.dumps(data))
        table.put_item(Item=data)

    return {"status": "ok"}
