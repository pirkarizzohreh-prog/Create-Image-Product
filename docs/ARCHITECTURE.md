# System Architecture

## 1. High-level diagram

```
                       ┌─────────────────────┐
                       │   Next.js Frontend    │
                       │  (App Router, TS)     │
                       └──────────┬───────────┘
                                  │ HTTPS / REST (JSON) + JWT
                                  ▼
                       ┌─────────────────────┐
                       │  Django + DRF API     │
                       │  (accounts, products, │
                       │  jobs, review, config) │
                       └──────┬───────┬───────┘
                              │       │
                 enqueue task │       │ reads/writes
                              ▼       ▼
                     ┌─────────────┐ ┌──────────────┐
                     │ Redis broker │ │ PostgreSQL   │
                     └──────┬──────┘ └──────────────┘
                            │
                            ▼
                 ┌───────────────────────┐
                 │   Celery workers        │
                 │  (imaging pipeline:     │
                 │  enhance → AI recreate  │
                 │  → bg removal → white   │
                 │  → square/center/pad →  │
                 │  export → QC)           │
                 └──────────┬─────────────┘
                             │ read/write objects
                             ▼
                 ┌───────────────────────┐
                 │ S3-compatible storage  │
                 │ (AWS S3 / Cloudflare R2)│
                 └───────────────────────┘
```

## 2. Repository layout

```
Create-Image-Product/
├── docs/                         # PRD, architecture, prompts, setup
├── backend/                      # Django + DRF + Celery
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── config/                   # Django project (settings, urls, celery app)
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── dev.py
│   │   │   └── prod.py
│   │   ├── urls.py
│   │   ├── celery.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   └── apps/
│       ├── accounts/              # Custom User model, roles, JWT auth endpoints
│       ├── products/              # Product, Batch, ProductImage models + API
│       ├── jobs/                  # ProcessingJob, JobStageLog, state machine + API
│       ├── review/                # ReviewItem, review workflow + API
│       ├── adminconfig/           # PipelineSettings, PromptTemplate, StorageSettings + API
│       └── imaging/               # Pipeline stages (pure Python, no Django deps) + Celery tasks
├── frontend/                      # Next.js (App Router, TypeScript, Tailwind)
│   ├── app/
│   │   ├── login/
│   │   ├── (dashboard)/
│   │   │   ├── upload/
│   │   │   ├── jobs/
│   │   │   ├── jobs/[id]/
│   │   │   ├── results/[batchId]/
│   │   │   ├── review/
│   │   │   └── admin/settings/
│   ├── components/
│   ├── lib/                       # api client, auth context, types
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## 3. Backend domain model (summary — full detail in `docs/DB_SCHEMA.md`)

- **User** (accounts) — email, role (`uploader` / `reviewer` / `admin`), auth via JWT (SimpleJWT).
- **Batch** (products) — a named group of images uploaded together, owned by a user, default
  processing mode + overrides.
- **ProductImage** (products) — one uploaded source image, belongs to a Batch, optional Product
  metadata (SKU/name/category — free text, not a strict catalog integration in v1).
- **ProcessingJob** (jobs) — 1:1 with a ProductImage per processing attempt; state machine
  (`queued → processing → needs_review → completed` / `failed` / `rejected`); stores processing mode,
  params snapshot, output asset refs, QC results.
- **JobStageLog** (jobs) — one row per pipeline stage execution (name, status, duration, error) for
  observability on the Jobs/Progress page.
- **ReviewItem** (review) — created when a job's QC fails or a stage errors; links to the job,
  QC reasons, reviewer decision, decision notes, timestamps.
- **PipelineSettings** (adminconfig) — singleton-ish (one active row) admin-editable defaults:
  output size, padding %, format, QC thresholds.
- **PromptTemplate** (adminconfig) — named AI prompt templates for Recreate Studio Mode, optionally
  scoped to a product category, with an "active default" flag.
- **StorageSettings** (adminconfig) — active bucket/region/endpoint/prefix config (secrets stay in
  env vars; this stores non-secret operational config plus a reference to which env credentials to
  use).

## 4. API surface (REST, DRF, JSON, JWT bearer auth)

```
POST   /api/auth/login/                     obtain JWT pair
POST   /api/auth/refresh/                   refresh JWT
GET    /api/auth/me/                        current user + role

GET    /api/users/                          [admin] list users
PATCH  /api/users/{id}/                     [admin] change role/active

POST   /api/batches/                        create batch (+ default mode/params)
GET    /api/batches/                        list own (or all, if reviewer/admin) batches
GET    /api/batches/{id}/                   batch detail incl. image/job summary
POST   /api/batches/{id}/download/          presigned ZIP of all completed outputs

POST   /api/images/                         upload image(s) to a batch (multipart, supports multi-file)
GET    /api/images/{id}/                    image detail

