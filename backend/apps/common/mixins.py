from apps.audit.services import log_action


class AuditLoggedViewSetMixin:
    """Logs create/update/delete actions performed through a ModelViewSet to AuditLog."""

    def perform_create(self, serializer):
        super().perform_create(serializer)
        log_action(
            user=self.request.user,
            action=f"{self.queryset.model.__name__.lower()}.create",
            object_id=str(serializer.instance.pk),
        )

    def perform_update(self, serializer):
        super().perform_update(serializer)
        log_action(
            user=self.request.user,
            action=f"{self.queryset.model.__name__.lower()}.update",
            object_id=str(serializer.instance.pk),
        )

    def perform_destroy(self, instance):
        object_id = str(instance.pk)
        super().perform_destroy(instance)
        log_action(
            user=self.request.user,
            action=f"{instance.__class__.__name__.lower()}.delete",
            object_id=object_id,
        )
