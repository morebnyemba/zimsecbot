from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.subjects.models import Subject, Subtopic, Topic

from ...ingestion import ExtractionError, extract_pdf_text, extract_url_text, is_url
from ...models import Note


class Command(BaseCommand):
    help = (
        "Create a draft Note from a local PDF file or a web page URL, for review in "
        "admin before publishing. Does not embed anything into the knowledge base -- "
        "that only happens once the note is marked Published."
    )

    def add_arguments(self, parser):
        parser.add_argument("source", help="Path to a local PDF file, or an http(s):// URL.")
        parser.add_argument("--subject", required=True, help="Subject code, e.g. BIO.")
        parser.add_argument("--title", required=True)
        parser.add_argument("--topic", help="Topic name (must already exist under the subject).")
        parser.add_argument(
            "--subtopic", help="Subtopic name (must already exist under --topic)."
        )

    def handle(self, *args, **options):
        source = options["source"]

        subject = Subject.objects.filter(code__iexact=options["subject"]).first()
        if not subject:
            raise CommandError(f"No subject with code {options['subject']!r}.")

        topic = None
        if options.get("topic"):
            topic = Topic.objects.filter(subject=subject, name__iexact=options["topic"]).first()
            if not topic:
                raise CommandError(
                    f"No topic {options['topic']!r} under subject {subject.code}."
                )

        subtopic = None
        if options.get("subtopic"):
            if not topic:
                raise CommandError("--subtopic requires --topic.")
            subtopic = Subtopic.objects.filter(
                topic=topic, name__iexact=options["subtopic"]
            ).first()
            if not subtopic:
                raise CommandError(
                    f"No subtopic {options['subtopic']!r} under topic {topic.name!r}."
                )

        try:
            if is_url(source):
                content = extract_url_text(source)
            else:
                path = Path(source)
                if not path.exists():
                    raise CommandError(f"File not found: {source}")
                with path.open("rb") as f:
                    content = extract_pdf_text(f)
        except ExtractionError as exc:
            raise CommandError(str(exc)) from exc

        note = Note.objects.create(
            subject=subject,
            topic=topic,
            subtopic=subtopic,
            title=options["title"],
            content=content,
            status=Note.Status.DRAFT,
            source=source,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created draft Note {note.id} ({len(content)} chars extracted from {source}). "
                f"Review it at /admin/notes/note/{note.id}/change/, then mark it Published "
                f"to index it into the knowledge base."
            )
        )
