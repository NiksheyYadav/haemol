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

Biomarkly now includes a root-level [render.yaml](./render.yaml) Blueprint for deploying the backend on Render with:
- a Docker web service for the FastAPI API
- a Docker background worker for Celery jobs
- a Render Key Value instance for Redis-compatible queueing and caching

Why this setup works well:
- The backend binds to Render's runtime `PORT`.
- `TASK_MODE=async` keeps uploads and API requests fast while extraction, analysis, and audio run on the worker.
- The web service exposes `/health` for Render health checks.
- The worker reuses the API service's secrets via Blueprint references, so you enter them once.
- The queue uses Render Key Value with `noeviction`, which is safer for background jobs than a cache-oriented eviction policy.

Render setup:
1. Push the latest repo changes to GitHub.
2. Open the Blueprint flow in Render and connect the repo.
3. Fill the required secret values on `biomarkly-api`:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `ADMIN_METRICS_TOKEN`
   - `S3_BUCKET_NAME`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `SARVAM_API_KEY`
   - `POSTHOG_API_KEY`
4. Let Render create these resources:
   - `biomarkly-api`
   - `biomarkly-worker`
   - `biomarkly-cache`
5. Deploy the Blueprint.
6. Confirm the worker is running before load-testing uploads or audio.
7. Copy the Render backend URL, for example `https://biomarkly-api.onrender.com`.
8. In Vercel, set `API_SERVER_URL` to that Render URL.
9. Remove `NEXT_PUBLIC_API_URL` from Vercel if it is set.
10. Redeploy the frontend.

Important:
- Do not manually set `DATABASE_URL` to `localhost` on Render.
- The Blueprint assumes you are using an external Postgres database such as Supabase, Neon, or RDS.
- `REDIS_URL`, `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND` are wired automatically from Render Key Value.
- If you created your current Render backend manually instead of through the Blueprint, either sync the Blueprint or create the worker and Key Value services manually with the same env values.

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
