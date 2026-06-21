import pytest
from django.contrib.auth import get_user_model

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
