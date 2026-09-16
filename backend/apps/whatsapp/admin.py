from django import forms
from django.contrib import admin

from .models import WebhookEventLog, WhatsAppProvider


class WhatsAppProviderForm(forms.ModelForm):
    access_token = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Leave blank to keep the existing access token unchanged.",
    )
    app_secret = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Leave blank to keep the existing app secret unchanged.",
    )
    verify_token = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Leave blank to keep the existing verify token unchanged.",
    )

    class Meta:
        model = WhatsAppProvider
        fields = [
            "name",
            "phone_number_id",
            "graph_api_version",
            "is_active",
            "access_token",
            "app_secret",
            "verify_token",
        ]

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get("access_token"):
            instance.set_access_token(self.cleaned_data["access_token"])
        if self.cleaned_data.get("app_secret"):
            instance.set_app_secret(self.cleaned_data["app_secret"])
        if self.cleaned_data.get("verify_token"):
            instance.set_verify_token(self.cleaned_data["verify_token"])
        if commit:
            instance.save()
        return instance


@admin.register(WhatsAppProvider)
class WhatsAppProviderAdmin(admin.ModelAdmin):
    form = WhatsAppProviderForm
    list_display = (
        "name",
        "phone_number_id",
        "graph_api_version",
        "is_active",
        "access_token_is_set",
        "app_secret_is_set",
        "verify_token_is_set",
    )
    list_filter = ("is_active",)
    readonly_fields = ("access_token_status", "app_secret_status", "verify_token_status")
    fieldsets = (
        (None, {"fields": ("name", "phone_number_id", "graph_api_version", "is_active")}),
        (
            "Credentials",
            {
                "fields": (
                    "access_token_status",
                    "access_token",
                    "app_secret_status",
                    "app_secret",
                    "verify_token_status",
                    "verify_token",
                )
            },
        ),
    )

    @admin.display(boolean=True, description="Access token set")
    def access_token_is_set(self, obj):
        return bool(obj.access_token_encrypted)

    @admin.display(boolean=True, description="App secret set")
    def app_secret_is_set(self, obj):
        return bool(obj.app_secret_encrypted)

    @admin.display(boolean=True, description="Verify token set")
    def verify_token_is_set(self, obj):
        return bool(obj.verify_token_encrypted)

    @admin.display(description="Current access token")
    def access_token_status(self, obj):
        return "●●●● set" if obj and obj.access_token_encrypted else "Not set"

    @admin.display(description="Current app secret")
    def app_secret_status(self, obj):
        return "●●●● set" if obj and obj.app_secret_encrypted else "Not set"

    @admin.display(description="Current verify token")
    def verify_token_status(self, obj):
        return "●●●● set" if obj and obj.verify_token_encrypted else "Not set"


@admin.register(WebhookEventLog)
class WebhookEventLogAdmin(admin.ModelAdmin):
    list_display = ("message_id", "phone_number", "processed_at", "created_at")
    search_fields = ("message_id", "phone_number")
