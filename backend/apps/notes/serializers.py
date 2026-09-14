from rest_framework import serializers

from .models import Note


class NoteSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    topic_name = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = [
            "id", "subject", "subject_name", "subject_code", "topic", "topic_name",
            "subtopic", "title", "content", "media",
        ]

    def get_topic_name(self, obj):
        return obj.topic.name if obj.topic_id else None