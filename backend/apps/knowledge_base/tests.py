from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.test import override_settings

from apps.ai_tutor.models import AIProvider
from apps.notes.models import Note
from apps.subjects.models import Subject

from . import services
from .embeddings import embed_text
from .models import KnowledgeChunk, KnowledgeDocument
from .retrieval import search


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Biology", code="BIO", level=Subject.Level.O_LEVEL)


@pytest.fixture
def note(subject):
    return Note.objects.create(subject=subject, title="Cells", content=" ".join(["word"] * 250))


def test_chunk_text_splits_long_text_with_overlap():
    text = " ".join(str(i) for i in range(500))
    chunks = services.chunk_text(text, chunk_size=200, overlap=30)
    assert len(chunks) > 1
    assert chunks[0].split()[0] == "0"
    last_word_of_first = chunks[0].split()[-1]
    first_word_of_second = chunks[1].split()[0]
    assert int(last_word_of_first) >= int(first_word_of_second)


def test_chunk_text_empty_returns_no_chunks():
    assert services.chunk_text("") == []


@pytest.mark.django_db
@patch("apps.knowledge_base.services.embed_text", return_value=[0.1] * 768)
def test_ingest_note_creates_document_and_chunks(mock_embed, note):
    document = services.ingest_note(note)

    assert document.note_id == note.id
    assert document.indexed_at is not None
    chunks = list(document.chunks.all())
    assert len(chunks) > 0
    assert all(chunk.embedding is not None for chunk in chunks)


@pytest.mark.django_db
@patch("apps.knowledge_base.services.embed_text")
def test_ingest_note_continues_on_embedding_failure(mock_embed, note):
    mock_embed.side_effect = Exception("boom")
    document = services.ingest_note(note)
    chunks = list(document.chunks.all())
    assert len(chunks) > 0
    assert all(chunk.embedding is None for chunk in chunks)


@pytest.mark.django_db
@patch("apps.knowledge_base.retrieval.embed_text", return_value=[1.0, 0.0, 0.0] + [0.0] * 765)
def test_search_orders_by_similarity(mock_embed, note):
    document = KnowledgeDocument.objects.create(note=note, subject=note.subject, title=note.title)
    close = KnowledgeChunk.objects.create(
        document=document, chunk_index=0, text="close", embedding=[0.9, 0.1, 0.0] + [0.0] * 765
    )
    far = KnowledgeChunk.objects.create(
        document=document, chunk_index=1, text="far", embedding=[0.0, 0.0, 1.0] + [0.0] * 765
    )

    results = search("query", top_k=2)

    assert results[0].id == close.id
    assert results[1].id == far.id


@pytest.mark.django_db
@patch("apps.knowledge_base.services.embed_text", return_value=[0.1] * 768)
def test_backfill_command_indexes_unindexed_notes_sync(mock_embed, note):
    call_command("backfill_knowledge_base", "--sync")

    document = KnowledgeDocument.objects.get(note=note)
    assert document.indexed_at is not None
    assert document.chunks.exists()


@pytest.mark.django_db
@patch("apps.knowledge_base.services.embed_text", return_value=[0.1] * 768)
def test_backfill_command_skips_already_indexed_notes_by_default(mock_embed, note):
    services.ingest_note(note)

    mock_embed.reset_mock()
    call_command("backfill_knowledge_base", "--sync")

    mock_embed.assert_not_called()


@pytest.mark.django_db
@patch("apps.knowledge_base.services.embed_text", return_value=[0.1] * 768)
def test_backfill_command_all_reindexes_already_indexed_notes(mock_embed, note):
    services.ingest_note(note)

    mock_embed.reset_mock()
    call_command("backfill_knowledge_base", "--all", "--sync")

    mock_embed.assert_called()


@pytest.mark.django_db
@patch("apps.knowledge_base.services.embed_text", return_value=[0.1] * 768)
def test_backfill_command_dry_run_does_not_index(mock_embed, note):
    call_command("backfill_knowledge_base", "--dry-run")

    assert not KnowledgeDocument.objects.filter(note=note).exists()
    mock_embed.assert_not_called()


@pytest.mark.django_db
@patch("apps.knowledge_base.tasks.ingest_note_task.delay")
def test_backfill_command_default_mode_enqueues_celery_task(mock_delay, note):
    call_command("backfill_knowledge_base")

    mock_delay.assert_called_once_with(str(note.id))


# --- embed_text uses the same admin-rotatable Gemini key as chat generation ---


@pytest.mark.django_db
@patch("apps.knowledge_base.embeddings.genai.Client")
def test_embed_text_uses_active_db_provider_key(mock_client_cls):
    AIProvider.objects.create(name="Prod", api_key="db-key", is_active=True)
    mock_response = MagicMock()
    mock_response.embeddings = [MagicMock(values=[0.1, 0.2, 0.3])]
    mock_client_cls.return_value.models.embed_content.return_value = mock_response

    result = embed_text("photosynthesis")

    mock_client_cls.assert_called_once_with(api_key="db-key")
    assert len(result) == 3
    assert result == pytest.approx([v / (0.14**0.5) for v in [0.1, 0.2, 0.3]])


@pytest.mark.django_db
@patch("apps.knowledge_base.embeddings.genai.Client")
def test_embed_text_falls_back_to_settings_key_when_no_active_provider(mock_client_cls):
    mock_response = MagicMock()
    mock_response.embeddings = [MagicMock(values=[0.1])]
    mock_client_cls.return_value.models.embed_content.return_value = mock_response

    with override_settings(GEMINI_API_KEY="env-key"):
        embed_text("x")

    mock_client_cls.assert_called_once_with(api_key="env-key")


@pytest.mark.django_db
@patch("apps.knowledge_base.embeddings.genai.Client")
def test_embed_text_pins_output_dimensionality_and_normalizes(mock_client_cls):
    mock_response = MagicMock()
    mock_response.embeddings = [MagicMock(values=[3.0, 4.0])]
    mock_client_cls.return_value.models.embed_content.return_value = mock_response

    result = embed_text("x")

    _, kwargs = mock_client_cls.return_value.models.embed_content.call_args
    assert kwargs["config"].output_dimensionality == 768
    assert result == pytest.approx([0.6, 0.8])
