from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client as DjangoClient
from rest_framework.test import APIClient

from apps.subjects.models import Subject, Topic

from . import ingestion
from .admin import NoteAdmin
from .ingestion import ExtractionError, extract_pdf_text, extract_url_text, is_url
from .models import Note

User = get_user_model()


@pytest.fixture
def client(db):
    student = User.objects.create_user(email="student@example.com", password="testpass123")
    api = APIClient()
    api.force_authenticate(user=student)
    return api


@pytest.fixture
def content_admin_client(db):
    admin = User.objects.create_user(
        email="content-admin@example.com", password="testpass123", role=User.Role.CONTENT_ADMIN
    )
    api = APIClient()
    api.force_authenticate(user=admin)
    return api


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Physics", code="PHY", level=Subject.Level.O_LEVEL)


@pytest.mark.django_db
def test_notes_search(client):
    subject = Subject.objects.create(name="Physics", code="PHY", level=Subject.Level.O_LEVEL)
    Note.objects.create(subject=subject, title="Newton's Laws", content="F=ma")
    Note.objects.create(subject=subject, title="Thermodynamics", content="entropy")

    response = client.get("/api/v1/notes/?q=Newton")
    assert response.status_code == 200

    response = client.get("/api/v1/notes/?search=Newton")
    assert response.data["count"] == 1


# --- status gating: students never see drafts, content admins see everything ---


@pytest.mark.django_db
def test_students_only_see_published_notes(client, subject):
    Note.objects.create(subject=subject, title="Live", content="x", status=Note.Status.PUBLISHED)
    Note.objects.create(subject=subject, title="Draft", content="x", status=Note.Status.DRAFT)

    response = client.get("/api/v1/notes/")

    titles = [n["title"] for n in response.data["results"]]
    assert titles == ["Live"]


@pytest.mark.django_db
def test_content_admin_sees_draft_notes(content_admin_client, subject):
    Note.objects.create(subject=subject, title="Live", content="x", status=Note.Status.PUBLISHED)
    Note.objects.create(subject=subject, title="Draft", content="x", status=Note.Status.DRAFT)

    response = content_admin_client.get("/api/v1/notes/")

    titles = {n["title"] for n in response.data["results"]}
    assert titles == {"Live", "Draft"}


# --- knowledge-base indexing only fires for published notes ---


@pytest.mark.django_db
@patch("apps.knowledge_base.signals.ingest_note_task.delay")
def test_draft_note_does_not_trigger_ingestion(mock_delay, subject):
    Note.objects.create(subject=subject, title="Draft", content="x", status=Note.Status.DRAFT)

    mock_delay.assert_not_called()


@pytest.mark.django_db
@patch("apps.knowledge_base.signals.ingest_note_task.delay")
def test_published_note_triggers_ingestion(mock_delay, subject):
    Note.objects.create(subject=subject, title="Live", content="x", status=Note.Status.PUBLISHED)

    mock_delay.assert_called_once()


@pytest.mark.django_db
@patch("apps.knowledge_base.signals.ingest_note_task.delay")
def test_publishing_a_draft_triggers_ingestion(mock_delay, subject):
    note = Note.objects.create(
        subject=subject, title="Draft", content="x", status=Note.Status.DRAFT
    )
    mock_delay.reset_mock()

    note.status = Note.Status.PUBLISHED
    note.save()

    mock_delay.assert_called_once_with(str(note.id))


# --- extraction service ---


def test_is_url():
    assert is_url("https://example.com/article")
    assert is_url("http://example.com")
    assert not is_url("/local/path/file.pdf")
    assert not is_url("relative.pdf")


def test_extract_pdf_text_joins_non_blank_pages():
    page1, page2, page3 = MagicMock(), MagicMock(), MagicMock()
    page1.extract_text.return_value = "  Page one text  "
    page2.extract_text.return_value = "   "
    page3.extract_text.return_value = "Page three text"

    with patch.object(ingestion, "PdfReader") as mock_reader_cls:
        mock_reader_cls.return_value.pages = [page1, page2, page3]
        result = extract_pdf_text(MagicMock())

    assert result == "Page one text\n\nPage three text"


