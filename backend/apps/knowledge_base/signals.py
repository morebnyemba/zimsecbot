from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notes.models import Note

from .tasks import ingest_note_task


@receiver(post_save, sender=Note)
def trigger_note_ingestion(sender, instance, **kwargs):
    # Draft notes (e.g. freshly extracted from a PDF/URL, not yet reviewed)
    # stay out of the knowledge base until a content admin flips status to
    # published -- that save fires this same signal again, so nothing extra
    # is needed to index it once it's approved.
    if instance.status != Note.Status.PUBLISHED:
        return
    ingest_note_task.delay(str(instance.id))
