from rest_framework.routers import DefaultRouter

from .views import PastPaperViewSet

router = DefaultRouter()
router.register("papers", PastPaperViewSet, basename="paper")

urlpatterns = router.urls
