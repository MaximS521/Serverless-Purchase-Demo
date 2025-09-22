# Serverless Purchase Demo (Anonymized)

A minimal serverless app:
- **Frontend** (static S3 website) sends JSON to an API Gateway endpoint.
- **Lambda #2 (API → SQS)** enqueues messages from the API.
- **Lambda #1 (SQS → DynamoDB)** processes messages and writes them to a table.

> All cloud identifiers are placeholders:
`{ACCOUNT_ID}`, `{REGION}`, `{BUCKET_NAME}`, `{QUEUE_ARN}`, `{QUEUE_URL}`, `{TABLE_ARN}`, `{APIGW_BASE_URL}`, `{APIGW_PATH}`.

## Architecture
Browser → API Gateway → Lambda #2 → SQS → Lambda #1 → DynamoDB

## Configure for your account
- **Frontend**
  - `frontend/index.html`: set `API_BASE` to your API Gateway base URL and `API_PATH` to your resource path.
- **Lambda #2 (API Producer)**
  - `backend/lambda2-api-producer/main.py`: uses env vars `QUEUE_URL` and `AWS_REGION`.
- **Lambda #1 (Queue Consumer)**
  - `backend/lambda1-queue-consumer/main.py`: uses env vars `TABLE_NAME` and `AWS_REGION`.
- **IAM policies**
  - `infra/iam/lambda-policy.json`: replace `{ACCOUNT_ID}`, `{REGION}`, `{TABLE_NAME}`, `{QUEUE_NAME}` or set fully to your specific ARNs.
- **S3 website**
  - `infra/s3/frontend-bucket-policy.json`: set `{BUCKET_NAME}`.
  - `infra/s3/site.json`: keeps the index document.

## Notes
- Do not put credentials or build artifacts in the repo.
- Deployed S3 website and AWS resources live in your AWS account and are separate from this repo.
