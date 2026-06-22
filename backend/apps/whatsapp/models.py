from django.db import models

from apps.common.models import BaseModel


class WebhookEventLog(BaseModel):
    """Dedupes inbound Meta webhook events by message id (idempotency)."""

    message_id = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=20, blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["message_id"])]

    def __str__(self):
        return f"WebhookEventLog<{self.message_id}>"
