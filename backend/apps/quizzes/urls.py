from django.urls import path

from .views import (
    MyQuizAttemptListView,
    QuizAttemptDetailView,
    QuizAttemptSubmitView,
    QuizDetailView,
    QuizGenerateView,
)

urlpatterns = [
    path("quizzes/generate/", QuizGenerateView.as_view(), name="quiz-generate"),
    path("quizzes/<uuid:pk>/", QuizDetailView.as_view(), name="quiz-detail"),
    path(
        "quizzes/<uuid:pk>/attempts/",
        QuizAttemptSubmitView.as_view(),
        name="quiz-attempt-submit",
    ),
    path("quizzes/attempts/", MyQuizAttemptListView.as_view(), name="quiz-attempt-list"),
    path(
        "quizzes/attempts/<uuid:pk>/",
        QuizAttemptDetailView.as_view(),
        name="quiz-attempt-detail",
    ),
]
