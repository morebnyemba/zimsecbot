from celery import shared_task

from apps.notes.models import Note

from .services import ingest_note


@shared_task
def ingest_note_task(note_id):
    try:
        note = Note.objects.get(id=note_id)
    except Note.DoesNotExist:
        return
    ingest_note(note)
