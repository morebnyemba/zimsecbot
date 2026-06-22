from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from . import services
from .models import AISession, Message
from .serializers import AskResponseSerializer, AskSerializer, MessageSerializer


class AskView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_tutor"

    def post(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        session_id = data.get("session_id")
        if session_id:
            session = generics.get_object_or_404(AISession, pk=session_id, user=request.user)
        else:
            session = AISession.objects.create(user=request.user, channel=AISession.Channel.WEB)

        result = services.ask(
            session,
            data["question"],
            subject_id=data.get("subject_id"),
            topic_id=data.get("topic_id"),
        )
        response = {"session_id": session.id, **result}
        return Response(AskResponseSerializer(response).data, status=status.HTTP_200_OK)


class SessionMessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        return Message.objects.filter(
            session_id=self.kwargs["session_id"], session__user=self.request.user
        )
