import json
import os
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.getenv("AWS_REGION", "{REGION}")
QUEUE_URL = os.getenv("QUEUE_URL", "{SQS_QUEUE_URL}")

sqs = boto3.client("sqs", region_name=REGION)

def _ok(body):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }

def _error(status, msg):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": msg}),
    }

def lambda_handler(event, context):
    """
    Expected to be invoked by API Gateway (proxy integration).
    """
    logger.info("Event: %s", json.dumps(event))
    try:
        if event.get("httpMethod") not in ("PUT", "POST"):
            return _error(405, "Method not allowed")

        body = event.get("body")
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")

        if not body:
            return _error(400, "Request body is required")

        # Validate minimal JSON
        data = json.loads(body)
        if "CustomerId" not in data or "ProductId" not in data:
            return _error(400, "Missing required fields: CustomerId, ProductId")

        # Enqueue
        resp = sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(data))
        logger.info("SQS send_message resp: %s", resp)

        return _ok({"messageId": resp.get("MessageId")})
    except Exception as e:
        logger.exception("Failed to enqueue message")
        return _error(500, f"Internal error: {str(e)}")
