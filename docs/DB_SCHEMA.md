# Database Schema

PostgreSQL, all primary keys are UUIDs. All tables inherit `created_at` / `updated_at` timestamps
(`apps.common.models.TimeStampedModel`) unless noted.

## accounts.User
Custom user model (`AUTH_USER_MODEL`), email/password auth.

| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| email | citext/unique | login identifier |
| full_name | varchar(255) | |
| role | enum: uploader / reviewer / admin | default `uploader` |
| is_active | bool | |
| is_staff | bool | Django admin access |
| date_joined | timestamptz | |

## products.Batch
A named group of images uploaded together.

| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | varchar(255) | |
| owner | FK → User | |
| default_mode | enum: recreate_studio / enhance_only | |
| output_size_px | int, null | overrides admin default |
| padding_percent | float, null | overrides admin default |
| output_format | varchar(10), null | overrides admin default |
| prompt_template | FK → adminconfig.PromptTemplate, null | |

## products.ProductImage
One uploaded source image, belongs to a Batch.

| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| batch | FK → Batch | |
| uploaded_by | FK → User | |
| source_file | file (S3) | `sources/{batch_id}/{id}_{filename}` |
| original_filename, content_type, size_bytes, width, height | | |
| sku, product_name, category | varchar | free-text metadata |
| processing_mode | enum, null | per-image override of batch default |

## jobs.ProcessingJob
One processing attempt for a ProductImage. New retries/reruns create a **new** row (full history
kept; `attempt` increments).

| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| image | FK → ProductImage | |
| status | enum: queued / processing / needs_review / completed / failed / rejected | |
| mode | varchar | snapshot of effective mode at enqueue time |
| params | JSONB | snapshot of resolved pipeline params (size, padding, format, QC thresholds, prompt text) |
| output_file | file (S3), null | `outputs/{job_id}.{ext}` |
| output_width, output_height, output_checksum | | |
| qc_passed | bool, null | |
| qc_report | JSONB | structured QC check results |
| error_message | text | |
| started_at, finished_at | timestamptz, null | |
| attempt | int | 1-indexed |

Indexes: `status`, `mode`.

## jobs.JobStageLog
One row per pipeline stage execution, for the Jobs/Progress UI and debugging.

| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| job | FK → ProcessingJob | |
| stage | enum: ingest / enhance / ai_recreate / remove_background / compose_white / square_center_pad / export / qc | |
| status | enum: running / success / skipped / failed | |
| started_at, finished_at, duration_ms | | |
| detail | JSONB | stage-specific metrics (e.g. QC scores, AI provider used) |
| error_message | text | |

## review.ReviewItem
Created when a job's QC fails, a stage errors, or QC flags for manual review.

| Field | Type | Notes |
|---|---|---|
| id | UUID PK | |
| job | FK → ProcessingJob | |
| reasons | JSONB (list) | QC failure reasons / error summaries |
| decision | enum: pending / approved / rejected / replaced / rerun | |
| decision_notes | text | |
| reviewed_by | FK → User, null | |
| reviewed_at | timestamptz, null | |

## adminconfig.PipelineSettings
Admin-editable defaults. Effectively a singleton (`is_active=True` on at most one row at a time —
enforced in `save()`); history of past settings retained for audit.

| Field | Type | Notes |
|---|---|---|
| output_size_px | int | default 2000 |
| padding_percent | float | default 8.0 |
| output_format | enum: WEBP / PNG / JPEG | default WEBP |
| output_quality | int | default 90 |
| qc_background_whiteness_tolerance | float | |
| qc_centering_tolerance_percent | float | |
| qc_min_product_coverage_percent, qc_max_product_coverage_percent | float | |
| qc_identity_similarity_threshold | float | |

## adminconfig.PromptTemplate
Named AI prompt templates for Recreate Studio Mode, optionally scoped by category.

| Field | Type | Notes |
|---|---|---|
| name | varchar | |
| category | varchar, blank = applies to all | |
| template_text | text | |
| is_default | bool | one default per category (enforced in `save()`) |

## adminconfig.StorageSettings
Non-secret operational storage config (credentials stay in environment variables).

| Field | Type | Notes |
|---|---|---|
| provider | enum: s3 / r2 / local | |
| bucket_name, region, endpoint_url, path_prefix | | |
| signed_url_ttl_seconds | int | |

## Entity relationship summary
```
User 1──* Batch 1──* ProductImage 1──* ProcessingJob 1──* JobStageLog
                                              │
                                              └──1──1 ReviewItem (when flagged)
PromptTemplate *──1 Batch (optional override)
```
