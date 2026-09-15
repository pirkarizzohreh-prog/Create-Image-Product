from django.urls import path

from .views import BatchDetailView, BatchDownloadView, BatchListCreateView, ImageDetailView, ImageUploadView

urlpatterns = [
    path("batches/", BatchListCreateView.as_view(), name="batch-list"),
    path("batches/<uuid:pk>/", BatchDetailView.as_view(), name="batch-detail"),
    path("batches/<uuid:pk>/download/", BatchDownloadView.as_view(), name="batch-download"),
    path("images/", ImageUploadView.as_view(), name="image-upload"),
    path("images/<uuid:pk>/", ImageDetailView.as_view(), name="image-detail"),
]
