from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsContentAdmin(BasePermission):
    """Allows write access to content_admin/superadmin, read access to anyone authenticated."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role in (
            request.user.Role.CONTENT_ADMIN,
            request.user.Role.SUPERADMIN,
        )


class IsOwner(BasePermission):
    """Object-level permission: the object's `user` field must match the requester."""

    def has_object_permission(self, request, view, obj):
        return getattr(obj, "user_id", None) == request.user.id
