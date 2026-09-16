from rest_framework import serializers

from apps.subjects.models import Subject, Subtopic, Topic

from .models import Note


class NoteImportSerializer(serializers.Serializer):
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    topic = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(), required=False, allow_null=True
    )
    subtopic = serializers.PrimaryKeyRelatedField(
        queryset=Subtopic.objects.all(), required=False, allow_null=True
    )
    title = serializers.CharField(max_length=255)
    source_file = serializers.FileField(required=False)
    source_url = serializers.URLField(required=False)

    def validate(self, attrs):
        has_file = bool(attrs.get("source_file"))
        has_url = bool(attrs.get("source_url"))
        if not has_file and not has_url:
            raise serializers.ValidationError("Provide either source_file or source_url.")
        if has_file and has_url:
            raise serializers.ValidationError("Provide only one of source_file or source_url.")
        return attrs


class NoteSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    topic_name = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = [
            "id", "subject", "subject_name", "subject_code", "topic", "topic_name",
            "subtopic", "title", "content", "media", "status", "source",
        ]

    def get_topic_name(self, obj):
        return obj.topic.name if obj.topic_id else None