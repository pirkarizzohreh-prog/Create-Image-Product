# AI Prompt Templates & QC Logic

## 1. Recreate Studio Mode prompting

Recreate Studio Mode calls a pluggable `AIRecreateProvider` (`backend/apps/imaging/ai/`) with the
**enhanced** source photo (after denoise/white-balance/contrast/sharpen, before background removal)
plus a rendered prompt from an admin-managed `PromptTemplate` row. The template is resolved per job as:

1. `Batch.prompt_template` if the batch explicitly sets one, else
2. the default `PromptTemplate` for the image's `category`, else
3. the global default `PromptTemplate` (`category=""`, `is_default=True`).

### Default template (seeded by `seed_defaults`)
```
A professional studio product photograph of the exact same item shown in the reference image,
front-facing, centered, on a seamless pure white background, soft even studio lighting, no
shadows other than a subtle contact shadow, sharp focus, high detail. Preserve the product's
exact shape, proportions, color, material, texture, logos, and any printed text with complete
accuracy. Do not invent, add, remove, or alter any product features.
```

### Category-specific examples (create these via `/api/admin/prompt-templates/`)

**Footwear**
```
A professional e-commerce studio photograph of the exact shoe shown in the reference image,
three-quarter-hidden front view presented as a straight front-facing product shot, laces and
stitching crisp and true to the reference, on a seamless pure white background, soft studio
lighting with a faint contact shadow beneath the sole. Preserve the exact silhouette, colorway,
material texture (leather/mesh/suede as shown), and all logos/branding exactly as in the
reference. Do not change the shoe model, add new design elements, or alter proportions.
```

**Apparel (flat/ghost-mannequin style)**
```
A professional studio product photograph of the exact garment in the reference image, laid flat
or on an invisible mannequin, front-facing, centered, on a seamless pure white background, even
diffused lighting with no harsh shadows. Preserve the garment's exact color, pattern, fabric
texture, seams, and any prints/logos precisely as shown. Do not restyle, add folds that hide
detail, or change the garment's fit or cut.
```

**Electronics / hard goods**
```
A professional studio product photograph of the exact device/object in the reference image,
front-facing, centered, on a seamless pure white background, clean specular studio lighting
appropriate for hard glossy or matte surfaces, subtle reflection permitted if realistic. Preserve
exact proportions, ports, buttons, screen contents (if any, keep blank/off unless shown on),
color, and finish. Do not add or remove physical features.
```

### Prompt-engineering guidelines encoded above (apply when writing new templates)
- Always anchor with "the exact same item / exact [item type] shown in the reference image" to bias
  the model toward preservation over creative reinterpretation.
- Always specify: front-facing, centered, seamless pure white background, studio lighting, subtle/contact
  shadow only.
- Always include an explicit negative instruction ("Do not invent/add/remove/alter...") — this
  measurably reduces hallucinated features in identity-preservation use cases.
- Keep category-specific vocabulary (materials, typical presentation angle) to help the model choose
  a sensible canonical studio pose for that product type.

## 2. AI provider abstraction
`apps/imaging/ai/base.py` defines `AIRecreateProvider.recreate(image, prompt) -> Image`. Two
implementations ship:
- `NoopRecreateProvider` — passthrough, used when `AI_RECREATE_PROVIDER=noop` (default, no API key
  required) so the rest of the pipeline is fully testable offline.
- `OpenAIRecreateProvider` — calls OpenAI's `images/edits` endpoint with the source image + rendered
  prompt (`AI_RECREATE_PROVIDER=openai`, requires `OPENAI_API_KEY`).

Adding another provider (Stability, Replicate, an in-house model) means implementing the same
interface and adding a branch to `apps/imaging/ai/__init__.py:get_provider()` — no changes needed
elsewhere in the pipeline.

Any provider failure (timeout, safety block, malformed response) must raise `AIRecreateError`, which
the Celery task catches and routes the job to `needs_review` rather than failing silently or crashing
the batch.

## 3. Quality control (QC) logic
Implemented in `apps/imaging/qc.py`, run once per job after export, against the admin-configurable
thresholds on `PipelineSettings`:

| Check | What it measures | Failure implies |
|---|---|---|
| `background_whiteness` | Max RGB deviation from `#FFFFFF` sampled from the four canvas corners | Background wasn't fully cleaned / stray matte residue |
| `product_coverage` | % of final canvas pixels that are product (non-white) | Product clipped at edges (too high) or lost in frame (too low, e.g. failed segmentation) |
| `centering` | Pixel delta between opposite padding edges (left vs right, top vs bottom) | Asymmetric placement — should be ~0 by construction, so a failure here indicates a upstream bug worth flagging |
| `identity_similarity` *(Recreate mode only)* | Perceptual-hash (pHash) similarity between the enhanced source and the AI-recreated image, before background removal | AI recreation drifted from / hallucinated the original product |

`run_qc()` aggregates all applicable checks into one report:
```json
{
  "passed": false,
  "reasons": ["Product coverage ratio out of expected bounds ..."],
  "checks": { "background_whiteness": {...}, "product_coverage": {...}, "centering": {...} }
}
```
Any failed check (or any stage exception earlier in the pipeline — segmentation failure, AI provider
error, corrupt/unsupported upload) creates a `review.ReviewItem` and sets the job to `needs_review`,
rather than either silently shipping a bad image or hard-failing the whole batch.

## 4. Review queue decisions
A Reviewer acting on a `ReviewItem` (`/api/review/{id}/...`) can:
- **approve** — accept the current output as-is (`job.status → completed`).
- **reject** — mark rejected with a required reason; notifies the uploader.
- **rerun** — re-queue a new `ProcessingJob` (new `attempt`), optionally overriding mode/size/padding/format.
- **replace** — upload a manually edited final image directly as the job's output (`job.status → completed`).
