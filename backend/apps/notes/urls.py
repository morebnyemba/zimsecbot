from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import NoteImportView, NoteViewSet

router = DefaultRouter()
router.register("notes", NoteViewSet, basename="note")

urlpatterns = [
    # Must precede router.urls: the router's detail route (`notes/<pk>/`)
    # matches any non-slash segment by default, so "import" would otherwise
    # be swallowed as a (nonexistent) note pk instead of reaching this view.
    path("notes/import/", NoteImportView.as_view(), name="note-import"),
] + router.urls
