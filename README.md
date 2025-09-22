# Serverless Purchase Demo

A minimal **serverless** app that demonstrates an event-driven pattern on AWS:

- **Frontend** (S3 static site) sends JSON to an **API Gateway** endpoint.
- **Lambda (API → SQS)** enqueues messages from the API.
- **Lambda (SQS → DynamoDB)** processes messages and writes them to a DynamoDB table.

All cloud identifiers are **placeholders** and must be provided from your own AWS account:
`{ACCOUNT_ID}`, `{REGION}`, `{BUCKET_NAME}`, `{QUEUE_ARN}`, `{QUEUE_URL}`, `{TABLE_ARN}`, `{APIGW_BASE_URL}`, `{APIGW_PATH}`.

---

## Architecture

Browser (S3 static website)
└─> PUT {APIGW_BASE_URL}/{APIGW_PATH}
└─> Amazon API Gateway (proxy)
└─> Lambda #2: lambda2-api-producer (API → SQS)
└─> Amazon SQS (queue)
└─> Lambda #1: lambda1-queue-consumer (SQS → DynamoDB)
└─> Amazon DynamoDB (table)


**Data flow**  
1. The web page calls API Gateway with a JSON payload.  
2. Lambda #2 pushes the JSON into SQS.  
3. Lambda #1 is triggered by SQS, validates the JSON and writes an item to DynamoDB.

---

## Repository Layout

backend/
lambda1-queue-consumer/ # SQS → DynamoDB
└─ main.py
lambda2-api-producer/ # API → SQS
└─ main.py
frontend/
└─ index.html # Static site (S3)
infra/
iam/
├─ lambda-policy.json # example IAM policy (reference)
└─ trust-lambda.json # example trust policy (reference)
s3/
├─ frontend-bucket-policy.json # example public read (reference)
└─ site.json # S3 website config (index suffix)
samples/
└─ purchase.json # example request body

**Note**  
> The files under `infra/` and `s3/` are **examples** meant to guide your config.  
> You’ll still create resources in your own account (via console or CLI) and plug in your real ARNs/URLs.

---

## Prerequisites

- AWS account with permissions to create S3, SQS, DynamoDB, Lambda, and API Gateway.
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) configured (e.g. `aws configure`).
- Python 3.11+ runtime available for Lambda packaging (if you zip locally).
- A terminal (PowerShell or bash). The snippets below are PowerShell-style; shell equivalents are trivial.

---

## 1) Create core resources

### DynamoDB
- **Table name**: `ProductPurchases`
- **Partition key**: `ProductPurchaseKey` (String)
- Billing: On-demand is fine for demos.

### SQS
- **Queue name**: e.g. `ProductPurchasesDataQueue`
- Copy the **Queue URL** and **Queue ARN**.

---

## 2) Deploy back-end Lambdas

### Lambda #2 — API Producer (API → SQS)
**Function**: `lambda2-api-producer/main.py`
- Environment variables:
  - `AWS_REGION` = your region, e.g. `us-east-1`
  - `QUEUE_URL` = your SQS URL
- IAM permissions must include:
  - `sqs:SendMessage` on your queue
  - CloudWatch Logs permissions

**Example trust policy** (attach to the role used by this function):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Principal": { "Service": "lambda.amazonaws.com" }, "Action": "sts:AssumeRole" }
  ]
}
```

**Example permission policy (replace placeholders with your real values):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["sqs:SendMessage"],
      "Resource": "arn:aws:sqs:{REGION}:{ACCOUNT_ID}:ProductPurchasesDataQueue"
    },
    {
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],
      "Resource": "*"
    }
  ]
}
```

## 2) Lambda #1 — Queue Consumer (SQS → DynamoDB)

**Function:** `lambda1-queue-consumer/main.py`

**Environment variables**

- `AWS_REGION` – e.g., `us-east-1`
- `TABLE_NAME` – e.g., `ProductPurchases`

**IAM permissions must include**

- `dynamodb:PutItem` on your DynamoDB table
- CloudWatch Logs permissions (create log group/stream, put log events)

**Event source mapping**

Create an **SQS trigger** (event source mapping) from your queue to this function.

---

## 3) API Gateway (REST)

1. Create a resource: `/productpurchase`.
2. Add a **PUT** method with **Lambda proxy integration** → point it to **Lambda #2 (API Producer)**.
3. **Enable CORS** for the resource & method (an `OPTIONS` method should be created automatically; if not, add it).
4. **Deploy** to a stage, e.g., `dev`.
5. Note the **Invoke URL**, e.g.:  
   `https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev/productpurchase`

---

## 4) Frontend (S3 static website)

1. Create a bucket (e.g., `product-purchase-form-XXXXXXXX`) in your `{REGION}`.
2. Enable **static website hosting**; set index to `index.html`.
3. Allow **public read** to objects (bucket policy) – see `s3/frontend-bucket-policy.json` for a canonical pattern.
4. Open `frontend/index.html` and set your API URL:

```
const API_URL = "https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/dev/productpurchase";
```
5.Upload frontend/index.html to the bucket root.
6.Visit the bucket website endpoint; submit a record from the page.

---
## Troubleshooting

### CORS errors in browser
- In API Gateway, ensure **CORS** is enabled for the resource and method.
- Lambda #2 returns CORS headers (e.g., `Access-Control-Allow-Origin: *`). Confirm they’re present on **2xx** and **error** responses.

### S3 `403 AccessDenied` (website)
- Confirm bucket policy allows `s3:GetObject` on `arn:aws:s3:::{BUCKET_NAME}/*`.
- Confirm **Block Public Access** is disabled for this demo bucket.

### SQS trigger stuck in `Creating`
- Re-check permissions on **Lambda #1’s** execution role.
- Ensure the SQS queue is in the **same region** as the function.

### API `500` from Lambda #2
- Check **CloudWatch Logs** for stack traces.
- Verify the env variables (especially `QUEUE_URL`) are set.

### No rows in DynamoDB
- Open logs for **Lambda #1**; confirm the function is invoked by SQS.
- Validate the JSON you send (use the `samples/purchase.json` template).
---
