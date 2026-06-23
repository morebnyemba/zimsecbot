from django.contrib.auth import get_user_model
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsContentAdminOrSuperadmin
from apps.notes.models import Note
from apps.papers.models import PastPaper
from apps.questions.models import Question
from apps.quizzes.models import Quiz, QuizAttempt
from apps.subjects.models import Subject

from .models import Recommendation, StudyStreak, TopicPerformance
from .serializers import (
    RecommendationSerializer,
    StudyStreakSerializer,
    TopicPerformanceSerializer,
)

User = get_user_model()


class PlatformAnalyticsView(APIView):
    permission_classes = [IsContentAdminOrSuperadmin]

    def get(self, request):
        return Response(
            {
                "total_students": User.objects.filter(role=User.Role.STUDENT).count(),
                "total_subjects": Subject.objects.filter(is_active=True).count(),
                "total_papers": PastPaper.objects.count(),
                "total_notes": Note.objects.count(),
                "total_questions": Question.objects.count(),
                "total_quizzes": Quiz.objects.count(),
                "total_quiz_attempts": QuizAttempt.objects.count(),
            }
        )


class StudentAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        performances = TopicPerformance.objects.filter(user=user).select_related(
            "subject", "topic"
        )
        recommendations = Recommendation.objects.filter(user=user).select_related(
            "subject", "topic"
        )
        streak = StudyStreak.objects.filter(user=user).first()
        recent_scores = list(
            QuizAttempt.objects.filter(user=user, completed_at__isnull=False)
            .order_by("-completed_at")
            .values_list("score", flat=True)[:5]
        )

        return Response(
            {
                "topic_performance": TopicPerformanceSerializer(performances, many=True).data,
                "recommendations": RecommendationSerializer(recommendations, many=True).data,
                "streak": StudyStreakSerializer(streak).data if streak else None,
                "recent_scores": recent_scores,
            }
        )
