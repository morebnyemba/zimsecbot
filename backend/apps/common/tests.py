import pytest
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APIClient

from apps.ai_tutor.models import AIProvider
from apps.whatsapp.models import WhatsAppProvider


@pytest.mark.django_db
def test_health_check_returns_ok():
    response = APIClient().get("/health/")

    assert response.status_code == 200
    assert response.data == {"status": "ok", "checks": {"database": True, "cache": True}}


@pytest.mark.django_db
@override_settings(
    GEMINI_API_KEY="env-gemini-key",
    WHATSAPP_ACCESS_TOKEN="env-token",
    WHATSAPP_PHONE_NUMBER_ID="env-phone-id",
    WHATSAPP_APP_SECRET="env-secret",
    WHATSAPP_VERIFY_TOKEN="env-verify",
    WHATSAPP_GRAPH_API_VERSION="v20.0",
    WHATSAPP_WABA_ID="env-waba-id",
)
def test_seed_providers_from_env_creates_provider_rows():
    call_command("seed_providers_from_env")

    ai_provider = AIProvider.objects.get(name="Default")
    assert ai_provider.api_key == "env-gemini-key"
    assert ai_provider.is_active is True

    whatsapp_provider = WhatsAppProvider.objects.get(name="Default")
    assert whatsapp_provider.access_token == "env-token"
    assert whatsapp_provider.phone_number_id == "env-phone-id"
    assert whatsapp_provider.app_secret == "env-secret"
    assert whatsapp_provider.verify_token == "env-verify"
    assert whatsapp_provider.graph_api_version == "v20.0"
    assert whatsapp_provider.waba_id == "env-waba-id"
    assert whatsapp_provider.is_active is True


@pytest.mark.django_db
@override_settings(GEMINI_API_KEY="updated-key", WHATSAPP_ACCESS_TOKEN="updated-token")
def test_seed_providers_from_env_updates_existing_rows_without_duplicating():
    AIProvider.objects.create(name="Default", provider_type=AIProvider.ProviderType.GEMINI)
    WhatsAppProvider.objects.create(name="Default")

    call_command("seed_providers_from_env")

    assert AIProvider.objects.filter(name="Default").count() == 1
    assert WhatsAppProvider.objects.filter(name="Default").count() == 1
    assert AIProvider.objects.get(name="Default").api_key == "updated-key"
    assert WhatsAppProvider.objects.get(name="Default").access_token == "updated-token"


@pytest.mark.django_db
@override_settings(GEMINI_API_KEY="", WHATSAPP_ACCESS_TOKEN="", WHATSAPP_PHONE_NUMBER_ID="",
                    WHATSAPP_APP_SECRET="", WHATSAPP_VERIFY_TOKEN="")
def test_seed_providers_from_env_skips_when_no_env_vars_set():
    call_command("seed_providers_from_env")

    assert not AIProvider.objects.exists()
    assert not WhatsAppProvider.objects.exists()
