from django.db import models
from pgvector.django import VectorField

from apps.common.models import BaseModel
from apps.notes.models import Note
from apps.subjects.models import Subject, Subtopic, Topic

EMBEDDING_DIMENSIONS = 768


class KnowledgeDocument(BaseModel):
    class SourceType(models.TextChoices):
        NOTE = "note", "Note"

    source_type = models.CharField(
        max_length=20, choices=SourceType.choices, default=SourceType.NOTE
    )
    note = models.OneToOneField(
        Note, on_delete=models.CASCADE, related_name="knowledge_document", null=True, blank=True
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="knowledge_documents"
    )
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name="knowledge_documents", null=True, blank=True
    )
    subtopic = models.ForeignKey(
        Subtopic,
        on_delete=models.CASCADE,
        related_name="knowledge_documents",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    indexed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["subject", "topic", "subtopic"])]

    def __str__(self):
        return self.title


class KnowledgeChunk(BaseModel):
    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    text = models.TextField()
    embedding = VectorField(dimensions=EMBEDDING_DIMENSIONS, null=True, blank=True)

    class Meta:
        ordering = ["document", "chunk_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "chunk_index"], name="unique_chunk_index_per_document"
            )
        ]

    def __str__(self):
        return f"{self.document.title} [{self.chunk_index}]"
