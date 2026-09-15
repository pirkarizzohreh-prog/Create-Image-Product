# Product Requirements Document

## Product name
**PixelForge Studio** — Automated E-commerce Product Image Processing Platform

## 1. Problem statement
Teams photograph products on mobile phones under inconsistent lighting, backgrounds, and framing.
Turning these raw photos into catalog-ready assets (clean white background, square 1:1 crop,
centered, consistent padding, web-optimized format) today requires manual editing per image, which
does not scale with catalog size or launch velocity.

## 2. Goal
Provide an internal SaaS-style tool where any team member can upload raw product photos (single or
bulk), automatically run them through an image-processing pipeline, optionally use AI to fully
reconstruct the product as a professional studio shot, and get back standardized, download-ready
catalog images — with a human review safety net for anything the system isn't confident about.

## 3. Users & roles
| Role | Capabilities |
|---|---|
| **Uploader** (default) | Upload images, create jobs, view own jobs/results, download outputs |
| **Reviewer** | Everything Uploader can do, plus: view/act on the review queue (approve, reject, re-run, manually replace) for any user's jobs |
| **Admin** | Everything Reviewer can do, plus: manage users/roles, configure pipeline defaults (output size, padding %, format, AI prompts), manage storage settings, view system-wide job stats |

Auth is email/password (JWT), with team membership implicit (single-tenant internal tool; the schema
leaves room for multi-team via `Organization` later but v1 ships single-org).

## 4. Core user flows

### 4.1 Upload & batch processing
1. User logs in, goes to **Upload**.
2. Selects one or many images (drag/drop or file picker), optionally groups them under a **Batch**
   name (e.g. "Fall Catalog Drop 1").
3. Chooses **Processing Mode** per batch (can be overridden per image):
   - **Recreate Studio Mode** — AI rebuilds the product as a front-facing studio photo, preserving
     identity/shape/color/texture, then the deterministic pipeline (bg removal, white background,
     square, center, pad, export) runs on the result.
   - **Enhance Only Mode** — no generative recreation; only deterministic enhancement (denoise,
     sharpen, white balance/exposure correction), background removal, whitening, squaring, centering,
     padding, export.
4. Submits. A `Job` is created per image inside a `Batch`; jobs are queued to Celery immediately.

### 4.2 Processing pipeline (per image)
See `docs/ARCHITECTURE.md` §5 for the technical pipeline. Functionally, each image goes through:
1. Ingest & validate (format, size, corruption check).
2. Quality improvement (denoise, auto white balance, exposure/contrast normalization, sharpen,
   upscale if below minimum resolution).
3. *(Recreate mode only)* AI studio recreation via a pluggable generative image provider, prompted
   to preserve product identity while producing a clean front-facing studio photo.
4. Background removal (salient object segmentation).
5. Composite onto pure white (#FFFFFF) background.
6. Square canvas (1:1), product centered, equal padding on all 4 edges (padding % configurable).
7. Export as WebP (configurable: WebP/PNG/JPEG) at configured target size.
8. Quality control scoring (see §4.3) → pass → **Results**; fail/uncertain → **Review Queue**.

### 4.3 Quality control (QC)
Automated heuristic + model-assisted checks run after step 7:
- Background whiteness check (corner/edge sampling must be within tolerance of pure white).
- Product coverage ratio sane bounds (not near-empty frame, not clipped/cropped at edges).
- Alpha-matte edge quality (no large islands of stray pixels / halo artifacts).
- Centering/padding delta check (asymmetry beyond tolerance flags for review).
- *(Recreate mode)* identity-similarity score between source crop and recreated product region
  (perceptual hash / embedding cosine distance) below threshold flags for review — protects against
  AI drift/hallucination.
- Any pipeline stage exception (segmentation failure, AI provider error/timeout/safety-block) always
  routes to review rather than silently failing.

Flagged jobs land in **Review Queue** with the QC reason(s), original, and processed output
side-by-side. A Reviewer can: **Approve as-is**, **Reject** (with reason, notifies uploader),
**Re-run** (same or different mode/params), or **Replace** (upload a manually edited final image).

### 4.4 Results & download
- **Results** page: grid of completed images per batch/job with before/after toggle, per-image
  download, and **Download All (ZIP)** for a batch.
- Filter by status: queued / processing / needs review / rejected / completed.

### 4.5 Admin settings
Admin-configurable, applied as defaults to new jobs (and overridable per batch):
- Default output size (px, e.g. 2000×2000), default padding % (e.g. 8%).
- Default output format (WebP/PNG/JPEG) + quality/compression level.
- Default AI prompt templates for Recreate Studio Mode (see `docs/AI_PROMPTS.md`), per product
  category if desired.
- Storage settings: active storage backend (S3/R2), bucket, region, endpoint, path prefix,
  signed-URL TTL.
- QC thresholds (whiteness tolerance, centering tolerance, identity-similarity threshold).

## 5. Non-functional requirements
- **Scalable batch throughput**: horizontal Celery worker scaling; one image = one task; jobs are
  independently retryable.
- **Idempotent & resumable**: pipeline stages checkpoint intermediate artifacts so a retry does not
  redo already-completed stages.
- **Observability**: structured job status/state machine, per-stage timing + error capture, visible
  in the Jobs/Progress UI.
- **Security**: authenticated API only, per-object ownership + role-based permissions, signed/expiring
  URLs for private S3 objects, secrets via environment variables, no credentials in code.
- **Portability**: fully Dockerized; works locally via `docker compose up` and deploys the same way to
  a VM/ECS/Kubernetes.

## 6. Out of scope (v1)
- Multi-tenant billing/organizations.
- Non-product images (e.g. lifestyle/model shots) — pipeline assumes single-product-on-surface input.
- Mobile native app (upload works from mobile browser, no dedicated app).
- Automatic categorization/tagging of products (manual product metadata only).

## 7. Success metrics
- % of uploaded images reaching "completed" without manual review.
- Median end-to-end processing time per image / per 100-image batch.
- Reviewer queue turnaround time.
- Reduction in manual editing hours vs. baseline.
