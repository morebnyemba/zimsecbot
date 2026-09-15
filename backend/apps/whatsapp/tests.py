import hashlib
import hmac
import json
import threading
from unittest.mock import patch

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from .client import WhatsAppClient
from .models import WebhookEventLog, WhatsAppProvider
from .providers import get_active_credentials
from .tasks import process_inbound_event

SECRET = "test-app-secret"


def _signed_request(api_client, body: dict, secret: str = SECRET):
    raw = json.dumps(body).encode()
    signature = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return api_client.post(
        "/api/v1/whatsapp/webhook/",
        data=raw,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256=f"sha256={signature}",
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@override_settings(WHATSAPP_APP_SECRET=SECRET)
@patch("apps.whatsapp.views.process_inbound_event.delay")
def test_webhook_accepts_valid_signature(mock_delay, api_client):
    response = _signed_request(api_client, {"entry": []})
    assert response.status_code == 200
    mock_delay.assert_called_once()


@pytest.mark.django_db
@override_settings(WHATSAPP_APP_SECRET=SECRET)
@patch("apps.whatsapp.views.process_inbound_event.delay")
def test_webhook_rejects_invalid_signature(mock_delay, api_client):
    response = api_client.post(
        "/api/v1/whatsapp/webhook/",
        data=json.dumps({"entry": []}),
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256="sha256=deadbeef",
    )
    assert response.status_code == 403
    mock_delay.assert_not_called()


@pytest.mark.django_db
@override_settings(WHATSAPP_APP_SECRET="")
@patch("apps.whatsapp.views.process_inbound_event.delay")
def test_webhook_never_bypasses_verification_when_secret_unset(mock_delay, api_client):
    response = _signed_request(api_client, {"entry": []}, secret="anything")
    assert response.status_code == 403
    mock_delay.assert_not_called()


@pytest.mark.django_db
@override_settings(WHATSAPP_VERIFY_TOKEN="verify-me")
def test_webhook_verification_challenge(api_client):
    response = api_client.get(
        "/api/v1/whatsapp/webhook/",
        {"hub.mode": "subscribe", "hub.verify_token": "verify-me", "hub.challenge": "12345"},
    )
    assert response.status_code == 200
    assert response.content == b"12345"


@pytest.mark.django_db
@override_settings(WHATSAPP_VERIFY_TOKEN="verify-me")
def test_webhook_verification_challenge_rejects_wrong_token(api_client):
    response = api_client.get(
        "/api/v1/whatsapp/webhook/",
        {"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "12345"},
    )
    assert response.status_code == 403


@pytest.mark.django_db
@patch("apps.whatsapp.tasks.WhatsAppClient")
def test_duplicate_message_id_processed_once(mock_client_cls):
    message = {
        "id": "wamid.123",
        "from": "263771234567",
        "type": "text",
        "text": {"body": "menu"},
    }
    payload = {"entry": [{"changes": [{"value": {"messages": [message]}}]}]}

    process_inbound_event(payload)
    process_inbound_event(payload)

    assert WebhookEventLog.objects.filter(message_id="wamid.123").count() == 1
    assert mock_client_cls.return_value.mark_as_read.call_count == 1


@pytest.mark.django_db(transaction=True)
@patch("apps.whatsapp.tasks.WhatsAppClient")
def test_concurrent_duplicate_deliveries_processed_once(mock_client_cls):
    # WhatsApp Cloud API is known to redeliver the same webhook concurrently
    # on retry, not just sequentially — that's the race the plain
    # get_or_create() + later save() in _process_message() didn't close.
    # transaction=True (a real TransactionTestCase, not the default rolled-
    # back TestCase) is required so the two threads below see each other's
    # committed rows instead of each running inside its own isolated,
    # never-visible-to-the-other test transaction.
    message = {
        "id": "wamid.concurrent",
        "from": "263771234568",
        "type": "text",
        "text": {"body": "menu"},
    }
    payload = {"entry": [{"changes": [{"value": {"messages": [message]}}]}]}

    barrier = threading.Barrier(2)

    def run():
        barrier.wait()
        process_inbound_event(payload)

    threads = [threading.Thread(target=run) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert WebhookEventLog.objects.filter(message_id="wamid.concurrent").count() == 1
    assert mock_client_cls.return_value.mark_as_read.call_count == 1


@pytest.mark.django_db
def test_whatsapp_provider_set_and_get_secrets_round_trip():
    provider = WhatsAppProvider(name="Meta Cloud API", phone_number_id="123456")
    provider.set_access_token("token-abc")
    provider.set_app_secret("secret-abc")
    provider.set_verify_token("verify-abc")
    provider.save()

    provider.refresh_from_db()
    assert provider.access_token_encrypted != "token-abc"
    assert provider.get_access_token() == "token-abc"
    assert provider.get_app_secret() == "secret-abc"
    assert provider.get_verify_token() == "verify-abc"


@pytest.mark.django_db
def test_whatsapp_provider_get_secrets_blank_when_unset():
    provider = WhatsAppProvider.objects.create(name="Empty")

    assert provider.get_access_token() == ""
    assert provider.get_app_secret() == ""
    assert provider.get_verify_token() == ""


@pytest.mark.django_db
@override_settings(
    WHATSAPP_ACCESS_TOKEN="env-token",
    WHATSAPP_PHONE_NUMBER_ID="env-phone-id",
    WHATSAPP_APP_SECRET="env-secret",
    WHATSAPP_VERIFY_TOKEN="env-verify",
    WHATSAPP_GRAPH_API_VERSION="v20.0",
)
def test_get_active_credentials_falls_back_to_settings_when_no_active_provider():
    credentials = get_active_credentials()

    assert credentials.access_token == "env-token"
    assert credentials.phone_number_id == "env-phone-id"
    assert credentials.app_secret == "env-secret"
    assert credentials.verify_token == "env-verify"
    assert credentials.graph_api_version == "v20.0"


@pytest.mark.django_db
@override_settings(WHATSAPP_ACCESS_TOKEN="env-token")
def test_get_active_credentials_prefers_active_db_provider_over_settings():
    provider = WhatsAppProvider(
        name="Prod", phone_number_id="db-phone-id", graph_api_version="v26.0"
    )
    provider.set_access_token("db-token")
    provider.set_app_secret("db-secret")
    provider.set_verify_token("db-verify")
    provider.save()

    credentials = get_active_credentials()

    assert credentials.access_token == "db-token"
    assert credentials.phone_number_id == "db-phone-id"
    assert credentials.graph_api_version == "v26.0"


@pytest.mark.django_db
def test_get_active_credentials_ignores_inactive_db_provider():
    provider = WhatsAppProvider(name="Disabled", is_active=False)
    provider.set_access_token("should-not-be-used")
    provider.save()

    credentials = get_active_credentials()

    assert credentials.access_token != "should-not-be-used"


@pytest.mark.django_db
def test_whatsapp_client_uses_active_provider_graph_api_version():
    provider = WhatsAppProvider(
        name="Prod", phone_number_id="123456", graph_api_version="v26.0"
    )
    provider.set_access_token("db-token")
    provider.save()

    client = WhatsAppClient()

    assert client.base_url == "https://graph.facebook.com/v26.0/123456"


@pytest.mark.django_db
def test_webhook_verification_challenge_uses_active_provider_verify_token(api_client):
    provider = WhatsAppProvider(name="Prod", phone_number_id="123456")
    provider.set_verify_token("db-verify")
    provider.save()

    response = api_client.get(
        "/api/v1/whatsapp/webhook/",
        {"hub.mode": "subscribe", "hub.verify_token": "db-verify", "hub.challenge": "999"},
    )

    assert response.status_code == 200
    assert response.content == b"999"
