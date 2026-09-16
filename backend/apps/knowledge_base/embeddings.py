import math

from google import genai
from google.genai import types

from apps.ai_tutor.providers import get_active_api_key

# text-embedding-004 was retired by Google; gemini-embedding-001 is its
# successor. It natively outputs 3072-dim vectors, so output_dimensionality
# must be pinned to match KnowledgeChunk.embedding's 768-dim pgvector column.
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768


def embed_text(text: str) -> list[float]:
    # Resolved fresh on every call (not cached) so a key rotated in
    # /admin/ai_tutor/aiprovider/ takes effect immediately, same as chat
    # generation already does -- a module-level cached client here
    # previously kept using whatever key was resolved on first call for the
    # life of the process.
    client = genai.Client(api_key=get_active_api_key())
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
    )
    values = response.embeddings[0].values
    # Google only normalizes to unit length at the native 3072 dimensions;
    # truncated (MRL) outputs like our 768-dim vectors must be renormalized
    # by hand or cosine-distance comparisons between chunks are skewed.
    norm = math.sqrt(sum(v * v for v in values))
    if norm == 0:
        return values
    return [v / norm for v in values]
