import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.subjects.models import Subject

from .models import Note

User = get_user_model()


@pytest.fixture
def client(db):
    student = User.objects.create_user(email="student@example.com", password="testpass123")
    api = APIClient()
    api.force_authenticate(user=student)
    return api


@pytest.mark.django_db
def test_notes_search(client):
    subject = Subject.objects.create(name="Physics", code="PHY", level=Subject.Level.O_LEVEL)
    Note.objects.create(subject=subject, title="Newton's Laws", content="F=ma")
    Note.objects.create(subject=subject, title="Thermodynamics", content="entropy")

    response = client.get("/api/v1/notes/?q=Newton")
    assert response.status_code == 200

    response = client.get("/api/v1/notes/?search=Newton")
    assert response.data["count"] == 1
