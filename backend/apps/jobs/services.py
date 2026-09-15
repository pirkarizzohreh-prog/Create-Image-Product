from apps.adminconfig.models import PipelineSettings

from .models import JobStatus, ProcessingJob


def build_job_params(image):
    """Resolve effective pipeline params for an image: batch overrides fall
    back to the active admin PipelineSettings. Snapshotted onto the job so
    later admin edits don't retroactively change an in-flight/completed job."""
    batch = image.batch
    settings_row = PipelineSettings.get_active()

    prompt_template = batch.prompt_template
    if prompt_template is None:
        from apps.adminconfig.models import PromptTemplate

        prompt_template = PromptTemplate.get_default(category=image.category)

    return {
        "output_size_px": batch.output_size_px or settings_row.output_size_px,
        "padding_percent": batch.padding_percent if batch.padding_percent is not None else settings_row.padding_percent,
        "output_format": batch.output_format or settings_row.output_format,
        "output_quality": settings_row.output_quality,
        "qc_background_whiteness_tolerance": settings_row.qc_background_whiteness_tolerance,
        "qc_centering_tolerance_percent": settings_row.qc_centering_tolerance_percent,
        "qc_min_product_coverage_percent": settings_row.qc_min_product_coverage_percent,
        "qc_max_product_coverage_percent": settings_row.qc_max_product_coverage_percent,
        "qc_identity_similarity_threshold": settings_row.qc_identity_similarity_threshold,
        "prompt_template_text": prompt_template.template_text if prompt_template else None,
        "prompt_template_id": str(prompt_template.id) if prompt_template else None,
    }


def create_and_enqueue_job(image, attempt=1, extra_params=None):
    params = build_job_params(image)
    if extra_params:
        params.update(extra_params)

    job = ProcessingJob.objects.create(
        image=image,
        status=JobStatus.QUEUED,
        mode=image.effective_mode,
        params=params,
        attempt=attempt,
    )

    from apps.imaging.tasks import process_image_job

    process_image_job.delay(str(job.id))
    return job
