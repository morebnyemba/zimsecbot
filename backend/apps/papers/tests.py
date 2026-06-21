import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.subjects.models import Subject

from .models import PastPaper

User = get_user_model()


@pytest.fixture
def client(db):
    student = User.objects.create_user(email="student@example.com", password="testpass123")
    api = APIClient()
    api.force_authenticate(user=student)
    return api


@pytest.mark.django_db
def test_paper_list_and_download(client, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    subject = Subject.objects.create(name="Physics", code="PHY", level=Subject.Level.O_LEVEL)
    paper = PastPaper.objects.create(
        subject=subject,
        year=2023,
        session=PastPaper.Session.JUNE,
        paper_number=1,
        paper_type=PastPaper.PaperType.MULTIPLE_CHOICE,
        file=SimpleUploadedFile("paper.pdf", b"content"),
    )

    response = client.get("/api/v1/papers/?subject=" + str(subject.id))
    assert response.status_code == 200
    assert response.data["count"] == 1

    response = client.get(f"/api/v1/papers/{paper.id}/download/")
    assert response.status_code == 200
    assert "file_url" in response.data
