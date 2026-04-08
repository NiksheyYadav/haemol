# Biomarkly

Biomarkly is a monorepo with a Next.js frontend and a FastAPI backend for blood-report extraction, specialist analysis, multilingual narration, and privacy-aware report lifecycle management.

## Production deploy

For Vercel, deploy only the frontend and point it at a separately hosted Biomarkly API.

Recommended setup:
- Set `API_SERVER_URL=https://your-api-domain` in the Vercel project.
- Leave `NEXT_PUBLIC_API_URL` unset in Vercel so the frontend uses the built-in `/api/backend` proxy.
- Keep the backend deployed on Render, Railway, App Runner, ECS, or another Python host.

Why this matters:
- If `NEXT_PUBLIC_API_URL` is missing and no proxy exists, the app can fall back to `localhost`, which breaks parsing and uploads in production.
- The `/api/backend/*` rewrite keeps frontend requests same-origin on Vercel and forwards them to your real API.

## Render backend deploy

Biomarkly now includes a root-level [render.yaml](./render.yaml) Blueprint for deploying the FastAPI backend as a Docker web service on Render.

Why this setup works well:
- The backend binds to Render's runtime `PORT`.
- `TASK_MODE=sync` avoids requiring a separate Celery worker just to get production parsing and analysis working.
- The web service exposes `/health` for Render health checks.
- Secrets stay out of Git because the required credentials are marked with `sync: false`.

Render setup:
1. Push the latest repo changes to GitHub.
2. Open the Blueprint flow in Render and connect the repo.
3. Fill the required secret values:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `ADMIN_METRICS_TOKEN`
   - `S3_BUCKET_NAME`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `SARVAM_API_KEY`
   - `POSTHOG_API_KEY`
4. Deploy the `biomarkly-api` service.
5. Copy the Render backend URL, for example `https://biomarkly-api.onrender.com`.
6. In Vercel, set `API_SERVER_URL` to that Render URL.
7. Remove `NEXT_PUBLIC_API_URL` from Vercel if it is set.
8. Redeploy the frontend.

After both deploys are live, this should work:
- `https://biomarkly.vercel.app/api/backend/health`
- `https://biomarkly.vercel.app/api/backend/about`

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
