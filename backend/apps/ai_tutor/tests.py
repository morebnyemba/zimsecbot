from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from .encryption import decrypt_value, encrypt_value
from .models import AIProvider, AISession, Message
from .tasks import answer_whatsapp_question

User = get_user_model()


def test_encryption_round_trip():
    token = encrypt_value("super-secret-key")
    assert token != "super-secret-key"
    assert decrypt_value(token) == "super-secret-key"


@pytest.mark.django_db
def test_ai_provider_set_and_get_api_key():
    provider = AIProvider(name="Gemini")
    provider.set_api_key("abc123")
    provider.save()

    provider.refresh_from_db()
    assert provider.api_key_encrypted != "abc123"
    assert provider.get_api_key() == "abc123"


@pytest.fixture
def student(db):
    return User.objects.create_user(email="student@example.com", password="testpass123")


@pytest.fixture
def client(student):
    api = APIClient()
    api.force_authenticate(user=student)
    return api


@pytest.mark.django_db
@patch("apps.ai_tutor.services.search", return_value=[])
@patch("apps.ai_tutor.services.get_active_provider")
def test_ask_with_no_context_appends_disclaimer(mock_get_provider, mock_search):
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "Here is a general answer."
    mock_get_provider.return_value = mock_provider

    from .services import ask

    session = AISession.objects.create(channel=AISession.Channel.WEB)
    result = ask(session, "What is gravity?")

    assert "general answer" in result["answer"]
    assert "couldn't find this topic" in result["answer"]
    assert result["sources"] == []
    assert Message.objects.filter(session=session).count() == 2


@pytest.mark.django_db
@patch("apps.ai_tutor.services.get_active_provider")
def test_ask_with_context_returns_sources(mock_get_provider):
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "Grounded answer."
    mock_get_provider.return_value = mock_provider

    chunk = MagicMock()
    chunk.text = "Relevant context."
    chunk.document_id = "doc-1"
    chunk.document.title = "Photosynthesis"

    with patch("apps.ai_tutor.services.search", return_value=[chunk]):
        from .services import ask

        session = AISession.objects.create(channel=AISession.Channel.WEB)
        result = ask(session, "Explain photosynthesis")

    assert result["answer"] == "Grounded answer."
    assert result["sources"] == [{"document_id": "doc-1", "title": "Photosynthesis"}]


@pytest.mark.django_db
def test_ask_view_creates_session_and_returns_answer(client):
    with patch("apps.ai_tutor.services.search", return_value=[]), patch(
        "apps.ai_tutor.services.get_active_provider"
    ) as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.generate.return_value = "Answer"
        mock_get_provider.return_value = mock_provider

        response = client.post(
            "/api/v1/ai-tutor/ask/", {"question": "What is 2+2?"}, format="json"
        )

    assert response.status_code == 200
    assert AISession.objects.filter(id=response.data["session_id"]).exists()
    assert "Answer" in response.data["answer"]


@pytest.mark.django_db
@patch("apps.ai_tutor.tasks.WhatsAppClient")
@patch("apps.ai_tutor.services.search", return_value=[])
@patch("apps.ai_tutor.services.get_active_provider")
def test_answer_whatsapp_question_sends_reply(mock_get_provider, mock_search, mock_client_cls):
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "WhatsApp answer."
    mock_get_provider.return_value = mock_provider

    answer_whatsapp_question("263771234567", "What is photosynthesis?")

    session = AISession.objects.get(phone_number="263771234567")
    assert session.channel == AISession.Channel.WHATSAPP
    mock_client_cls.return_value.send_text.assert_called_once()
    args = mock_client_cls.return_value.send_text.call_args[0]
    assert args[0] == "263771234567"
    assert "WhatsApp answer" in args[1]
