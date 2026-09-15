from django.contrib import admin

from .models import ReviewItem


@admin.register(ReviewItem)
class ReviewItemAdmin(admin.ModelAdmin):
    list_display = ["id", "job", "decision", "reviewed_by", "reviewed_at", "created_at"]
    list_filter = ["decision"]
