import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.subjects.models import Subject

from .models import AuditLog

User = get_user_model()


@pytest.fixture
def admin_client(db):
    admin = User.objects.create_user(
        email="admin@example.com", password="testpass123", role=User.Role.CONTENT_ADMIN
    )
    api = APIClient()
    api.force_authenticate(user=admin)
    return api, admin


@pytest.mark.django_db
def test_content_create_logs_audit_entry(admin_client):
    client, admin = admin_client
    response = client.post(
        "/api/v1/subjects/", {"name": "Chemistry", "code": "CHEM", "level": "o_level"}
    )
    assert response.status_code == 201
    assert AuditLog.objects.filter(user=admin, action="subject.create").exists()


@pytest.mark.django_db
def test_audit_log_list_requires_superadmin(admin_client):
    client, _ = admin_client
    response = client.get("/api/v1/admin/audit-logs/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_superadmin_can_list_audit_logs(db):
    superadmin = User.objects.create_superuser(email="root@example.com", password="testpass123")
    Subject.objects.create(name="Physics", code="PHY", level=Subject.Level.O_LEVEL)
    client = APIClient()
    client.force_authenticate(user=superadmin)
    response = client.get("/api/v1/admin/audit-logs/")
    assert response.status_code == 200
