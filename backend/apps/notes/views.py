from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from apps.common.permissions import IsContentAdmin

from .models import Note
from .serializers import NoteSerializer


class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.select_related("subject", "topic", "subtopic").all()
    serializer_class = NoteSerializer
    permission_classes = [IsContentAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["subject", "topic", "subtopic"]
    search_fields = ["title", "content"]
