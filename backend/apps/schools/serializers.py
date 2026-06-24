from rest_framework import serializers

from .models import School, SchoolSeat


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ["id", "name", "admin_user", "seat_count"]
        read_only_fields = ["id", "admin_user"]


class SchoolSeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolSeat
        fields = ["id", "school", "user", "is_active"]
        read_only_fields = ["id", "school"]


class AddSeatSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()


class SchoolAnalyticsSerializer(serializers.Serializer):
    student_count = serializers.IntegerField()
    average_accuracy = serializers.FloatField(allow_null=True)
    weak_topic_count = serializers.IntegerField()
