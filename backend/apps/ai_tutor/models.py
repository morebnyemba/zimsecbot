from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class AIProvider(BaseModel):
    class ProviderType(models.TextChoices):
        GEMINI = "gemini", "Google Gemini"

    name = models.CharField(max_length=100)
    provider_type = models.CharField(
        max_length=20, choices=ProviderType.choices, default=ProviderType.GEMINI
    )
    model_name = models.CharField(max_length=100, default="gemini-3.6-flash")
    api_key = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Mirrors bubi-rural's MetaAppConfig.save() / WhatsAppProvider.save():
        # get_active_provider() takes .filter(is_active=True, provider_type=...)
        # .first(), so two active rows of the same provider_type would make
        # "which one wins" arbitrary and silent. Scoped by provider_type so
        # future non-Gemini provider types (if any) don't fight over the
        # single active slot with each other.
        if self.is_active:
            AIProvider.objects.filter(
                is_active=True, provider_type=self.provider_type
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class AISession(BaseModel):
    class Channel(models.TextChoices):
        WEB = "web", "Web"
        WHATSAPP = "whatsapp", "WhatsApp"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ai_sessions",
    )
    phone_number = models.CharField(max_length=20, blank=True, default="")
    channel = models.CharField(max_length=20, choices=Channel.choices)

    class Meta:
        indexes = [models.Index(fields=["user"]), models.Index(fields=["phone_number"])]

    def __str__(self):
        identifier = self.user_id or self.phone_number
        return f"AISession<{identifier}> ({self.channel})"


class Message(BaseModel):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    session = models.ForeignKey(AISession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"
