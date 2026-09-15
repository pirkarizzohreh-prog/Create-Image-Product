from rest_framework import serializers

from .models import PipelineSettings, PromptTemplate, StorageSettings


class PipelineSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineSettings
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PromptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptTemplate
        fields = ["id", "name", "category", "template_text", "is_default", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class StorageSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageSettings
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
