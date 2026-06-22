from .models import AuditLog


def log_action(*, user, action, **metadata):
    AuditLog.objects.create(user=user, action=action, metadata=metadata)
