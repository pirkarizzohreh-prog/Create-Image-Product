from rest_framework import serializers

from apps.jobs.serializers import JobDetailSerializer

from .models import ReviewItem


class ReviewItemSerializer(serializers.ModelSerializer):
    job_detail = JobDetailSerializer(source="job", read_only=True)
    reviewed_by_email = serializers.EmailField(source="reviewed_by.email", read_only=True)

    class Meta:
        model = ReviewItem
        fields = [
            "id", "job", "job_detail", "reasons", "decision", "decision_notes",
            "reviewed_by", "reviewed_by_email", "reviewed_at", "created_at",
        ]
        read_only_fields = ["id", "job", "reasons", "decision", "reviewed_by", "reviewed_at", "created_at"]


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(allow_blank=False)


class RerunSerializer(serializers.Serializer):
    output_size_px = serializers.IntegerField(required=False)
    padding_percent = serializers.FloatField(required=False)
    output_format = serializers.ChoiceField(choices=["WEBP", "PNG", "JPEG"], required=False)
    mode = serializers.ChoiceField(choices=["recreate_studio", "enhance_only"], required=False)


class ReplaceSerializer(serializers.Serializer):
    file = serializers.ImageField()
