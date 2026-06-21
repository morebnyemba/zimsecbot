from django.db import models

from apps.common.models import BaseModel
from apps.subjects.models import Subject, Subtopic, Topic


class Note(BaseModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="notes")
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name="notes", null=True, blank=True
    )
    subtopic = models.ForeignKey(
        Subtopic, on_delete=models.CASCADE, related_name="notes", null=True, blank=True
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    media = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["title"]
        indexes = [models.Index(fields=["subject", "topic", "subtopic"])]

    def __str__(self):
        return self.title
