from django.db import models

from apps.common.models import BaseModel
from apps.subjects.models import Subject


class MarkingScheme(BaseModel):
    file = models.FileField(upload_to="marking_schemes/")

    def __str__(self):
        return f"MarkingScheme<{self.id}>"


class PastPaper(BaseModel):
    class PaperType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Multiple Choice"
        STRUCTURED = "structured", "Structured"
        PRACTICAL = "practical", "Practical"

    class Session(models.TextChoices):
        JUNE = "june", "June"
        NOVEMBER = "november", "November"

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="past_papers")
    year = models.PositiveIntegerField()
    session = models.CharField(max_length=20, choices=Session.choices)
    paper_number = models.PositiveSmallIntegerField()
    paper_type = models.CharField(max_length=30, choices=PaperType.choices)
    file = models.FileField(upload_to="past_papers/")
    marking_scheme = models.ForeignKey(
        MarkingScheme, on_delete=models.SET_NULL, null=True, blank=True, related_name="papers"
    )

    class Meta:
        ordering = ["-year", "session"]
        indexes = [models.Index(fields=["subject", "year", "paper_type"])]

    def __str__(self):
        return f"{self.subject.code} {self.year} {self.session} P{self.paper_number}"
