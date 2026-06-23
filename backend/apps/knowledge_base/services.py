import logging

from django.utils import timezone

from .embeddings import embed_text
from .models import KnowledgeChunk, KnowledgeDocument

logger = logging.getLogger(__name__)

CHUNK_SIZE_WORDS = 200
CHUNK_OVERLAP_WORDS = 30


def chunk_text(
    text: str, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = CHUNK_OVERLAP_WORDS
) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks = []
    step = chunk_size - overlap
    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]
        if chunk_words:
            chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break
    return chunks


def ingest_note(note) -> KnowledgeDocument:
    document, _ = KnowledgeDocument.objects.update_or_create(
        note=note,
        defaults={
            "source_type": KnowledgeDocument.SourceType.NOTE,
            "subject_id": note.subject_id,
            "topic_id": note.topic_id,
            "subtopic_id": note.subtopic_id,
            "title": note.title,
        },
    )
    document.chunks.all().delete()

    texts = chunk_text(note.content)
    for index, chunk_text_value in enumerate(texts):
        try:
            embedding = embed_text(chunk_text_value)
        except Exception:
            logger.exception("Failed to embed chunk %s for note %s", index, note.id)
            embedding = None
        KnowledgeChunk.objects.create(
            document=document,
            chunk_index=index,
            text=chunk_text_value,
            embedding=embedding,
        )

    document.indexed_at = timezone.now()
    document.save(update_fields=["indexed_at"])
    return document
