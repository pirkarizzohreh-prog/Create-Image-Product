from django.urls import path

from .views import JobDetailView, JobListView, JobRetryView

urlpatterns = [
    path("jobs/", JobListView.as_view(), name="job-list"),
    path("jobs/<uuid:pk>/", JobDetailView.as_view(), name="job-detail"),
    path("jobs/<uuid:pk>/retry/", JobRetryView.as_view(), name="job-retry"),
]
