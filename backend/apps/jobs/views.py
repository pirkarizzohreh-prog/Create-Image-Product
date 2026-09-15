import django_filters
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import JobStatus, ProcessingJob
from .serializers import JobDetailSerializer, JobSummarySerializer


class JobFilter(django_filters.FilterSet):
    # Exposed as `batch` (not `image__batch`) to match the query param used
    # by every other endpoint that filters on a batch (images, download).
    batch = django_filters.UUIDFilter(field_name="image__batch")

    class Meta:
        model = ProcessingJob
        fields = ["status", "mode", "batch"]


class JobListView(generics.ListAPIView):
    serializer_class = JobSummarySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = JobFilter

    def get_queryset(self):
        user = self.request.user
        qs = ProcessingJob.objects.select_related("image", "image__batch").all()
        if user.role == "uploader" or self.request.query_params.get("mine") == "true":
            qs = qs.filter(image__uploaded_by=user)
        return qs


class JobDetailView(generics.RetrieveAPIView):
    serializer_class = JobDetailSerializer
    queryset = ProcessingJob.objects.select_related("image", "image__batch").prefetch_related("stage_logs")
    permission_classes = [permissions.IsAuthenticated]


class JobRetryView(APIView):
    def post(self, request, pk):
        job = get_object_or_404(ProcessingJob, pk=pk)
        if job.status not in (JobStatus.FAILED, JobStatus.REJECTED, JobStatus.NEEDS_REVIEW):
            return Response({"detail": "Only failed/rejected/needs_review jobs can be retried."}, status=status.HTTP_400_BAD_REQUEST)

        from apps.jobs.services import create_and_enqueue_job

        new_job = create_and_enqueue_job(job.image, attempt=job.attempt + 1)
        return Response(JobDetailSerializer(new_job, context={"request": request}).data, status=status.HTTP_201_CREATED)
