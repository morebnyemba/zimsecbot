from rest_framework import serializers

from .models import Recommendation, StudyStreak, TopicPerformance


class TopicPerformanceSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name")
    subject_code = serializers.CharField(source="subject.code")
    topic_name = serializers.CharField(source="topic.name")

    class Meta:
        model = TopicPerformance
        fields = [
            "id",
            "subject_id",
            "subject_name",
            "subject_code",
            "topic_id",
            "topic_name",
            "attempts_count",
            "correct_count",
            "accuracy",
        ]


class StudyStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyStreak
        fields = ["current_streak", "longest_streak", "last_activity_date"]


class RecommendationSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name")
    topic_name = serializers.CharField(source="topic.name")

    class Meta:
        model = Recommendation
        fields = [
            "id",
            "subject_id",
            "subject_name",
            "topic_id",
            "topic_name",
            "reason",
            "message",
            "created_at",
        ]
