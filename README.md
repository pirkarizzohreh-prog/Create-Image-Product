# PixelForge Studio

Automated e-commerce product image processing: upload raw mobile photos, run them through a
background-removal / whitening / squaring / centering pipeline (with an optional AI "recreate as
professional studio photo" step), and get catalog-ready WebP images back — with a manual review
queue for anything the system flags as uncertain.

See `docs/PRD.md` for the full product spec and `docs/ARCHITECTURE.md` for the system design.

## Stack
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind CSS
- **Backend**: Django + Django REST Framework, JWT auth
- **Async processing**: Celery + Redis
- **Database**: PostgreSQL
- **Storage**: S3-compatible (AWS S3 or Cloudflare R2); local filesystem for offline dev
- **Image processing**: Pillow + OpenCV + rembg (U^2-Net background segmentation)

## Quick start

```bash
cp .env.example .env    # edit DJANGO_SECRET_KEY / DJANGO_SUPERUSER_PASSWORD at minimum
docker compose up --build
```

- App: http://localhost:3000 (log in with `DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD` from `.env`)
- API: http://localhost:8000/api/ (interactive docs at `/api/docs/`)
- Django admin: http://localhost:8000/admin/

Full setup options (bare-process dev without Docker, S3/R2 configuration, AI provider setup,
production deployment checklist) are in **`docs/DEPLOYMENT.md`**.

## Repository layout

```
docs/               PRD, architecture, DB schema, AI prompts, deployment guide
backend/            Django + DRF + Celery (apps/accounts, products, jobs, review, adminconfig, imaging)
frontend/           Next.js app (login, upload, jobs, results, review queue, admin settings)
docker-compose.yml  db, redis, backend, worker, beat, frontend
```

## Processing modes
- **Recreate Studio Mode** — AI rebuilds the product as a professional front-facing studio photo
  (preserving shape/color/texture/identity), then the deterministic pipeline finishes the job.
- **Enhance Only Mode** — preserves the original photo; only improves quality, removes the
  background, whitens, squares, centers, and standardizes it.

Both modes end with the same output contract: pure white background, square (1:1), product
perfectly centered with equal padding on all sides, exported as WebP (configurable).

## Docs index
- `docs/PRD.md` — product requirements
- `docs/ARCHITECTURE.md` — system architecture, API surface, pipeline design
- `docs/DB_SCHEMA.md` — database schema
- `docs/AI_PROMPTS.md` — AI prompt templates and QC logic
- `docs/DEPLOYMENT.md` — setup, configuration, and production deployment
