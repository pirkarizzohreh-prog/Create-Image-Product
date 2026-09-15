from django.urls import path

from .views import UserListView, UserUpdateView

urlpatterns = [
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<uuid:pk>/", UserUpdateView.as_view(), name="user-update"),
]
