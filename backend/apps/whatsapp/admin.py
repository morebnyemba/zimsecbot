from django.contrib import admin

from .models import WebhookEventLog, WhatsAppProvider


@admin.register(WhatsAppProvider)
class WhatsAppProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "waba_id", "phone_number_id", "graph_api_version", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "waba_id", "phone_number_id")
    fieldsets = (
        (None, {"fields": ("name", "is_active")}),
        (
            "WhatsApp",
            {"fields": ("waba_id", "phone_number_id", "graph_api_version")},
        ),
        (
            "Credentials",
            {"fields": ("access_token", "app_secret", "verify_token")},
        ),
    )


@admin.register(WebhookEventLog)
class WebhookEventLogAdmin(admin.ModelAdmin):
    list_display = ("message_id", "phone_number", "processed_at", "created_at")
    search_fields = ("message_id", "phone_number")
