from django.conf import settings
from google import genai

from .models import AIProvider


class GeminiProvider:
    def __init__(self, api_key: str, model_name: str = "gemini-3.6-flash"):
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    def generate(self, system_prompt: str, prompt: str) -> str:
        contents = f"{system_prompt}\n\n{prompt}"
        response = self._client.models.generate_content(model=self._model_name, contents=contents)
        return response.text


def get_active_api_key() -> str:
    """The Gemini API key any Gemini caller should use -- an active DB
    AIProvider row takes precedence over GEMINI_API_KEY, same precedence
    used for WhatsApp credentials (apps.whatsapp.providers). Shared with
    apps.knowledge_base.embeddings so embedding calls use the same,
    admin-rotatable key as chat generation instead of silently reading the
    (possibly stale/unset) env var on its own.
    """
    provider = AIProvider.objects.filter(
        is_active=True, provider_type=AIProvider.ProviderType.GEMINI
    ).first()
    return provider.api_key if provider else settings.GEMINI_API_KEY


def get_active_provider() -> GeminiProvider:
    provider = AIProvider.objects.filter(
        is_active=True, provider_type=AIProvider.ProviderType.GEMINI
    ).first()
    if provider:
        return GeminiProvider(api_key=provider.api_key, model_name=provider.model_name)
    return GeminiProvider(api_key=settings.GEMINI_API_KEY)
