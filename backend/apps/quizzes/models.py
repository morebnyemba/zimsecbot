from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.questions.models import Question
from apps.subjects.models import Subject, Topic


class Quiz(BaseModel):
    class SourceChannel(models.TextChoices):
        WEB = "web", "Web"
        WHATSAPP = "whatsapp", "WhatsApp"

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quizzes"
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="quizzes")
    topic = models.ForeignKey(
        Topic, on_delete=models.SET_NULL, related_name="quizzes", null=True, blank=True
    )
    difficulty = models.CharField(max_length=10, blank=True)
    source_channel = models.CharField(
        max_length=20, choices=SourceChannel.choices, default=SourceChannel.WEB
    )
    questions = models.ManyToManyField(Question, through="QuizQuestion", related_name="quizzes")

    def __str__(self):
        return f"Quiz<{self.id}> {self.subject.code}"


class QuizQuestion(BaseModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="quiz_questions")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["quiz", "question"], name="unique_quiz_question")
        ]


class QuizAttempt(BaseModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    score = models.FloatField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "quiz"]),
            models.Index(fields=["user", "completed_at"]),
        ]

    def __str__(self):
        return f"Attempt<{self.id}> user={self.user_id} score={self.score}"


class QuizAnswer(BaseModel):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="quiz_answers")
    student_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    marks_awarded = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["attempt", "question"], name="unique_attempt_question")
        ]
