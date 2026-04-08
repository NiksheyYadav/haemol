# Biomarkly

Biomarkly is a monorepo with a Next.js frontend and a FastAPI backend for blood-report extraction, specialist analysis, multilingual narration, and privacy-aware report lifecycle management.

## Local development

```bash
docker compose up --build
```

Services:
- `web` on `http://localhost:3000`
- `api` on `http://localhost:8000`
- `localstack` S3 API on `http://localhost:4566`

## AWS deployment notes

- The backend storage layer now targets Amazon S3 via `boto3`.
- `apprunner.yaml` is included for an AWS App Runner deployment path.
- ECS Fargate is the main alternative if you want tighter network control or separate worker scaling; the existing API and Celery Docker images can be reused as-is.

## IAM

Required AWS IAM permissions for the service account:
- `s3:PutObject`
- `s3:GetObject`
- `s3:DeleteObject`
- `s3:ListBucket`

Resource scope:
- `arn:aws:s3:::biomarkly-uploads`
- `arn:aws:s3:::biomarkly-uploads/*`

## Verify local S3

```bash
aws s3 ls s3://biomarkly-uploads --endpoint-url http://localhost:4566
```
