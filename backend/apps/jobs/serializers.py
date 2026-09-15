from rest_framework import serializers

from .models import JobStageLog, ProcessingJob


class JobStageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobStageLog
        fields = ["id", "stage", "status", "started_at", "finished_at", "duration_ms", "detail", "error_message"]


class JobSummarySerializer(serializers.ModelSerializer):
    output_url = serializers.SerializerMethodField()

    class Meta:
        model = ProcessingJob
        fields = ["id", "status", "mode", "qc_passed", "output_url", "created_at", "finished_at"]

    def get_output_url(self, obj):
        return obj.output_url


class JobDetailSerializer(serializers.ModelSerializer):
    stage_logs = JobStageLogSerializer(many=True, read_only=True)
    output_url = serializers.SerializerMethodField()
    source_url = serializers.SerializerMethodField()
    image_original_filename = serializers.CharField(source="image.original_filename", read_only=True)
    batch_id = serializers.UUIDField(source="image.batch_id", read_only=True)

    class Meta:
        model = ProcessingJob
        fields = [
            "id", "image", "image_original_filename", "batch_id", "status", "mode", "params",
            "output_file", "output_url", "output_width", "output_height", "output_checksum",
            "qc_passed", "qc_report", "error_message", "started_at", "finished_at", "attempt",
            "stage_logs", "source_url", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_output_url(self, obj):
        return obj.output_url

    def get_source_url(self, obj):
        try:
            return obj.image.source_file.url
        except ValueError:
            return None
