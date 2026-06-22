from django.contrib import admin

from .models import WebhookEventLog


@admin.register(WebhookEventLog)
class WebhookEventLogAdmin(admin.ModelAdmin):
    list_display = ("message_id", "phone_number", "processed_at", "created_at")
    search_fields = ("message_id", "phone_number")
