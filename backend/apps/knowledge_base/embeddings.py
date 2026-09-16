from google import genai

from apps.ai_tutor.providers import get_active_api_key

EMBEDDING_MODEL = "text-embedding-004"


def embed_text(text: str) -> list[float]:
    # Resolved fresh on every call (not cached) so a key rotated in
    # /admin/ai_tutor/aiprovider/ takes effect immediately, same as chat
    # generation already does -- a module-level cached client here
    # previously kept using whatever key was resolved on first call for the
    # life of the process.
    client = genai.Client(api_key=get_active_api_key())
    response = client.models.embed_content(model=EMBEDDING_MODEL, contents=text)
    return response.embeddings[0].values
