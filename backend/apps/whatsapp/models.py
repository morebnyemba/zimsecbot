from django.db import models

from apps.common.encryption import decrypt_value, encrypt_value
from apps.common.models import BaseModel


class WhatsAppProvider(BaseModel):
    """DB-backed WhatsApp Cloud API credentials, editable in Django admin.

    Mirrors ai_tutor.AIProvider: an active row here takes precedence over
    the WHATSAPP_* env vars (see apps.whatsapp.providers.get_active_credentials).
    """

    name = models.CharField(max_length=100)
    phone_number_id = models.CharField(max_length=64, blank=True, default="")
    access_token_encrypted = models.TextField(blank=True, default="")
    app_secret_encrypted = models.TextField(blank=True, default="")
    verify_token_encrypted = models.TextField(blank=True, default="")
    graph_api_version = models.CharField(max_length=10, default="v26.0")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def set_access_token(self, raw_token: str):
        self.access_token_encrypted = encrypt_value(raw_token)

    def get_access_token(self) -> str:
        return decrypt_value(self.access_token_encrypted) if self.access_token_encrypted else ""

    def set_app_secret(self, raw_secret: str):
        self.app_secret_encrypted = encrypt_value(raw_secret)

    def get_app_secret(self) -> str:
        return decrypt_value(self.app_secret_encrypted) if self.app_secret_encrypted else ""

    def set_verify_token(self, raw_token: str):
        self.verify_token_encrypted = encrypt_value(raw_token)

    def get_verify_token(self) -> str:
        return decrypt_value(self.verify_token_encrypted) if self.verify_token_encrypted else ""


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
