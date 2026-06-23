from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.subjects.models import Subject, Topic


class TopicPerformance(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topic_performances"
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="topic_performances"
    )
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name="topic_performances"
    )
    attempts_count = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    accuracy = models.FloatField(default=0.0)

    class Meta:
        ordering = ["subject", "topic"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "subject", "topic"], name="unique_topic_performance_per_user"
            )
        ]

    def __str__(self):
        return f"{self.user_id} / {self.topic.name}: {self.accuracy:.1f}%"


class StudyStreak(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_streak"
    )
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"StudyStreak<{self.user_id}> current={self.current_streak}"


class Recommendation(BaseModel):
    class Reason(models.TextChoices):
        WEAK_TOPIC = "weak_topic", "Weak Topic"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendations"
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="recommendations")
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="recommendations")
    reason = models.CharField(max_length=20, choices=Reason.choices, default=Reason.WEAK_TOPIC)
    message = models.TextField()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "topic"], name="unique_recommendation_per_user_topic"
            )
        ]

    def __str__(self):
        return f"Recommendation<{self.user_id}> {self.topic.name}"
