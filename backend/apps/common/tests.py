import re

import pytest
from django.conf import settings
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


@override_settings(ALLOWED_HOSTS=["testserver"])
def test_admin_login_renders_with_unfold_theme():
    response = APIClient().get("/admin/login/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Zimfundi" in content
    assert "unfold" in content.lower()


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


@pytest.mark.parametrize("compose_file", ["docker-compose.yml", "docker-compose.prod.yml"])
def test_celery_worker_consumes_every_routed_queue(compose_file):
    """CELERY_TASK_ROUTES sends tasks to named queues (whatsapp/ai/etc.);
    without a matching `-Q` on the worker's command, Celery only consumes
    the "celery" default -- those tasks enqueue successfully and then sit
    unconsumed in Redis forever, with no error anywhere. This caught a real
    production incident (WhatsApp never marking messages read/replying)
    that was invisible everywhere except "the task never seems to run".
    """
    compose_path = settings.BASE_DIR.parent / compose_file
    compose_text = compose_path.read_text()

    worker_block_match = re.search(
        r"celery_worker:.*?(?=\n  \w[\w_]*:|\Z)", compose_text, re.DOTALL
    )
    assert worker_block_match, f"no celery_worker service found in {compose_file}"
    worker_block = worker_block_match.group(0)

    command_match = re.search(r"command:\s*(.+)", worker_block)
    assert command_match, f"celery_worker has no command in {compose_file}"
    command = command_match.group(1)

    routed_queues = {route["queue"] for route in settings.CELERY_TASK_ROUTES.values()}
    for queue in routed_queues:
        assert re.search(rf"-Q[= ][\w,]*\b{queue}\b", command), (
            f"queue '{queue}' is routed to in CELERY_TASK_ROUTES but the "
            f"celery_worker command in {compose_file} doesn't consume it: {command!r}"
        )
