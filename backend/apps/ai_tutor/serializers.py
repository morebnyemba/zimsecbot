from rest_framework import serializers

from .models import AISession, Message


class AskSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=False)
    question = serializers.CharField()
    subject_id = serializers.UUIDField(required=False, allow_null=True)
    topic_id = serializers.UUIDField(required=False, allow_null=True)


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "sources", "created_at"]


class AskResponseSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    answer = serializers.CharField()
    sources = serializers.ListField()


class AISessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AISession
        fields = ["id", "channel", "created_at"]
