from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Plan, Subscription
from apps.subjects.models import Subject

from .models import PastPaper

User = get_user_model()


@pytest.fixture
def student(db):
    return User.objects.create_user(email="student@example.com", password="testpass123")


@pytest.fixture
def client(student):
    api = APIClient()
    api.force_authenticate(user=student)
    return api


@pytest.mark.django_db
def test_paper_list_and_download_denied_on_free_plan(client, tmp_path, settings):
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
    assert response.status_code == 403


@pytest.mark.django_db
def test_paper_download_allowed_on_plus_plan(client, student, tmp_path, settings):
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
    plus = Plan.objects.get(code="plus")
    now = timezone.now()
    Subscription.objects.create(
        user=student,
        plan=plus,
        status=Subscription.Status.ACTIVE,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
    )

    response = client.get(f"/api/v1/papers/{paper.id}/download/")
    assert response.status_code == 200
    assert "file_url" in response.data
