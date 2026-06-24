from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.models import TopicPerformance

from .models import School, SchoolSeat
from .serializers import (
    AddSeatSerializer,
    SchoolAnalyticsSerializer,
    SchoolSeatSerializer,
    SchoolSerializer,
)

User = get_user_model()


class IsSchoolAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.admin_user_id == request.user.id


class SchoolListCreateView(generics.ListCreateAPIView):
    serializer_class = SchoolSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return School.objects.filter(admin_user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(admin_user=self.request.user)


class SchoolSeatListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSchoolAdmin]

    def get_school(self):
        school = get_object_or_404(School, pk=self.kwargs["school_id"])
        self.check_object_permissions(self.request, school)
        return school

    def get(self, request, school_id):
        school = self.get_school()
        seats = SchoolSeat.objects.filter(school=school)
        return Response(SchoolSeatSerializer(seats, many=True).data)

    def post(self, request, school_id):
        school = self.get_school()
        serializer = AddSeatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, pk=serializer.validated_data["user_id"])
        seat, _ = SchoolSeat.objects.update_or_create(
            school=school, user=user, defaults={"is_active": True}
        )
        return Response(SchoolSeatSerializer(seat).data, status=status.HTTP_201_CREATED)


class SchoolAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSchoolAdmin]

    def get(self, request, school_id):
        school = get_object_or_404(School, pk=school_id)
        self.check_object_permissions(request, school)

        student_ids = SchoolSeat.objects.filter(school=school, is_active=True).values_list(
            "user_id", flat=True
        )
        performances = TopicPerformance.objects.filter(user_id__in=student_ids)
        average_accuracy = performances.aggregate(avg=Avg("accuracy"))["avg"]
        weak_topic_count = performances.filter(accuracy__lt=60.0).count()

        data = {
            "student_count": student_ids.count(),
            "average_accuracy": average_accuracy,
            "weak_topic_count": weak_topic_count,
        }
        return Response(SchoolAnalyticsSerializer(data).data)
