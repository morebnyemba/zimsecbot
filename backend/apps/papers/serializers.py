from rest_framework import serializers

from .models import MarkingScheme, PastPaper


class MarkingSchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarkingScheme
        fields = ["id", "file"]


class PastPaperSerializer(serializers.ModelSerializer):
    subject = serializers.CharField(source="subject.name", read_only=True)
    marking_scheme = MarkingSchemeSerializer(read_only=True)

    class Meta:
        model = PastPaper
        fields = [
            "id", "subject", "year", "session", "paper_number", "paper_type",
            "file", "marking_scheme",
        ]
