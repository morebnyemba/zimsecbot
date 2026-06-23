import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.analytics.models import TopicPerformance
from apps.subjects.models import Subject, Topic

from .models import School, SchoolSeat

User = get_user_model()


@pytest.fixture
def school_admin(db):
    return User.objects.create_user(
        email="admin@school.com", password="testpass123", role=User.Role.SCHOOL_ADMIN
    )


@pytest.fixture
def client(school_admin):
    api = APIClient()
    api.force_authenticate(user=school_admin)
    return api


@pytest.mark.django_db
def test_school_create_and_list(client, school_admin):
    response = client.post("/api/v1/schools/", {"name": "Harare High", "seat_count": 50})
    assert response.status_code == 201
    assert response.data["name"] == "Harare High"

    response = client.get("/api/v1/schools/")
    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_add_seat_to_school(client, school_admin):
    school = School.objects.create(name="Harare High", admin_user=school_admin, seat_count=50)
    student = User.objects.create_user(email="kid@example.com", password="testpass123")

    response = client.post(f"/api/v1/schools/{school.id}/seats/", {"user_id": str(student.id)})

    assert response.status_code == 201
    assert SchoolSeat.objects.filter(school=school, user=student, is_active=True).exists()


@pytest.mark.django_db
def test_school_analytics_aggregates_seated_students(client, school_admin):
    school = School.objects.create(name="Harare High", admin_user=school_admin, seat_count=50)
    student = User.objects.create_user(email="kid@example.com", password="testpass123")
    SchoolSeat.objects.create(school=school, user=student, is_active=True)

    subject = Subject.objects.create(name="Biology", code="BIO", level=Subject.Level.O_LEVEL)
    topic = Topic.objects.create(subject=subject, name="Cells")
    TopicPerformance.objects.create(
        user=student, subject=subject, topic=topic, attempts_count=4, correct_count=1,
        accuracy=25.0,
    )

    response = client.get(f"/api/v1/schools/{school.id}/analytics/")

    assert response.status_code == 200
    assert response.data["student_count"] == 1
    assert response.data["average_accuracy"] == 25.0
    assert response.data["weak_topic_count"] == 1


@pytest.mark.django_db
def test_school_analytics_denied_for_non_admin(db):
    school_admin = User.objects.create_user(email="owner@school.com", password="testpass123")
    other_admin = User.objects.create_user(email="other@school.com", password="testpass123")
    school = School.objects.create(name="Harare High", admin_user=school_admin, seat_count=50)

    client = APIClient()
    client.force_authenticate(user=other_admin)
    response = client.get(f"/api/v1/schools/{school.id}/analytics/")

    assert response.status_code == 403
