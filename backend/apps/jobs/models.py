from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


def output_upload_path(instance, filename):
    return f"{settings.MEDIA_STORAGE_PREFIX}/outputs/{instance.id}.{filename.rsplit('.', 1)[-1]}"


class JobStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    PROCESSING = "processing", "Processing"
    NEEDS_REVIEW = "needs_review", "Needs Review"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    REJECTED = "rejected", "Rejected"


class ProcessingJob(TimeStampedModel):
    image = models.ForeignKey("products.ProductImage", on_delete=models.CASCADE, related_name="jobs")
    status = models.CharField(max_length=20, choices=JobStatus.choices, default=JobStatus.QUEUED)
    mode = models.CharField(max_length=32)  # snapshot of ProcessingMode at enqueue time

    # Snapshot of params used for this run (so admin changes mid-run don't retroactively apply).
    params = models.JSONField(default=dict, blank=True)

    output_file = models.FileField(upload_to=output_upload_path, null=True, blank=True)
    output_width = models.PositiveIntegerField(null=True, blank=True)
    output_height = models.PositiveIntegerField(null=True, blank=True)
    output_checksum = models.CharField(max_length=64, blank=True)

    qc_passed = models.BooleanField(null=True, blank=True)
    qc_report = models.JSONField(default=dict, blank=True)

    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    attempt = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["mode"])]

    def __str__(self):
        return f"Job({self.id}) {self.status}"

    @property
    def output_url(self):
        try:
            return self.output_file.url if self.output_file else None
        except ValueError:
            return None


class StageName(models.TextChoices):
    INGEST = "ingest", "Ingest & Validate"
    ENHANCE = "enhance", "Quality Enhancement"
    AI_RECREATE = "ai_recreate", "AI Studio Recreation"
    REMOVE_BACKGROUND = "remove_background", "Background Removal"
    COMPOSE_WHITE = "compose_white", "Composite on White"
    SQUARE_CENTER_PAD = "square_center_pad", "Square / Center / Pad"
    EXPORT = "export", "Export"
    QC = "qc", "Quality Control"


class StageStatus(models.TextChoices):
    RUNNING = "running", "Running"
    SUCCESS = "success", "Success"
    SKIPPED = "skipped", "Skipped"
    FAILED = "failed", "Failed"


class JobStageLog(TimeStampedModel):
    job = models.ForeignKey(ProcessingJob, on_delete=models.CASCADE, related_name="stage_logs")
    stage = models.CharField(max_length=32, choices=StageName.choices)
    status = models.CharField(max_length=16, choices=StageStatus.choices, default=StageStatus.RUNNING)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    detail = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.job_id}:{self.stage}:{self.status}"
