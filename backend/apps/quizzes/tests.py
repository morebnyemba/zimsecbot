import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.questions.models import Question
from apps.subjects.models import Subject

User = get_user_model()


@pytest.fixture
def student(db):
    return User.objects.create_user(email="student@example.com", password="testpass123")


@pytest.fixture
def client(student):
    api = APIClient()
    api.force_authenticate(user=student)
    return api


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Physics", code="PHY", level=Subject.Level.O_LEVEL)


@pytest.fixture
def questions(subject):
    return [
        Question.objects.create(
            subject=subject,
            question_type=Question.QuestionType.MCQ,
            question_text=f"Question {i}",
            answer="A",
            marks=2,
        )
        for i in range(3)
    ]


@pytest.mark.django_db
def test_generate_and_submit_quiz(client, subject, questions):
    response = client.post(
        "/api/v1/quizzes/generate/",
        {"subject_id": str(subject.id), "question_count": 3},
        format="json",
    )
    assert response.status_code == 201
    quiz_id = response.data["id"]
    assert len(response.data["quiz_questions"]) == 3

    answers = [
        {"question_id": q["id"], "student_answer": "A"} for q in response.data["quiz_questions"]
    ]
    response = client.post(
        f"/api/v1/quizzes/{quiz_id}/attempts/", {"answers": answers}, format="json"
    )
    assert response.status_code == 201
    assert response.data["score"] == 100.0
    assert response.data["marks_awarded"] == 6


@pytest.mark.django_db
def test_attempt_list_shows_own_attempts(client, subject, questions):
    response = client.post(
        "/api/v1/quizzes/generate/",
        {"subject_id": str(subject.id), "question_count": 1},
        format="json",
    )
    quiz_id = response.data["id"]
    client.post(f"/api/v1/quizzes/{quiz_id}/attempts/", {"answers": []}, format="json")

    response = client.get("/api/v1/quizzes/attempts/")
    assert response.status_code == 200
    assert response.data["count"] == 1
