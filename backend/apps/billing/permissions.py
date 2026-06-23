from rest_framework.permissions import BasePermission

from .services import AccessDenied, AccessGate


class HasFeatureAccess(BasePermission):
    """Gates a view behind `view.feature_key` using `AccessGate`.

    DRF's default exception handler returns `exc.detail` verbatim (no
    "detail" wrapper) when it's a dict, so setting `self.message` to
    `{"error": {...}}` here produces the uniform 403 envelope from
    docs/MONETIZATION.md section 4: `{"error": {"code": "feature_locked",
    "message": ..., "upgrade_url": ...}}`.
    """

    feature_key = None

    def has_permission(self, request, view):
        feature_key = getattr(view, "feature_key", self.feature_key)
        if not feature_key:
            return True
        try:
            AccessGate.check(request.user, feature_key)
        except AccessDenied as exc:
            self.message = {
                "error": {
                    "code": "feature_locked",
                    "message": exc.message,
                    "upgrade_url": exc.upgrade_url,
                }
            }
            return False
        return True
