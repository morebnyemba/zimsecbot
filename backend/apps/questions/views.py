from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from apps.common.permissions import IsContentAdmin

from .models import Question
from .serializers import QuestionSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.select_related("subject", "topic").all()
    serializer_class = QuestionSerializer
    permission_classes = [IsContentAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["subject", "topic", "difficulty", "question_type"]
