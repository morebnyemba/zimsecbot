from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.mixins import AuditLoggedViewSetMixin
from apps.common.permissions import IsContentAdmin, IsContentAdminOrSuperadmin

from .ingestion import ExtractionError, extract_pdf_text, extract_url_text
from .models import Note
from .serializers import NoteImportSerializer, NoteSerializer


class NoteViewSet(AuditLoggedViewSetMixin, viewsets.ModelViewSet):
    queryset = Note.objects.select_related("subject", "topic", "subtopic").all()
    serializer_class = NoteSerializer
    permission_classes = [IsContentAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["subject", "topic", "subtopic", "status"]
    search_fields = ["title", "content"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        # Content admins/superadmins need to see drafts to review them (e.g.
        # freshly PDF/URL-imported notes); everyone else -- students -- only
        # ever sees published notes.
        if user.is_authenticated and user.role in (
            user.Role.CONTENT_ADMIN,
            user.Role.SUPERADMIN,
        ):
            return queryset
        return queryset.filter(status=Note.Status.PUBLISHED)


class NoteImportView(APIView):
    """Extracts text from an uploaded PDF or a web page URL into a draft Note.

    Never embeds anything into the knowledge base directly -- that only
    happens once a content admin reviews the draft and flips its status to
    published (see apps.knowledge_base.signals).
    """

    permission_classes = [IsContentAdminOrSuperadmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = NoteImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            if data.get("source_file"):
                content = extract_pdf_text(data["source_file"])
                source = data["source_file"].name
            else:
                content = extract_url_text(data["source_url"])
                source = data["source_url"]
        except ExtractionError as exc:
            return Response(
                {"error": {"code": "extraction_failed", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        note = Note.objects.create(
            subject=data["subject"],
            topic=data.get("topic"),
            subtopic=data.get("subtopic"),
            title=data["title"],
            content=content,
            status=Note.Status.DRAFT,
            source=source,
        )
        return Response(NoteSerializer(note).data, status=status.HTTP_201_CREATED)
