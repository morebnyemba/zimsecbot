from rest_framework import serializers

from apps.subjects.models import Subject

from .models import MarkingScheme, PastPaper


class MarkingSchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarkingScheme
        fields = ["id", "file"]


class PastPaperSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    marking_scheme = serializers.PrimaryKeyRelatedField(
        queryset=MarkingScheme.objects.all(), required=False, allow_null=True
    )
    marking_scheme_detail = MarkingSchemeSerializer(source="marking_scheme", read_only=True)

    class Meta:
        model = PastPaper
        fields = [
            "id", "subject", "subject_name", "year", "session", "paper_number",
            "paper_type", "file", "marking_scheme", "marking_scheme_detail",
        ]
