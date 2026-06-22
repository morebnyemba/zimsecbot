from django.contrib import admin

from .models import ConversationState


@admin.register(ConversationState)
class ConversationStateAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "user", "current_flow", "current_step", "updated_at")
    list_filter = ("current_flow",)
    search_fields = ("phone_number", "user__email")
