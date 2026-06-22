from rest_framework.routers import DefaultRouter

from .views import MarkingSchemeViewSet, PastPaperViewSet

router = DefaultRouter()
router.register("papers", PastPaperViewSet, basename="paper")
router.register("marking-schemes", MarkingSchemeViewSet, basename="marking-scheme")

urlpatterns = router.urls
