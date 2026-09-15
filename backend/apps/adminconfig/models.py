from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class PipelineSettings(TimeStampedModel):
    """Admin-editable defaults applied to new batches/jobs. Only one row is
    ever 'active'; enforced in save()."""

    is_active = models.BooleanField(default=True)

    output_size_px = models.PositiveIntegerField(default=2000)
    padding_percent = models.FloatField(default=8.0)
    output_format = models.CharField(
        max_length=10,
        choices=[("WEBP", "WebP"), ("PNG", "PNG"), ("JPEG", "JPEG")],
        default="WEBP",
    )
    output_quality = models.PositiveIntegerField(default=90)

    # QC thresholds
    qc_background_whiteness_tolerance = models.FloatField(default=6.0, help_text="Max allowed mean deviation from #FFFFFF in corner samples (0-255 scale).")
    qc_centering_tolerance_percent = models.FloatField(default=2.5, help_text="Max allowed asymmetry between opposite padding edges, as % of canvas size.")
    qc_min_product_coverage_percent = models.FloatField(default=15.0)
    qc_max_product_coverage_percent = models.FloatField(default=95.0)
    qc_identity_similarity_threshold = models.FloatField(default=0.80, help_text="Min similarity score (0-1) between source and AI-recreated product region.")

    class Meta:
        verbose_name = "Pipeline Settings"
        verbose_name_plural = "Pipeline Settings"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            PipelineSettings.objects.exclude(pk=self.pk).update(is_active=False)

    @classmethod
    def get_active(cls):
        obj = cls.objects.filter(is_active=True).first()
        if obj:
            return obj
        return cls.objects.create(
            output_size_px=settings.DEFAULT_OUTPUT_SIZE_PX,
            padding_percent=settings.DEFAULT_PADDING_PERCENT,
            output_format=settings.DEFAULT_OUTPUT_FORMAT,
        )

    def __str__(self):
        return f"PipelineSettings({self.output_size_px}px, pad={self.padding_percent}%, {self.output_format})"


class PromptTemplate(TimeStampedModel):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, help_text="Optional product category scope, e.g. 'footwear'.")
    template_text = models.TextField(
        default=(
            "A professional studio product photograph of the exact same item shown in the "
            "reference image, front-facing, centered, on a seamless pure white background, "
            "soft even studio lighting, no shadows other than a subtle contact shadow, sharp "
            "focus, high detail. Preserve the product's exact shape, proportions, color, "
            "material, texture, logos, and any printed text with complete accuracy. Do not "
            "invent, add, remove, or alter any product features."
        )
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "name"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            PromptTemplate.objects.exclude(pk=self.pk).filter(category=self.category).update(is_default=False)

    def __str__(self):
        return self.name

    @classmethod
    def get_default(cls, category=""):
        return (
            cls.objects.filter(category=category, is_default=True).first()
            or cls.objects.filter(is_default=True).first()
        )


class StorageSettings(TimeStampedModel):
    is_active = models.BooleanField(default=True)
    provider = models.CharField(
        max_length=20,
        choices=[("s3", "AWS S3"), ("r2", "Cloudflare R2"), ("local", "Local filesystem (dev only)")],
        default="s3",
    )
    bucket_name = models.CharField(max_length=255, default="pixelforge-media")
    region = models.CharField(max_length=100, default="auto")
    endpoint_url = models.URLField(blank=True, help_text="Required for R2 / non-AWS S3-compatible endpoints.")
    path_prefix = models.CharField(max_length=100, default="pixelforge")
    signed_url_ttl_seconds = models.PositiveIntegerField(default=3600)

    class Meta:
        verbose_name = "Storage Settings"
        verbose_name_plural = "Storage Settings"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            StorageSettings.objects.exclude(pk=self.pk).update(is_active=False)

    @classmethod
    def get_active(cls):
        obj = cls.objects.filter(is_active=True).first()
        if obj:
            return obj
        return cls.objects.create(
            bucket_name=settings.AWS_STORAGE_BUCKET_NAME,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL or "",
            path_prefix=settings.MEDIA_STORAGE_PREFIX,
            signed_url_ttl_seconds=settings.AWS_QUERYSTRING_EXPIRE,
        )

    def __str__(self):
        return f"StorageSettings({self.provider}:{self.bucket_name})"
