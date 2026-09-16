from django.db import models

from apps.common.models import BaseModel
from apps.subjects.models import Subject, Subtopic, Topic


class Note(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

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
    # PUBLISHED by default: existing notes (and anything created directly via
    # admin/API without touching this field) keep behaving exactly as before
    # -- immediately visible to students and indexed into the knowledge base.
    # Only the PDF/URL import pipeline explicitly creates DRAFT rows, so
    # messy extraction gets a review step instead of going straight to
    # students. See apps.knowledge_base.signals, which only indexes
    # PUBLISHED notes.
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PUBLISHED)
    # Where imported content came from: a URL, or the original uploaded
    # filename. Blank for hand-authored notes.
    source = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["title"]
        indexes = [models.Index(fields=["subject", "topic", "subtopic"])]

    def __str__(self):
        return self.title
