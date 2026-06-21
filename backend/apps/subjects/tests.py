import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from .models import Subject, Topic

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
def test_subject_list_visible_to_authenticated_student(client):
    Subject.objects.create(name="Physics", code="PHY", level=Subject.Level.O_LEVEL)
    response = client.get("/api/v1/subjects/")
    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_student_cannot_create_subject(client):
    response = client.post(
        "/api/v1/subjects/", {"name": "Chemistry", "code": "CHEM", "level": "o_level"}
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_subject_topics_endpoint(client):
    subject = Subject.objects.create(name="Physics", code="PHY", level=Subject.Level.O_LEVEL)
    Topic.objects.create(subject=subject, name="Mechanics", order=1)
    response = client.get(f"/api/v1/subjects/{subject.id}/topics/")
    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_select_and_remove_student_subject(client):
    subject = Subject.objects.create(name="Physics", code="PHY", level=Subject.Level.O_LEVEL)
    response = client.post("/api/v1/profile/me/subjects/", {"subject_id": str(subject.id)})
    assert response.status_code == 201

    response = client.delete(f"/api/v1/profile/me/subjects/{subject.id}/")
    assert response.status_code == 204
