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


def decrypt_api_keys(apps, schema_editor):
    AIProvider = apps.get_model("ai_tutor", "AIProvider")
    for provider in AIProvider.objects.all():
        provider.api_key = _decrypt(provider.api_key_encrypted)
        provider.save(update_fields=["api_key"])


class Migration(migrations.Migration):
    dependencies = [("ai_tutor", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="aiprovider",
            name="api_key",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(decrypt_api_keys, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="aiprovider",
            name="api_key_encrypted",
        ),
    ]
