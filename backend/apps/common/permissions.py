from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsReviewerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ("reviewer", "admin"))


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class IsOwnerOrReviewerReadOnly(BasePermission):
    """Owners have full access to their own objects; reviewers/admins get read
    access to everyone's, write access is handled by the more specific review
    endpoints rather than generic object mutation."""

    def has_object_permission(self, request, view, obj):
        owner_id = getattr(obj, "owner_id", None) or getattr(getattr(obj, "batch", None), "owner_id", None)
        if owner_id == request.user.id:
            return True
        if request.user.role in ("reviewer", "admin"):
            return request.method in SAFE_METHODS or getattr(view, "allow_privileged_write", False)
        return False
