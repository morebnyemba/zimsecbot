from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from apps.quizzes.models import QuizAnswer

from .models import Recommendation, StudyStreak, TopicPerformance

WEAK_TOPIC_ACCURACY_THRESHOLD = 60.0
MIN_ATTEMPTS_FOR_RECOMMENDATION = 3


def recompute_topic_performance(user) -> list[TopicPerformance]:
    rows = (
        QuizAnswer.objects.filter(attempt__user=user, question__topic__isnull=False)
        .values("question__subject_id", "question__topic_id")
        .annotate(attempts=Count("id"), correct=Count("id", filter=Q(is_correct=True)))
    )

    performances = []
    for row in rows:
        attempts = row["attempts"]
        accuracy = (row["correct"] / attempts * 100) if attempts else 0.0
        performance, _ = TopicPerformance.objects.update_or_create(
            user=user,
            subject_id=row["question__subject_id"],
            topic_id=row["question__topic_id"],
            defaults={
                "attempts_count": attempts,
                "correct_count": row["correct"],
                "accuracy": accuracy,
            },
        )
        performances.append(performance)
    return performances


def generate_recommendations(performances: list[TopicPerformance]):
    for performance in performances:
        is_weak = (
            performance.attempts_count >= MIN_ATTEMPTS_FOR_RECOMMENDATION
            and performance.accuracy < WEAK_TOPIC_ACCURACY_THRESHOLD
        )
        if is_weak:
            Recommendation.objects.update_or_create(
                user=performance.user,
                topic=performance.topic,
                defaults={
                    "subject": performance.subject,
                    "reason": Recommendation.Reason.WEAK_TOPIC,
                    "message": (
                        f"Revise {performance.topic.name} — your accuracy is "
                        f"{performance.accuracy:.0f}%."
                    ),
                },
            )
        else:
            Recommendation.objects.filter(user=performance.user, topic=performance.topic).delete()


def update_study_streak(user, activity_date=None) -> StudyStreak:
    activity_date = activity_date or timezone.localdate()
    streak, _ = StudyStreak.objects.get_or_create(user=user)

    if streak.last_activity_date == activity_date:
        return streak

    if streak.last_activity_date == activity_date - timedelta(days=1):
        streak.current_streak += 1
    else:
        streak.current_streak = 1

    streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    streak.last_activity_date = activity_date
    streak.save(update_fields=["current_streak", "longest_streak", "last_activity_date"])
    return streak


def recompute_user_analytics(user):
    performances = recompute_topic_performance(user)
    generate_recommendations(performances)
    update_study_streak(user)
