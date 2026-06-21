from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.response import Response

from apps.common.permissions import IsContentAdmin

from .models import StudentSubject, Subject, Subtopic, Topic
from .serializers import (
    StudentSubjectSerializer,
    SubjectSerializer,
    SubtopicSerializer,
    TopicSerializer,
)


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsContentAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tier", "level", "is_active"]


class SubjectTopicListView(generics.ListAPIView):
    serializer_class = TopicSerializer

    def get_queryset(self):
        return Topic.objects.filter(subject_id=self.kwargs["subject_id"])


class TopicSubtopicListView(generics.ListAPIView):
    serializer_class = SubtopicSerializer

    def get_queryset(self):
        return Subtopic.objects.filter(topic_id=self.kwargs["topic_id"])


class MyStudentSubjectsView(generics.ListCreateAPIView):
    serializer_class = StudentSubjectSerializer

    def get_queryset(self):
        return StudentSubject.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MyStudentSubjectDeleteView(generics.DestroyAPIView):
    serializer_class = StudentSubjectSerializer

    def get_queryset(self):
        return StudentSubject.objects.filter(user=self.request.user)

    def get_object(self):
        return self.get_queryset().get(subject_id=self.kwargs["subject_id"])

    def delete(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
