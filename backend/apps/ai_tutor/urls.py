from django.urls import path

from .views import AskView, SessionMessageListView

urlpatterns = [
    path("ai-tutor/ask/", AskView.as_view(), name="ai-tutor-ask"),
    path(
        "ai-tutor/sessions/<uuid:session_id>/messages/",
        SessionMessageListView.as_view(),
        name="ai-tutor-session-messages",
    ),
]
