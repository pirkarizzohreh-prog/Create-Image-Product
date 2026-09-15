from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsReviewerOrAdmin
from apps.jobs.models import JobStatus

from .models import ReviewDecision, ReviewItem
from .notifications import notify_uploader
from .serializers import RejectSerializer, ReplaceSerializer, RerunSerializer, ReviewItemSerializer


class ReviewItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReviewItemSerializer
    permission_classes = [IsReviewerOrAdmin]

    def get_queryset(self):
        qs = ReviewItem.objects.select_related("job", "job__image").all()
        decision = self.request.query_params.get("decision", ReviewDecision.PENDING)
        if decision and decision != "all":
            qs = qs.filter(decision=decision)
        return qs

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        item = self.get_object()
        job = item.job
        job.status = JobStatus.COMPLETED
        job.qc_passed = True
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "qc_passed", "finished_at", "updated_at"])

        item.decision = ReviewDecision.APPROVED
        item.reviewed_by = request.user
        item.reviewed_at = timezone.now()
        item.decision_notes = request.data.get("notes", "")
        item.save()

        notify_uploader(job, "Your image was approved", f"Job {job.id} passed manual review and is ready to download.")
        return Response(ReviewItemSerializer(item).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        item = self.get_object()
        serializer = RejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = item.job
        job.status = JobStatus.REJECTED
        job.qc_passed = False
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "qc_passed", "finished_at", "updated_at"])

        item.decision = ReviewDecision.REJECTED
        item.decision_notes = serializer.validated_data["reason"]
        item.reviewed_by = request.user
        item.reviewed_at = timezone.now()
        item.save()

        notify_uploader(job, "Your image was rejected", f"Job {job.id} was rejected: {item.decision_notes}")
        return Response(ReviewItemSerializer(item).data)

    @action(detail=True, methods=["post"])
    def rerun(self, request, pk=None):
        item = self.get_object()
        serializer = RerunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        overrides = dict(serializer.validated_data)
        mode_override = overrides.pop("mode", None)

        from apps.jobs.services import create_and_enqueue_job

        image = item.job.image
        if mode_override:
            image.processing_mode = mode_override
            image.save(update_fields=["processing_mode"])

        new_job = create_and_enqueue_job(image, attempt=item.job.attempt + 1, extra_params=overrides or None)

        item.decision = ReviewDecision.RERUN
        item.reviewed_by = request.user
        item.reviewed_at = timezone.now()
        item.decision_notes = f"Re-run requested; new job {new_job.id} queued."
        item.save()

        return Response(ReviewItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def replace(self, request, pk=None):
        item = self.get_object()
        serializer = ReplaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = item.job
        job.output_file = serializer.validated_data["file"]
        job.status = JobStatus.COMPLETED
        job.qc_passed = True
        job.finished_at = timezone.now()
        job.save()

        item.decision = ReviewDecision.REPLACED
        item.reviewed_by = request.user
        item.reviewed_at = timezone.now()
        item.decision_notes = request.data.get("notes", "Manually replaced by reviewer.")
        item.save()

        notify_uploader(job, "Your image was updated", f"Job {job.id} output was manually replaced by a reviewer.")
        return Response(ReviewItemSerializer(item).data)
