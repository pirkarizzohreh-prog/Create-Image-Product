from rest_framework import serializers

from .models import Batch, ProductImage


class BatchListSerializer(serializers.ModelSerializer):
    image_count = serializers.IntegerField(read_only=True)
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    status_counts = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = [
            "id", "name", "owner", "owner_email", "default_mode", "output_size_px",
            "padding_percent", "output_format", "prompt_template", "image_count",
            "status_counts", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def get_status_counts(self, obj):
        from apps.jobs.models import ProcessingJob

        qs = ProcessingJob.objects.filter(image__batch=obj).values_list("status", flat=True)
        counts = {}
        for status in qs:
            counts[status] = counts.get(status, 0) + 1
        return counts


class BatchCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ["id", "name", "default_mode", "output_size_px", "padding_percent", "output_format", "prompt_template"]
        read_only_fields = ["id"]


class ProductImageSerializer(serializers.ModelSerializer):
    source_url = serializers.SerializerMethodField()
    latest_job = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = [
            "id", "batch", "uploaded_by", "source_file", "source_url", "original_filename",
            "content_type", "size_bytes", "width", "height", "sku", "product_name", "category",
            "processing_mode", "effective_mode", "latest_job", "created_at",
        ]
        read_only_fields = ["id", "uploaded_by", "size_bytes", "width", "height", "created_at"]

    def get_source_url(self, obj):
        try:
            return obj.source_file.url
        except ValueError:
            return None

    def get_latest_job(self, obj):
        from apps.jobs.serializers import JobSummarySerializer

        job = obj.jobs.order_by("-created_at").first()
        return JobSummarySerializer(job).data if job else None
