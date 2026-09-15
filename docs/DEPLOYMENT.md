# Deployment Guide

## 1. Local development (Docker Compose)

```bash
git clone <repo-url>
cd Create-Image-Product
cp .env.example .env      # edit values, especially DJANGO_SECRET_KEY and DJANGO_SUPERUSER_PASSWORD
docker compose up --build
```

This starts: `db` (Postgres), `redis`, `backend` (Django/gunicorn, runs migrations + seeds defaults +
creates the admin user on first boot), `worker` (Celery), `beat` (Celery beat, for future scheduled
tasks like periodic batch-progress rollups or expiring old ZIP downloads), and `frontend` (Next.js).

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/
- Backend API docs (Swagger UI): http://localhost:8000/api/docs/
- Django admin: http://localhost:8000/admin/ (log in with `DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD`)

The default `.env` uses `STORAGE_BACKEND=local`, which stores uploads/outputs on the `backend`
container's filesystem (a named Docker volume, `media`) — this is fine for local dev/demo but is
**not durable across container rebuilds without the volume, and does not work with multiple backend
replicas**. Switch to S3/R2 (below) for anything beyond local dev.

## 2. Running without Docker (bare processes)

Useful for active backend development.

```bash
# Postgres + Redis (via Docker, or your own local install)
docker compose up -d db redis

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=config.settings.dev
export POSTGRES_HOST=localhost STORAGE_BACKEND=local AI_RECREATE_PROVIDER=noop
python manage.py migrate
python manage.py seed_defaults
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000

# Celery worker (separate terminal, same venv/env vars)
celery -A config worker --loglevel=info --concurrency=2

# Frontend (separate terminal)
cd frontend
npm install
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local
npm run dev
```

## 3. Configuring S3 / Cloudflare R2 storage

Set in `.env` (or your platform's secret manager in production):

```bash
STORAGE_BACKEND=s3
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=your-bucket
S3_REGION=auto              # AWS: an actual region, e.g. us-east-1
S3_ENDPOINT_URL=            # AWS S3: leave blank. R2: https://<account_id>.r2.cloudflarestorage.com
S3_SIGNED_URL_TTL_SECONDS=3600
```

Bucket setup:
- Create the bucket, keep it **private** (the app issues signed URLs for all reads/downloads).
- CORS: allow `GET`/`PUT` from your frontend's origin if you later add direct browser→S3 uploads.
- IAM/API token: needs `GetObject`, `PutObject`, `DeleteObject`, `ListBucket` on the bucket.

These same values are editable at runtime (non-secret fields only — the bucket name/region/endpoint/
prefix/TTL) from **Admin Settings → Storage settings** in the app; credentials always come from
environment variables / your platform's secret manager, never from the database.

## 4. Configuring AI Recreate Studio Mode

```bash
AI_RECREATE_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_IMAGE_MODEL=gpt-image-1
```

Leave `AI_RECREATE_PROVIDER=noop` to run without any external AI calls — Recreate Studio Mode jobs
will still run the full pipeline, just with a passthrough "recreation" step, useful for testing/demos
without incurring API costs. See `docs/AI_PROMPTS.md` to add other providers.

## 5. Production deployment notes

The same Docker images (`backend/Dockerfile`, `backend/Dockerfile.worker`, `frontend/Dockerfile`)
work on any container platform (ECS, Kubernetes, a single VM with `docker compose`, Fly.io, Render,
etc.). Production checklist:

- **Django**: set `DJANGO_SETTINGS_MODULE=config.settings.prod`, a strong random `DJANGO_SECRET_KEY`,
  `DJANGO_DEBUG=false`, and `DJANGO_ALLOWED_HOSTS` to your real domain(s). `config/settings/prod.py`
  turns on HSTS, secure cookies, and SSL redirect — put the app behind a TLS-terminating proxy/load
  balancer that sets `X-Forwarded-Proto`.
- **Database**: use a managed Postgres (RDS, Cloud SQL, etc.) instead of the `db` container; point
  `POSTGRES_*` env vars at it. Run `python manage.py migrate` as a release step.
- **Redis**: use a managed Redis (ElastiCache, Upstash, etc.) instead of the `redis` container.
- **Storage**: `STORAGE_BACKEND=s3` (or R2) is required — `local` storage does not work with more
  than one backend/worker replica and has no durability guarantees.
- **Workers**: scale the `worker` service horizontally for batch throughput; each `ProcessingJob` is
  an independent task, so more workers directly increases parallel image throughput. Keep `beat` to
  exactly one replica (it schedules periodic tasks; running more than one duplicates them).
- **Static files**: `whitenoise` serves Django admin/static assets directly from the `backend`
  container — no separate static file server needed. `collectstatic` runs automatically in the
  container entrypoint.
- **Secrets**: never commit `.env`. Use your platform's secret manager (AWS Secrets Manager, GCP
  Secret Manager, Kubernetes Secrets, Fly secrets, etc.) to inject the same variable names at deploy
  time.
- **Frontend**: `NEXT_PUBLIC_API_BASE_URL` is baked in at build time (Next.js public env var
  convention) — rebuild the `frontend` image if the backend's public URL changes.
- **Health checks**: `GET /healthz/` on the backend is unauthenticated and safe for load balancer /
  orchestrator liveness probes.

## 6. First-run checklist
1. `docker compose up --build`, wait for `backend` to report healthy.
2. Log into the frontend with the seeded admin account.
3. Go to **Admin Settings** and review/adjust pipeline defaults, QC thresholds, and (if using S3/R2)
   confirm storage settings.
4. Go to **Admin Settings → AI prompt templates** and add any category-specific prompts you want
   (see `docs/AI_PROMPTS.md` for examples); a sensible generic default is seeded automatically.
5. Upload a small test batch in both Enhance Only and Recreate Studio modes, confirm outputs land in
   Results / Review Queue as expected, then invite the rest of the team.
