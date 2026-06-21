from django.db import models

from apps.common.models import BaseModel
from apps.subjects.models import Subject, Topic


class Question(BaseModel):
    class QuestionType(models.TextChoices):
        MCQ = "mcq", "Multiple Choice"
        STRUCTURED = "structured", "Structured"
        ESSAY = "essay", "Essay"
        PRACTICAL = "practical", "Practical"

    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="questions")
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name="questions", null=True, blank=True
    )
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    difficulty = models.CharField(
        max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM
    )
    question_text = models.TextField()
    options = models.JSONField(default=list, blank=True)
    answer = models.TextField()
    explanation = models.TextField(blank=True)
    marks = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["subject", "topic", "difficulty", "question_type"]),
        ]

    def __str__(self):
        return f"{self.subject.code} [{self.question_type}] {self.question_text[:50]}"
