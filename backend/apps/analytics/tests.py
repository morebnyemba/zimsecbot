from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.questions.models import Question
from apps.quizzes.models import Quiz, QuizAnswer, QuizAttempt
from apps.subjects.models import Subject, Topic

from . import services
from .models import Recommendation, TopicPerformance

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


@pytest.fixture
def student(db):
    return User.objects.create_user(email="student2@example.com", password="testpass123")


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Biology", code="BIO", level=Subject.Level.O_LEVEL)


@pytest.fixture
def topic(subject):
    return Topic.objects.create(subject=subject, name="Cells")


def _create_answered_attempt(student, subject, topic, *, correct_count, total_count):
    quiz = Quiz.objects.create(created_by=student, subject=subject)
    attempt = QuizAttempt.objects.create(
        quiz=quiz, user=student, score=0, completed_at=timezone.now()
    )
    for i in range(total_count):
        question = Question.objects.create(
            subject=subject,
            topic=topic,
            question_type=Question.QuestionType.MCQ,
            question_text=f"Q{i}",
            answer="A",
        )
        QuizAnswer.objects.create(
            attempt=attempt, question=question, is_correct=i < correct_count
        )
    return attempt


@pytest.mark.django_db
def test_recompute_topic_performance_computes_accuracy(student, subject, topic):
    _create_answered_attempt(student, subject, topic, correct_count=1, total_count=4)

    performances = services.recompute_topic_performance(student)

    assert len(performances) == 1
    assert performances[0].attempts_count == 4
    assert performances[0].correct_count == 1
    assert performances[0].accuracy == 25.0


@pytest.mark.django_db
def test_generate_recommendations_flags_weak_topics(student, subject, topic):
    performances = services.recompute_topic_performance(student)
    _create_answered_attempt(student, subject, topic, correct_count=1, total_count=4)
    performances = services.recompute_topic_performance(student)

    services.generate_recommendations(performances)

    assert Recommendation.objects.filter(user=student, topic=topic).exists()


@pytest.mark.django_db
def test_generate_recommendations_clears_when_no_longer_weak(student, subject, topic):
    performance = TopicPerformance.objects.create(
        user=student, subject=subject, topic=topic, attempts_count=5, correct_count=1, accuracy=20.0
    )
    services.generate_recommendations([performance])
    assert Recommendation.objects.filter(user=student, topic=topic).exists()

    performance.accuracy = 90.0
    performance.save()
    services.generate_recommendations([performance])

    assert not Recommendation.objects.filter(user=student, topic=topic).exists()


@pytest.mark.django_db
def test_update_study_streak_increments_on_consecutive_days(student):
    yesterday = timezone.localdate() - timedelta(days=1)
    services.update_study_streak(student, activity_date=yesterday)

    streak = services.update_study_streak(student, activity_date=timezone.localdate())

    assert streak.current_streak == 2
    assert streak.longest_streak == 2


@pytest.mark.django_db
def test_update_study_streak_resets_after_gap(student):
    services.update_study_streak(student, activity_date=timezone.localdate() - timedelta(days=5))

    streak = services.update_study_streak(student, activity_date=timezone.localdate())

    assert streak.current_streak == 1


@pytest.mark.django_db
@patch("apps.analytics.signals.recompute_user_analytics_task.delay")
def test_quiz_attempt_completion_triggers_analytics_recompute(mock_delay, student, subject):
    quiz = Quiz.objects.create(created_by=student, subject=subject)
    attempt = QuizAttempt.objects.create(quiz=quiz, user=student, score=0)
    mock_delay.assert_not_called()

    attempt.completed_at = timezone.now()
    attempt.save()

    mock_delay.assert_called_once_with(str(student.id))


@pytest.mark.django_db
def test_student_analytics_view_returns_own_data(student, subject, topic):
    TopicPerformance.objects.create(
        user=student, subject=subject, topic=topic, attempts_count=4, correct_count=1, accuracy=25.0
    )
    client = APIClient()
    client.force_authenticate(user=student)

    response = client.get("/api/v1/analytics/me/")

    assert response.status_code == 200
    assert len(response.data["topic_performance"]) == 1
    assert response.data["topic_performance"][0]["accuracy"] == 25.0
