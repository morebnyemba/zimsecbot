import hashlib
import hmac

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .tasks import process_inbound_event


class WhatsAppWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge", "")
        if (
            mode == "subscribe"
            and settings.WHATSAPP_VERIFY_TOKEN
            and hmac.compare_digest(token or "", settings.WHATSAPP_VERIFY_TOKEN)
        ):
            return HttpResponse(challenge, content_type="text/plain")
        return HttpResponseForbidden()

    def post(self, request):
        if not self._verify_signature(request):
            return HttpResponseForbidden("Invalid signature")
        process_inbound_event.delay(request.data)
        return Response(status=status.HTTP_200_OK)

    def _verify_signature(self, request):
        secret = settings.WHATSAPP_APP_SECRET
        if not secret:
            return False
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not signature.startswith("sha256="):
            return False
        expected = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
        provided = signature.removeprefix("sha256=")
        return hmac.compare_digest(expected, provided)
