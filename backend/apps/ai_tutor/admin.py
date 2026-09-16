from django import forms
from django.contrib import admin

from .models import AIProvider, AISession, Message


class AIProviderForm(forms.ModelForm):
    api_key = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Leave blank to keep the existing key unchanged.",
    )

    class Meta:
        model = AIProvider
        fields = ["name", "provider_type", "model_name", "is_active", "api_key"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw_key = self.cleaned_data.get("api_key")
        if raw_key:
            instance.set_api_key(raw_key)
        if commit:
            instance.save()
        return instance


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    form = AIProviderForm
    list_display = ("name", "provider_type", "model_name", "is_active", "api_key_is_set")
    list_filter = ("provider_type", "is_active")
    readonly_fields = ("api_key_status",)
    fieldsets = (
        (None, {"fields": ("name", "provider_type", "model_name", "is_active")}),
        ("Credentials", {"fields": ("api_key_status", "api_key")}),
    )

    @admin.display(boolean=True, description="API key set")
    def api_key_is_set(self, obj):
        return bool(obj.api_key_encrypted)

    @admin.display(description="Current API key")
    def api_key_status(self, obj):
        return "●●●● set" if obj and obj.api_key_encrypted else "Not set"


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
