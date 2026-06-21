import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.subjects.models import Subject

from .models import Question

User = get_user_model()


@pytest.fixture
def client(db):
    student = User.objects.create_user(email="student@example.com", password="testpass123")
    api = APIClient()
    api.force_authenticate(user=student)
    return api


@pytest.mark.django_db
def test_question_filter_by_difficulty(client):
    subject = Subject.objects.create(name="Physics", code="PHY", level=Subject.Level.O_LEVEL)
    Question.objects.create(
        subject=subject,
        question_type=Question.QuestionType.MCQ,
        difficulty=Question.Difficulty.EASY,
        question_text="Easy one",
        answer="A",
    )
    Question.objects.create(
        subject=subject,
        question_type=Question.QuestionType.MCQ,
        difficulty=Question.Difficulty.HARD,
        question_text="Hard one",
        answer="B",
    )

    response = client.get("/api/v1/questions/?difficulty=easy")
    assert response.status_code == 200
    assert response.data["count"] == 1