def test_extract_pdf_text_raises_when_no_extractable_text():
    blank_page = MagicMock()
    blank_page.extract_text.return_value = ""

    with patch.object(ingestion, "PdfReader") as mock_reader_cls:
        mock_reader_cls.return_value.pages = [blank_page]
        with pytest.raises(ExtractionError, match="scanned/image-only"):
            extract_pdf_text(MagicMock())


def test_extract_pdf_text_raises_on_unreadable_pdf():
    with patch.object(ingestion, "PdfReader", side_effect=ingestion.PdfReadError("bad file")):
        with pytest.raises(ExtractionError, match="Could not read PDF"):
            extract_pdf_text(MagicMock())


@patch("apps.notes.ingestion.trafilatura.extract", return_value="Clean article text.")
@patch("apps.notes.ingestion.trafilatura.fetch_url", return_value="<html>raw</html>")
def test_extract_url_text_returns_extracted_content(mock_fetch, mock_extract):
    result = extract_url_text("https://example.com/article")

    assert result == "Clean article text."
    mock_fetch.assert_called_once_with("https://example.com/article")


@patch("apps.notes.ingestion.trafilatura.fetch_url", return_value=None)
def test_extract_url_text_raises_when_fetch_fails(mock_fetch):
    with pytest.raises(ExtractionError, match="Could not fetch"):
        extract_url_text("https://example.com/unreachable")


@patch("apps.notes.ingestion.trafilatura.extract", return_value=None)
@patch("apps.notes.ingestion.trafilatura.fetch_url", return_value="<html></html>")
def test_extract_url_text_raises_when_no_article_text(mock_fetch, mock_extract):
    with pytest.raises(ExtractionError, match="Could not extract readable article text"):
        extract_url_text("https://example.com/empty")


# --- DRF import endpoint ---


@pytest.mark.django_db
def test_note_import_requires_content_admin(client, subject):
    response = client.post(
        "/api/v1/notes/import/",
        {"subject": str(subject.id), "title": "X", "source_url": "https://example.com/a"},
    )

    assert response.status_code == 403


@pytest.mark.django_db
@patch("apps.notes.views.extract_url_text", return_value="Extracted body text.")
def test_note_import_creates_draft_from_url(mock_extract, content_admin_client, subject):
    response = content_admin_client.post(
        "/api/v1/notes/import/",
        {
            "subject": str(subject.id),
            "title": "Photosynthesis",
            "source_url": "https://example.com/photosynthesis",
        },
    )

    assert response.status_code == 201
    note = Note.objects.get(title="Photosynthesis")
    assert note.status == Note.Status.DRAFT
    assert note.content == "Extracted body text."
    assert note.source == "https://example.com/photosynthesis"


@pytest.mark.django_db
@patch("apps.notes.views.extract_pdf_text", return_value="PDF body text.")
def test_note_import_creates_draft_from_pdf_upload(mock_extract, content_admin_client, subject):
    upload = SimpleUploadedFile("bio-notes.pdf", b"%PDF-1.4 fake", content_type="application/pdf")

    response = content_admin_client.post(
        "/api/v1/notes/import/",
        {"subject": str(subject.id), "title": "Bio Notes", "source_file": upload},
        format="multipart",
    )

    assert response.status_code == 201
    note = Note.objects.get(title="Bio Notes")
    assert note.status == Note.Status.DRAFT
    assert note.content == "PDF body text."
    assert note.source == "bio-notes.pdf"


@pytest.mark.django_db
def test_note_import_requires_exactly_one_source(content_admin_client, subject):
    response = content_admin_client.post(
        "/api/v1/notes/import/", {"subject": str(subject.id), "title": "X"}
    )
    assert response.status_code == 400

    upload = SimpleUploadedFile("a.pdf", b"x", content_type="application/pdf")
    response = content_admin_client.post(
        "/api/v1/notes/import/",
        {
            "subject": str(subject.id),
            "title": "X",
            "source_url": "https://example.com/a",
            "source_file": upload,
        },
        format="multipart",
    )
    assert response.status_code == 400


