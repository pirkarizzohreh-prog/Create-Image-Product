from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class ReviewDecision(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    REPLACED = "replaced", "Replaced"
    RERUN = "rerun", "Re-run Requested"


class ReviewItem(TimeStampedModel):
    job = models.ForeignKey("jobs.ProcessingJob", on_delete=models.CASCADE, related_name="review_items")
    reasons = models.JSONField(default=list, blank=True, help_text="QC failure reasons / stage error summaries.")
    decision = models.CharField(max_length=20, choices=ReviewDecision.choices, default=ReviewDecision.PENDING)
    decision_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="review_decisions"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["decision"])]

    def __str__(self):
        return f"ReviewItem({self.job_id}) {self.decision}"
