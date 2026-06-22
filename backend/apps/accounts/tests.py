import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(email="student@example.com", password="testpass123")
    assert user.role == User.Role.STUDENT
    assert user.check_password("testpass123")
    assert not user.is_staff


@pytest.mark.django_db
def test_create_superuser():
    admin = User.objects.create_superuser(email="admin@example.com", password="testpass123")
    assert admin.role == User.Role.SUPERADMIN
    assert admin.is_staff
    assert admin.is_superuser


@pytest.mark.django_db
def test_student_profile_one_to_one():
    from apps.accounts.models import StudentProfile

    user = User.objects.create_user(email="profile@example.com", password="testpass123")
    profile = StudentProfile.objects.create(
        user=user, level=StudentProfile.Level.O_LEVEL, exam_year=2026
    )
    assert profile.user == user
    assert str(profile) == f"Profile<{user.email}>"


@pytest.mark.django_db
def test_register_endpoint():
    client = APIClient()
    response = client.post(
        "/api/v1/auth/register/",
        {"email": "new@example.com", "password": "testpass123"},
    )
    assert response.status_code == 201
    assert User.objects.filter(email="new@example.com").exists()


@pytest.mark.django_db
def test_my_profile_get_and_update():
    user = User.objects.create_user(email="me@example.com", password="testpass123")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/profile/me/")
    assert response.status_code == 200

    response = client.patch("/api/v1/profile/me/", {"school_name": "Harare High"})
    assert response.status_code == 200
    assert response.data["school_name"] == "Harare High"


@pytest.mark.django_db
def test_auth_me_returns_role():
    admin = User.objects.create_user(
        email="admin2@example.com", password="testpass123", role=User.Role.CONTENT_ADMIN
    )
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get("/api/v1/auth/me/")
    assert response.status_code == 200
    assert response.data["role"] == "content_admin"
    assert response.data["email"] == "admin2@example.com"


@pytest.mark.django_db
def test_logout_blacklists_refresh_token():
    from rest_framework_simplejwt.tokens import RefreshToken

    user = User.objects.create_user(email="out@example.com", password="testpass123")
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post("/api/v1/auth/logout/", {"refresh": str(refresh)})
    assert response.status_code == 205
