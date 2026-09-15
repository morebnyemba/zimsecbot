from dataclasses import dataclass

from django.conf import settings

from .models import WhatsAppProvider


@dataclass
class WhatsAppCredentials:
    access_token: str
    phone_number_id: str
    app_secret: str
    verify_token: str
    graph_api_version: str


def get_active_credentials() -> WhatsAppCredentials:
    provider = WhatsAppProvider.objects.filter(is_active=True).first()
    if provider:
        return WhatsAppCredentials(
            access_token=provider.get_access_token(),
            phone_number_id=provider.phone_number_id,
            app_secret=provider.get_app_secret(),
            verify_token=provider.get_verify_token(),
            graph_api_version=provider.graph_api_version,
        )
    return WhatsAppCredentials(
        access_token=settings.WHATSAPP_ACCESS_TOKEN,
        phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID,
        app_secret=settings.WHATSAPP_APP_SECRET,
        verify_token=settings.WHATSAPP_VERIFY_TOKEN,
        graph_api_version=settings.WHATSAPP_GRAPH_API_VERSION,
    )
