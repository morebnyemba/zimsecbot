from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notes.models import Note

from .tasks import ingest_note_task


@receiver(post_save, sender=Note)
def trigger_note_ingestion(sender, instance, **kwargs):
    ingest_note_task.delay(str(instance.id))
