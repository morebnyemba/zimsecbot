from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from apps.common.permissions import IsSuperadmin

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(generics.ListAPIView):
    queryset = AuditLog.objects.select_related("user").all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsSuperadmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["user", "action"]
