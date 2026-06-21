import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.subjects.models import Subject

User = get_user_model()


@pytest.mark.django_db
def test_platform_analytics_counts():
    admin = User.objects.create_user(
        email="admin@example.com", password="testpass123", role=User.Role.CONTENT_ADMIN
    )
    Subject.objects.create(name="Physics", code="PHY", level=Subject.Level.O_LEVEL)
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get("/api/v1/admin/analytics/platform/")
    assert response.status_code == 200
    assert response.data["total_subjects"] == 1


@pytest.mark.django_db
def test_platform_analytics_denied_for_student():
    student = User.objects.create_user(email="student@example.com", password="testpass123")
    client = APIClient()
    client.force_authenticate(user=student)

    response = client.get("/api/v1/admin/analytics/platform/")
    assert response.status_code == 403
