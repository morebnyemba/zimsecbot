from unittest.mock import patch

import pytest

from apps.notes.models import Note
from apps.subjects.models import Subject

from . import services
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
    document = KnowledgeDocument.objects.create(
        note=note, subject=note.subject, title=note.title
    )
    close = KnowledgeChunk.objects.create(
        document=document, chunk_index=0, text="close", embedding=[0.9, 0.1, 0.0] + [0.0] * 765
    )
    far = KnowledgeChunk.objects.create(
        document=document, chunk_index=1, text="far", embedding=[0.0, 0.0, 1.0] + [0.0] * 765
    )

    results = search("query", top_k=2)

    assert results[0].id == close.id
    assert results[1].id == far.id
