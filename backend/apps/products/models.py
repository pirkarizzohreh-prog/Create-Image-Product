from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


def source_upload_path(instance, filename):
    return f"{settings.MEDIA_STORAGE_PREFIX}/sources/{instance.batch_id}/{instance.id}_{filename}"


class ProcessingMode(models.TextChoices):
    RECREATE_STUDIO = "recreate_studio", "Recreate Studio Mode"
    ENHANCE_ONLY = "enhance_only", "Enhance Only Mode"


class Batch(TimeStampedModel):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="batches")
    default_mode = models.CharField(max_length=32, choices=ProcessingMode.choices, default=ProcessingMode.ENHANCE_ONLY)

    # Per-batch overrides of admin defaults; null = use active PipelineSettings.
    output_size_px = models.PositiveIntegerField(null=True, blank=True)
    padding_percent = models.FloatField(null=True, blank=True)
    output_format = models.CharField(max_length=10, null=True, blank=True)
    prompt_template = models.ForeignKey(
        "adminconfig.PromptTemplate", null=True, blank=True, on_delete=models.SET_NULL, related_name="batches"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def image_count(self):
        return self.images.count()


class ProductImage(TimeStampedModel):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="images")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="uploaded_images")

    source_file = models.FileField(upload_to=source_upload_path)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True)
    size_bytes = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)

    # Free-text product metadata (no strict catalog integration in v1).
    sku = models.CharField(max_length=100, blank=True)
    product_name = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=100, blank=True)

    # Overrides the batch default_mode for this single image, if set.
    processing_mode = models.CharField(max_length=32, choices=ProcessingMode.choices, null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.original_filename

    @property
    def effective_mode(self):
        return self.processing_mode or self.batch.default_mode
