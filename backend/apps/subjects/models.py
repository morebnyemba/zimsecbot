from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Subject(BaseModel):
    class Level(models.TextChoices):
        O_LEVEL = "o_level", "O-Level"
        A_LEVEL = "a_level", "A-Level"

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    level = models.CharField(max_length=20, choices=Level.choices)
    tier = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Topic(BaseModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="topics")
    name = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.subject.code} / {self.name}"


class Subtopic(BaseModel):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="subtopics")
    name = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.topic.name} / {self.name}"


class StudentSubject(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="selected_subjects"
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="students")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "subject"], name="unique_student_subject")
        ]

    def __str__(self):
        return f"{self.user_id} -> {self.subject.code}"
