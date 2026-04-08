# Biomarkly

Biomarkly is a monorepo with a Next.js frontend and a FastAPI backend for blood-report extraction, specialist analysis, multilingual narration, and privacy-aware report lifecycle management.

## Production deploy

For Vercel, deploy only the frontend and point it at a separately hosted Biomarkly API.

Recommended setup:
- Set `API_SERVER_URL=https://your-api-domain` in the Vercel project.
- Leave `NEXT_PUBLIC_API_URL` unset in Vercel so the frontend uses the built-in `/api/backend` proxy.
- Keep the backend deployed on App Runner, ECS, Render, Railway, or another Python host.

Why this matters:
- If `NEXT_PUBLIC_API_URL` is missing and no proxy exists, the app can fall back to `localhost`, which breaks parsing and uploads in production.
- The `/api/backend/*` rewrite keeps frontend requests same-origin on Vercel and forwards them to your real API.

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
