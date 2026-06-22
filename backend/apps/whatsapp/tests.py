import hashlib
import hmac
import json
from unittest.mock import patch

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from .models import WebhookEventLog
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
