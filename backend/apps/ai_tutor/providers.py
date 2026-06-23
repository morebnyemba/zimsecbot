from django.conf import settings
from google import genai

from .models import AIProvider


class GeminiProvider:
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    def generate(self, system_prompt: str, prompt: str) -> str:
        contents = f"{system_prompt}\n\n{prompt}"
        response = self._client.models.generate_content(model=self._model_name, contents=contents)
        return response.text


def get_active_provider() -> GeminiProvider:
    provider = AIProvider.objects.filter(
        is_active=True, provider_type=AIProvider.ProviderType.GEMINI
    ).first()
    if provider:
        return GeminiProvider(api_key=provider.get_api_key(), model_name=provider.model_name)
    return GeminiProvider(api_key=settings.GEMINI_API_KEY)
