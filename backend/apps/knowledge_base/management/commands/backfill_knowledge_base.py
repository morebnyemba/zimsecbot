from django.core.management.base import BaseCommand

from apps.notes.models import Note

from ...services import ingest_note
from ...tasks import ingest_note_task


class Command(BaseCommand):
    help = "Embed Notes into the knowledge base that aren't indexed yet (or all, with --all)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Reindex every note, including ones already indexed.",
        )
        parser.add_argument(
            "--sync",
            action="store_true",
            help="Embed notes synchronously in this process instead of enqueueing a Celery task.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List which notes would be processed without embedding anything.",
        )

    def handle(self, *args, **options):
        notes = Note.objects.all().order_by("id")
        if not options["all"]:
            notes = notes.filter(knowledge_document__isnull=True) | notes.filter(
                knowledge_document__indexed_at__isnull=True
            )
            notes = notes.distinct().order_by("id")

        count = notes.count()
        if count == 0:
            self.stdout.write("Nothing to backfill.")
            return

        if options["dry_run"]:
            for note in notes:
                self.stdout.write(f"Would index: {note.id}  {note.title}")
            self.stdout.write(self.style.SUCCESS(f"{count} note(s) would be indexed."))
            return

        for note in notes.iterator():
            if options["sync"]:
                ingest_note(note)
            else:
                ingest_note_task.delay(str(note.id))

        mode = "synchronously" if options["sync"] else "via Celery"
        self.stdout.write(self.style.SUCCESS(f"Queued {count} note(s) for indexing {mode}."))
