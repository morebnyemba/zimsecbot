from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    MyStudentSubjectDeleteView,
    MyStudentSubjectsView,
    SubjectTopicListView,
    SubjectViewSet,
    TopicSubtopicListView,
)

router = DefaultRouter()
router.register("subjects", SubjectViewSet, basename="subject")

urlpatterns = [
    path(
        "subjects/<uuid:subject_id>/topics/",
        SubjectTopicListView.as_view(),
        name="subject-topics",
    ),
    path(
        "topics/<uuid:topic_id>/subtopics/",
        TopicSubtopicListView.as_view(),
        name="topic-subtopics",
    ),
    path("profile/me/subjects/", MyStudentSubjectsView.as_view(), name="my-subjects"),
    path(
        "profile/me/subjects/<uuid:subject_id>/",
        MyStudentSubjectDeleteView.as_view(),
        name="my-subject-delete",
    ),
] + router.urls
