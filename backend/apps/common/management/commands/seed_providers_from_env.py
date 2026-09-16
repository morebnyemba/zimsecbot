from django.conf import settings
from django.core.management.base import BaseCommand

from apps.ai_tutor.models import AIProvider
from apps.whatsapp.models import WhatsAppProvider


class Command(BaseCommand):
    help = (
        "Create or update the DB-backed AIProvider (Gemini) and WhatsAppProvider rows "
        "from the corresponding env vars, so credentials can be rotated in Django admin "
        "instead of editing .env and redeploying."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            default="Default",
            help="Name to use for the created/updated provider rows (default: 'Default').",
        )

    def handle(self, *args, **options):
        name = options["name"]
        self._seed_gemini(name)
        self._seed_whatsapp(name)

    def _seed_gemini(self, name):
        if not settings.GEMINI_API_KEY:
            self.stdout.write("GEMINI_API_KEY is not set; skipping AIProvider.")
            return

        provider, created = AIProvider.objects.get_or_create(
            name=name,
            provider_type=AIProvider.ProviderType.GEMINI,
            defaults={"is_active": True},
        )
        provider.set_api_key(settings.GEMINI_API_KEY)
        provider.save()

        verb = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(f"{verb} AIProvider '{provider.name}' from GEMINI_API_KEY.")
        )

    def _seed_whatsapp(self, name):
        has_any_env_value = any(
            [
                settings.WHATSAPP_ACCESS_TOKEN,
                settings.WHATSAPP_PHONE_NUMBER_ID,
                settings.WHATSAPP_APP_SECRET,
                settings.WHATSAPP_VERIFY_TOKEN,
            ]
        )
        if not has_any_env_value:
            self.stdout.write("No WHATSAPP_* env vars are set; skipping WhatsAppProvider.")
            return

        provider, created = WhatsAppProvider.objects.get_or_create(
            name=name, defaults={"is_active": True}
        )
        provider.waba_id = settings.WHATSAPP_WABA_ID
        provider.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        provider.graph_api_version = settings.WHATSAPP_GRAPH_API_VERSION
        if settings.WHATSAPP_ACCESS_TOKEN:
            provider.set_access_token(settings.WHATSAPP_ACCESS_TOKEN)
        if settings.WHATSAPP_APP_SECRET:
            provider.set_app_secret(settings.WHATSAPP_APP_SECRET)
        if settings.WHATSAPP_VERIFY_TOKEN:
            provider.set_verify_token(settings.WHATSAPP_VERIFY_TOKEN)
        provider.save()

        verb = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} WhatsAppProvider '{provider.name}' from WHATSAPP_* env vars."
            )
        )
