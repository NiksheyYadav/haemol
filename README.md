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

## AWS Elastic Beanstalk

For the simplest first production deployment on Elastic Beanstalk, use a single Docker web environment for the API and keep:
- Vercel for the frontend
- Supabase or another managed Postgres for `DATABASE_URL`
- S3 for file and audio storage
- `TASK_MODE=sync` for the first rollout

Why this setup is safest:
- the repo now has a root-level `Dockerfile` so Elastic Beanstalk can build the API directly
- it avoids trying to run the dev-only `docker-compose.yml`
- it removes Redis/Celery from the first deploy so we can get the core upload, extraction, analysis, and audio flow stable first

Elastic Beanstalk setup:
1. Create a new environment and choose `Web server environment`.
2. Use names like:
   - application name: `biomarkly-api`
   - environment name: `biomarkly-api-prod`
3. Use the Docker platform.
4. Set these environment properties in Elastic Beanstalk:
   - `APP_ENV=production`
   - `TASK_MODE=sync`
   - `DATABASE_URL=<your Supabase or managed Postgres URL>`
   - `SECRET_KEY=<strong random value>`
   - `ADMIN_METRICS_TOKEN=<strong random value>`
   - `AWS_ACCESS_KEY_ID=<iam access key>`
   - `AWS_SECRET_ACCESS_KEY=<iam secret>`
   - `AWS_REGION=ap-south-1`
   - `S3_BUCKET_NAME=biomarkly-uploads`
   - `SARVAM_API_KEY=<sarvam key>`
   - `POSTHOG_API_KEY=<posthog key>`
   - `POSTHOG_HOST=https://app.posthog.com`
5. Do not set `DATABASE_URL` to `localhost`.
6. After the environment is healthy, point Vercel `API_SERVER_URL` to the Elastic Beanstalk URL and redeploy the frontend.

GitHub Actions auto-deploy:
- Yes, create the Elastic Beanstalk application and environment first.
- After that, add these GitHub repository secrets:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_REGION`
  - `EB_APPLICATION_NAME`
  - `EB_ENVIRONMENT_NAME`
  - `EB_DEPLOY_BUCKET`
- The workflow at `.github/workflows/deploy-elastic-beanstalk.yml` will:
  - build a small source bundle with the API-only Docker setup
  - upload it to the S3 deploy bucket
  - create a new Elastic Beanstalk application version
  - update the target environment automatically on pushes to `main`

Recommended bucket:
- create a dedicated private S3 bucket for deploy bundles, for example `biomarkly-eb-deploys`

Recommended later improvement:
- move to a separate worker and queue only after the single-container API is stable in production

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
