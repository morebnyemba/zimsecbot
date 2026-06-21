from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import StudentProfile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "phone_number", "password", "first_name", "last_name"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class StudentProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = StudentProfile
        fields = ["email", "level", "exam_year", "school_name", "preferences"]
