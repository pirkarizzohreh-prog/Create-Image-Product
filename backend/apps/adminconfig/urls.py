from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PipelineSettingsView, PromptTemplateViewSet, StorageSettingsView

router = DefaultRouter()
router.register("prompt-templates", PromptTemplateViewSet, basename="prompt-template")

urlpatterns = [
    path("pipeline-settings/", PipelineSettingsView.as_view(), name="pipeline-settings"),
    path("storage-settings/", StorageSettingsView.as_view(), name="storage-settings"),
] + router.urls
