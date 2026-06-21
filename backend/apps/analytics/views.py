from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsContentAdminOrSuperadmin
from apps.notes.models import Note
from apps.papers.models import PastPaper
from apps.questions.models import Question
from apps.quizzes.models import Quiz, QuizAttempt
from apps.subjects.models import Subject

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