@pytest.mark.django_db
@patch("apps.notes.views.extract_url_text", side_effect=ExtractionError("could not fetch"))
def test_note_import_returns_400_on_extraction_failure(mock_extract, content_admin_client, subject):
    response = content_admin_client.post(
        "/api/v1/notes/import/",
        {"subject": str(subject.id), "title": "X", "source_url": "https://example.com/dead"},
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "extraction_failed"
    assert not Note.objects.filter(title="X").exists()


# --- management command ---


@pytest.mark.django_db
@patch("apps.notes.management.commands.import_content.extract_pdf_text", return_value="Extracted.")
def test_import_content_command_creates_draft_from_pdf(mock_extract, subject, tmp_path):
    pdf_path = tmp_path / "notes.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    call_command("import_content", str(pdf_path), "--subject", "PHY", "--title", "Newton")

    note = Note.objects.get(title="Newton")
    assert note.status == Note.Status.DRAFT
    assert note.content == "Extracted."
    assert note.source == str(pdf_path)


@pytest.mark.django_db
@patch("apps.notes.management.commands.import_content.extract_url_text", return_value="Web text.")
def test_import_content_command_creates_draft_from_url(mock_extract, subject):
    call_command(
        "import_content",
        "https://example.com/article",
        "--subject",
        "PHY",
        "--title",
        "From Web",
    )

    note = Note.objects.get(title="From Web")
    assert note.content == "Web text."
    assert note.source == "https://example.com/article"


@pytest.mark.django_db
def test_import_content_command_rejects_unknown_subject(tmp_path):
    pdf_path = tmp_path / "notes.pdf"
    pdf_path.write_bytes(b"x")

    with pytest.raises(CommandError, match="No subject"):
        call_command("import_content", str(pdf_path), "--subject", "NOPE", "--title", "X")


@pytest.mark.django_db
def test_import_content_command_rejects_missing_file(subject):
    with pytest.raises(CommandError, match="File not found"):
        call_command(
            "import_content", "/no/such/file.pdf", "--subject", "PHY", "--title", "X"
        )


@pytest.mark.django_db
@patch("apps.notes.management.commands.import_content.extract_pdf_text", return_value="Extracted.")
def test_import_content_command_resolves_topic(mock_extract, subject, tmp_path):
    topic = Topic.objects.create(subject=subject, name="Mechanics")
    pdf_path = tmp_path / "notes.pdf"
    pdf_path.write_bytes(b"x")

    call_command(
        "import_content",
        str(pdf_path),
        "--subject",
        "PHY",
        "--title",
        "X",
        "--topic",
        "Mechanics",
    )

    note = Note.objects.get(title="X")
    assert note.topic_id == topic.id


# --- Django admin: import view + publish/draft actions ---


@pytest.fixture
def admin_django_client(db):
    superuser = User.objects.create_superuser(email="super@example.com", password="testpass123")
    dj_client = DjangoClient()
    dj_client.force_login(superuser)
    return dj_client


@pytest.mark.django_db
def test_admin_import_view_renders_form(admin_django_client):
    response = admin_django_client.get("/admin/notes/note/import/")
    assert response.status_code == 200


@pytest.mark.django_db
@patch("apps.notes.admin.extract_url_text", return_value="Extracted via admin.")
def test_admin_import_view_creates_draft_and_redirects(mock_extract, admin_django_client, subject):
    response = admin_django_client.post(
        "/admin/notes/note/import/",
        {"subject": str(subject.id), "title": "Admin Import", "source_url": "https://example.com/x"},
    )

    assert response.status_code == 302
    note = Note.objects.get(title="Admin Import")
    assert note.status == Note.Status.DRAFT
    assert note.content == "Extracted via admin."


@pytest.mark.django_db
def test_admin_mark_published_action(subject):
    note = Note.objects.create(subject=subject, title="X", content="y", status=Note.Status.DRAFT)
    admin_instance = NoteAdmin(Note, None)

    with patch("apps.knowledge_base.signals.ingest_note_task.delay") as mock_delay:
        admin_instance.mark_published(MagicMock(), Note.objects.filter(pk=note.pk))

    note.refresh_from_db()
    assert note.status == Note.Status.PUBLISHED
    mock_delay.assert_called_once_with(str(note.id))


@pytest.mark.django_db
def test_admin_mark_draft_action(subject):
    note = Note.objects.create(
        subject=subject, title="X", content="y", status=Note.Status.PUBLISHED
    )
    admin_instance = NoteAdmin(Note, None)

    admin_instance.mark_draft(MagicMock(), Note.objects.filter(pk=note.pk))

    note.refresh_from_db()
    assert note.status == Note.Status.DRAFT
