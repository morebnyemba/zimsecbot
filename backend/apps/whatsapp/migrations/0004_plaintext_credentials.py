import base64
import hashlib

from django.conf import settings
from django.db import migrations, models


def _decrypt(ciphertext: str) -> str:
    """Standalone copy of the old apps.common.encryption.decrypt_value.

    Inlined here (rather than imported) because this migration must keep
    working after that module is deleted in the same change that adds it.
    """
    if not ciphertext:
        return ""
    from cryptography.fernet import Fernet, InvalidToken

    key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    try:
        return Fernet(key).decrypt(ciphertext.encode()).decode()
    except (InvalidToken, ValueError):
        # Corrupted/foreign ciphertext (e.g. SECRET_KEY rotated since it was
        # written) -- can't recover the plaintext. Leave it blank rather than
        # crash the migration; whoever owns the row re-enters it in admin.
        return ""


def decrypt_credentials(apps, schema_editor):
    WhatsAppProvider = apps.get_model("whatsapp", "WhatsAppProvider")
    for provider in WhatsAppProvider.objects.all():
        provider.access_token = _decrypt(provider.access_token_encrypted)
        provider.app_secret = _decrypt(provider.app_secret_encrypted)
        provider.verify_token = _decrypt(provider.verify_token_encrypted)
        provider.save(update_fields=["access_token", "app_secret", "verify_token"])


class Migration(migrations.Migration):
    dependencies = [("whatsapp", "0003_whatsappprovider_waba_id")]

    operations = [
        migrations.AddField(
            model_name="whatsappprovider",
            name="access_token",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="whatsappprovider",
            name="app_secret",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="whatsappprovider",
            name="verify_token",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(decrypt_credentials, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="whatsappprovider",
            name="access_token_encrypted",
        ),
        migrations.RemoveField(
            model_name="whatsappprovider",
            name="app_secret_encrypted",
        ),
        migrations.RemoveField(
            model_name="whatsappprovider",
            name="verify_token_encrypted",
        ),
    ]
