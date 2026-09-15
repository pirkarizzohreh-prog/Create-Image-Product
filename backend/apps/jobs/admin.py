from django.contrib import admin

from .models import JobStageLog, ProcessingJob


class JobStageLogInline(admin.TabularInline):
    model = JobStageLog
    extra = 0
    readonly_fields = ["stage", "status", "started_at", "finished_at", "duration_ms", "error_message"]


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = ["id", "image", "status", "mode", "qc_passed", "created_at"]
    list_filter = ["status", "mode", "qc_passed"]
    inlines = [JobStageLogInline]
