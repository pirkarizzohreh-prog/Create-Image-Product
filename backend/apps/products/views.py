import io
import zipfile

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsOwnerOrReviewerReadOnly

from .models import Batch, ProductImage
from .serializers import BatchCreateSerializer, BatchListSerializer, ProductImageSerializer


class IsUploaderAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class BatchListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsUploaderAuthenticated]

    def get_serializer_class(self):
        return BatchCreateSerializer if self.request.method == "POST" else BatchListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Batch.objects.select_related("owner").all()
        if user.role == "uploader":
            qs = qs.filter(owner=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class BatchDetailView(generics.RetrieveAPIView):
    serializer_class = BatchListSerializer
    permission_classes = [IsUploaderAuthenticated, IsOwnerOrReviewerReadOnly]
    queryset = Batch.objects.all()


class ImageUploadView(APIView):
    """Accepts multipart POST with a `batch` id and one or more `files`,
    supporting single or bulk upload from the same endpoint."""

    def post(self, request):
        batch_id = request.data.get("batch")
        batch = get_object_or_404(Batch, id=batch_id)
        if batch.owner_id != request.user.id and request.user.role == "uploader":
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        files = request.FILES.getlist("files") or request.FILES.getlist("file")
        if not files:
            return Response({"detail": "No files provided."}, status=status.HTTP_400_BAD_REQUEST)

        processing_mode = request.data.get("processing_mode") or None
        created = []
        for f in files:
            image = ProductImage.objects.create(
                batch=batch,
                uploaded_by=request.user,
                source_file=f,
                original_filename=f.name,
                content_type=getattr(f, "content_type", "") or "",
                size_bytes=f.size,
                processing_mode=processing_mode,
            )
            try:
                from PIL import Image as PILImage

                f.seek(0)
                with PILImage.open(f) as im:
                    image.width, image.height = im.size
                    image.save(update_fields=["width", "height"])
            except Exception:
                pass

            from apps.jobs.services import create_and_enqueue_job

            job = create_and_enqueue_job(image)
            created.append((image, job))

        data = [
            {**ProductImageSerializer(img, context={"request": request}).data, "job_id": str(job.id)}
            for img, job in created
        ]
        return Response(data, status=status.HTTP_201_CREATED)


class ImageDetailView(generics.RetrieveAPIView):
    serializer_class = ProductImageSerializer
    queryset = ProductImage.objects.all()
    permission_classes = [IsUploaderAuthenticated]


class BatchDownloadView(APIView):
    """Builds (or reuses) a ZIP of all completed output images for a batch and
    returns a downloadable/signed URL to it."""

    def post(self, request, pk):
        from apps.jobs.models import JobStatus, ProcessingJob

        batch = get_object_or_404(Batch, id=pk)
        jobs = ProcessingJob.objects.filter(image__batch=batch, status=JobStatus.COMPLETED).select_related("image")
        if not jobs.exists():
            return Response({"detail": "No completed outputs to download yet."}, status=status.HTTP_400_BAD_REQUEST)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for job in jobs:
                if not job.output_file:
                    continue
                name = job.image.sku or job.image.original_filename.rsplit(".", 1)[0]
                ext = job.output_file.name.rsplit(".", 1)[-1]
                with job.output_file.open("rb") as fh:
                    zf.writestr(f"{name}_{str(job.id)[:8]}.{ext}", fh.read())
        buffer.seek(0)

        from django.conf import settings as dj_settings

        zip_path = f"{dj_settings.MEDIA_STORAGE_PREFIX}/zips/{batch.id}.zip"
        if default_storage.exists(zip_path):
            default_storage.delete(zip_path)
        saved_path = default_storage.save(zip_path, ContentFile(buffer.read()))
        url = default_storage.url(saved_path)
        return Response({"url": url})
