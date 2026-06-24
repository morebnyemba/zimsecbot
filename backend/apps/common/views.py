from django.core.cache import cache
from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Liveness/readiness probe: verifies the DB and cache are reachable."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        checks = {"database": self._check_database(), "cache": self._check_cache()}
        status_code = 200 if all(checks.values()) else 503
        return Response({"status": "ok" if status_code == 200 else "error", "checks": checks},
                         status=status_code)

    def _check_database(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception:
            return False

    def _check_cache(self):
        try:
            cache.set("health_check", "ok", timeout=5)
            return cache.get("health_check") == "ok"
        except Exception:
            return False
