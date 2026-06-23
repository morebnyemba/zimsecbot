from pgvector.django import CosineDistance

from .embeddings import embed_text
from .models import KnowledgeChunk

DEFAULT_TOP_K = 5


def search(
    query: str, subject_id=None, topic_id=None, top_k: int = DEFAULT_TOP_K
) -> list[KnowledgeChunk]:
    query_embedding = embed_text(query)

    queryset = KnowledgeChunk.objects.filter(embedding__isnull=False)
    if subject_id:
        queryset = queryset.filter(document__subject_id=subject_id)
    if topic_id:
        queryset = queryset.filter(document__topic_id=topic_id)

    return list(
        queryset.annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")
        .select_related("document")[:top_k]
    )
