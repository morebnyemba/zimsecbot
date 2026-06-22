from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import AuditLoggedViewSetMixin
from apps.common.permissions import IsContentAdmin

from .models import MarkingScheme, PastPaper
from .serializers import MarkingSchemeSerializer, PastPaperSerializer


class MarkingSchemeViewSet(AuditLoggedViewSetMixin, viewsets.ModelViewSet):
    queryset = MarkingScheme.objects.all()
    serializer_class = MarkingSchemeSerializer
    permission_classes = [IsContentAdmin]


class PastPaperViewSet(AuditLoggedViewSetMixin, viewsets.ModelViewSet):
    queryset = PastPaper.objects.select_related("subject", "marking_scheme").all()
    serializer_class = PastPaperSerializer
    permission_classes = [IsContentAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["subject", "year", "paper_type", "session"]

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        paper = self.get_object()
        return Response({"file_url": request.build_absolute_uri(paper.file.url)})
