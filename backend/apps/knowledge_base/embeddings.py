from django.conf import settings
from google import genai

EMBEDDING_MODEL = "text-embedding-004"

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def embed_text(text: str) -> list[float]:
    response = _get_client().models.embed_content(model=EMBEDDING_MODEL, contents=text)
    return response.embeddings[0].values