GET    /api/jobs/                           list jobs (filter: status, batch, mine)
GET    /api/jobs/{id}/                      job detail incl. stage logs + QC report
POST   /api/jobs/{id}/retry/                re-queue a failed/rejected job
GET    /api/jobs/{id}/stream/                SSE/poll endpoint for live progress (see §6)

GET    /api/review/                         list review queue items (reviewer/admin)
POST   /api/review/{id}/approve/            approve as-is → completed
POST   /api/review/{id}/reject/             reject with reason → rejected, notifies uploader
POST   /api/review/{id}/rerun/              re-run pipeline with optional param overrides
POST   /api/review/{id}/replace/            upload manual replacement output → completed

GET    /api/admin/pipeline-settings/        [admin] get active settings
PUT    /api/admin/pipeline-settings/        [admin] update
GET    /api/admin/prompt-templates/         [admin] list/CRUD
GET    /api/admin/storage-settings/         [admin] get/update
```

Permissions: DRF permission classes per role; object-level checks so Uploaders only see their own
batches/jobs, Reviewers/Admins see all.

## 5. Image processing pipeline (Celery task chain)

Implemented as a **Celery chain** of idempotent, checkpointed subtasks per `ProcessingJob`, orchestrated
in `apps/imaging/tasks.py`, calling into pure-Python pipeline stage functions in `apps/imaging/pipeline/`
(kept framework-free so they're independently unit-testable):

1. `stage_ingest` — download source from storage, validate (Pillow open, EXIF-transpose, min
   resolution, format allow-list). Writes `job.stage_logs`.
2. `stage_enhance` — OpenCV/Pillow: denoise (fastNlMeansDenoisingColored), auto white balance (gray
   world), exposure/contrast (CLAHE on L channel), unsharp mask, optional Lanczos upscale to a
   configurable minimum edge length before further processing.
3. `stage_ai_recreate` *(Recreate Studio Mode only)* — calls a pluggable `AIRecreateProvider`
   (interface in `apps/imaging/ai/base.py`) with the enhanced image + rendered prompt (from
   `PromptTemplate`), asking for a front-facing studio product photo preserving identity. Ships with
   an OpenAI Images-edit implementation and a local no-op/passthrough implementation for
   offline/dev use when no API key is configured, so the rest of the pipeline is testable without
   external calls.
4. `stage_remove_background` — salient/product segmentation via `rembg` (U^2-Net) producing an
   RGBA cutout; OpenCV morphological close/open + Gaussian-feathered alpha edge to reduce halos.
5. `stage_compose_white` — alpha-composite the cutout onto a pure-white RGB canvas sized to the
   cutout's bounding box + configured padding.
6. `stage_square_center_pad` — compute the max content dimension, build an N×N white canvas
   (N = configured output size), resize content to fit within `(1 - padding%) * N` preserving aspect
   ratio, paste centered → guarantees equal padding on all 4 edges by construction.
7. `stage_export` — encode to configured format (WebP default, quality configurable), write to
   storage under `outputs/{job_id}.webp`, store checksum + dimensions.
8. `stage_qc` — run QC checks from PRD §4.3 (`apps/imaging/qc.py`); on pass → job `completed`; on any
   failure/exception at any stage → job `needs_review` + `ReviewItem` created with reasons attached.

Each stage function takes/returns an explicit typed context object and never mutates ORM state itself
— the Celery task wrapper does ORM updates + `JobStageLog` writes, keeping pipeline logic portable and
testable outside Django/Celery.

Batch fan-out: submitting a Batch with N images enqueues N independent `ProcessingJob` chains
(`celery.group`) so images process in parallel across workers; a lightweight periodic Celery beat
task rolls up batch-level progress for the UI.

## 6. Progress reporting
`ProcessingJob.status` + `JobStageLog` rows are the source of truth. The frontend Jobs page polls
`GET /api/jobs/?batch=...` every few seconds (simple, robust, no infra for websockets required);
`GET /api/jobs/{id}/stream/` is provided as an SSE upgrade path for a snappier per-job progress view
without adding infrastructure dependencies.

## 7. Storage layout (S3/R2 bucket)
```
{prefix}/sources/{batch_id}/{image_id}.{ext}          # original upload, private
{prefix}/intermediate/{job_id}/{stage}.png             # optional debug artifacts (configurable, TTL'd)
{prefix}/outputs/{job_id}.webp                          # final catalog image
{prefix}/zips/{batch_id}.zip                            # generated on-demand batch download, TTL'd
```
All objects are private; the API issues short-lived presigned URLs for read/download and for direct
browser→S3 multipart upload on large batches (frontend uses presigned PUT to avoid proxying big
files through Django).

## 8. Deployment
Everything ships as containers (`docker-compose.yml` for local/dev; the same images are deployable to
ECS/Kubernetes/a single VM with `docker compose -f docker-compose.prod.yml up`): `frontend`, `backend`
(Django/gunicorn), `worker` (Celery), `beat` (Celery beat), `redis`, `db` (Postgres; swappable for a
managed RDS/managed Postgres in prod). See `docs/DEPLOYMENT.md` for step-by-step instructions.
