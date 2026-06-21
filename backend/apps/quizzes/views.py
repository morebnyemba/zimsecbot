from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Quiz, QuizAttempt
from .serializers import (
    AttemptSubmitSerializer,
    QuizAttemptSerializer,
    QuizGenerateSerializer,
    QuizSerializer,
)


class QuizGenerateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = QuizGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quiz = services.generate_quiz(user=request.user, **serializer.validated_data)
        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)


class QuizDetailView(generics.RetrieveAPIView):
    queryset = Quiz.objects.prefetch_related("quiz_questions__question")
    serializer_class = QuizSerializer


class QuizAttemptSubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        quiz = generics.get_object_or_404(Quiz, pk=pk)
        serializer = AttemptSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt = services.submit_attempt(
            quiz=quiz, user=request.user, answers=serializer.validated_data["answers"]
        )
        return Response(QuizAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)


class MyQuizAttemptListView(generics.ListAPIView):
    serializer_class = QuizAttemptSerializer

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user).order_by("-started_at")


class QuizAttemptDetailView(generics.RetrieveAPIView):
    serializer_class = QuizAttemptSerializer

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)
