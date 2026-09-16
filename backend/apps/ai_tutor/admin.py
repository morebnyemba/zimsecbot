from django.contrib import admin

from .models import AIProvider, AISession, Message


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "provider_type", "model_name", "is_active")
    list_filter = ("provider_type", "is_active")
    search_fields = ("name",)
    fieldsets = (
        (None, {"fields": ("name", "provider_type", "model_name", "is_active")}),
        ("Credentials", {"fields": ("api_key",)}),
    )


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ("role", "content", "created_at")
    readonly_fields = ("role", "content", "created_at")


@admin.register(AISession)
class AISessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "phone_number", "channel", "created_at")
    list_filter = ("channel",)
    inlines = [MessageInline]
