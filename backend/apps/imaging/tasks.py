import logging
import time
from contextlib import contextmanager

from celery import shared_task
from django.conf import settings as django_settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.jobs.models import JobStageLog, JobStatus, ProcessingJob, StageName, StageStatus
from apps.review.models import ReviewItem

from .ai import get_provider
from .ai.base import AIRecreateError
from .pipeline.background import BackgroundRemovalError, stage_remove_background
from .pipeline.compose import stage_compose_white, stage_square_center_pad
from .pipeline.context import PipelineContext, PipelineParams
from .pipeline.enhance import stage_enhance
from .pipeline.export import EXT_BY_FORMAT, stage_export
from .pipeline.ingest import IngestError, stage_ingest
from .qc import run_qc

logger = logging.getLogger(__name__)


class StageFailure(Exception):
    """Raised to short-circuit the pipeline and route the job to manual
    review, carrying a human-readable reason."""

    def __init__(self, stage: str, reason: str):
        self.stage = stage
        self.reason = reason
        super().__init__(f"{stage}: {reason}")


@contextmanager
def _stage(job, stage_name):
    log = JobStageLog.objects.create(job=job, stage=stage_name, status=StageStatus.RUNNING)
    t0 = time.monotonic()
    try:
        result_detail = {}
        yield result_detail
        log.status = StageStatus.SUCCESS
        log.detail = result_detail
    except Exception as exc:
        log.status = StageStatus.FAILED
        log.error_message = str(exc)
        raise
    finally:
        log.finished_at = timezone.now()
        log.duration_ms = int((time.monotonic() - t0) * 1000)
        log.save()


def _send_to_review(job, reasons):
    job.status = JobStatus.NEEDS_REVIEW
    job.finished_at = timezone.now()
    job.save(update_fields=["status", "finished_at", "updated_at"])
    ReviewItem.objects.create(job=job, reasons=reasons)


@shared_task(bind=True, max_retries=0, acks_late=True)
def process_image_job(self, job_id: str):
    job = ProcessingJob.objects.select_related("image", "image__batch").get(id=job_id)
    job.status = JobStatus.PROCESSING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at", "updated_at"])

    params = PipelineParams.from_dict(job.params or {})
    ctx = PipelineContext(mode=job.mode, params=params)

    try:
        with _stage(job, StageName.INGEST) as d:
            source_bytes = job.image.source_file.read()
            try:
                ctx.image = stage_ingest(source_bytes)
            except IngestError as exc:
                raise StageFailure(StageName.INGEST, str(exc)) from exc
            d["source_size"] = ctx.image.size

        with _stage(job, StageName.ENHANCE) as d:
            ctx.image, enhance_detail = stage_enhance(ctx.image, params.min_processing_edge_px)
            ctx.detail["enhance"] = enhance_detail
            d.update(enhance_detail)

        if ctx.mode == "recreate_studio":
            with _stage(job, StageName.AI_RECREATE) as d:
                ctx.pre_ai_image = ctx.image.copy()
                provider_name = django_settings.AI_RECREATE_PROVIDER
                provider = get_provider(provider_name)
                prompt = params.prompt_template_text or (
                    "A professional studio product photograph of the exact same item, "
                    "front-facing, centered, on a seamless pure white background."
                )
                try:
                    ctx.image = provider.recreate(ctx.image, prompt)
                except AIRecreateError as exc:
                    raise StageFailure(StageName.AI_RECREATE, str(exc)) from exc
                ctx.post_ai_image = ctx.image.copy()
                d["provider"] = provider_name
                d["output_size"] = ctx.image.size
        else:
            JobStageLog.objects.create(job=job, stage=StageName.AI_RECREATE, status=StageStatus.SKIPPED)

        with _stage(job, StageName.REMOVE_BACKGROUND) as d:
            try:
                ctx.cutout_rgba, bg_detail = stage_remove_background(ctx.image)
            except BackgroundRemovalError as exc:
                raise StageFailure(StageName.REMOVE_BACKGROUND, str(exc)) from exc
            ctx.detail["remove_background"] = bg_detail
            d.update(bg_detail)

        with _stage(job, StageName.COMPOSE_WHITE) as d:
            ctx.image, compose_detail = stage_compose_white(ctx.cutout_rgba)
            ctx.detail["compose_white"] = compose_detail
            d.update({k: v for k, v in compose_detail.items() if k != "crop_bbox"})

        with _stage(job, StageName.SQUARE_CENTER_PAD) as d:
            ctx.final_image, square_detail = stage_square_center_pad(
                ctx.image, params.output_size_px, params.padding_percent
            )
            ctx.detail["square_center_pad"] = square_detail
            d.update(square_detail)

        with _stage(job, StageName.EXPORT) as d:
            ctx.export_bytes, export_detail = stage_export(ctx.final_image, params.output_format, params.output_quality)
            ctx.export_checksum = export_detail["checksum"]
            ctx.detail["export"] = export_detail
            d.update(export_detail)

        with _stage(job, StageName.QC) as d:
            qc_report = run_qc(ctx)
            d.update(qc_report)

        ext = EXT_BY_FORMAT.get(params.output_format.upper(), "webp")
        job.output_file.save(f"{job.id}.{ext}", ContentFile(ctx.export_bytes), save=False)
        job.output_width, job.output_height = ctx.final_image.size
        job.output_checksum = ctx.export_checksum
        job.qc_report = qc_report
        job.qc_passed = qc_report["passed"]
        job.status = JobStatus.COMPLETED if qc_report["passed"] else JobStatus.NEEDS_REVIEW
        job.finished_at = timezone.now()
        job.save()

        if not qc_report["passed"]:
            ReviewItem.objects.create(job=job, reasons=qc_report["reasons"])

    except StageFailure as exc:
        logger.warning("Job %s stage %s failed: %s", job.id, exc.stage, exc.reason)
        with transaction.atomic():
            job.error_message = f"[{exc.stage}] {exc.reason}"
            job.save(update_fields=["error_message", "updated_at"])
            _send_to_review(job, [f"{exc.stage} failed: {exc.reason}"])

    except Exception as exc:  # noqa: BLE001 - deliberate catch-all safety net
        logger.exception("Job %s failed with an unexpected error", job.id)
        with transaction.atomic():
            job.error_message = str(exc)
            job.save(update_fields=["error_message", "updated_at"])
            _send_to_review(job, [f"Unexpected pipeline error: {exc}"])

    return str(job.id)
