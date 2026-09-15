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
    list_display = ("name", "phone_number_id", "graph_api_version", "is_active")
    list_filter = ("is_active",)


@admin.register(WebhookEventLog)
class WebhookEventLogAdmin(admin.ModelAdmin):
    list_display = ("message_id", "phone_number", "processed_at", "created_at")
    search_fields = ("message_id", "phone_number")
