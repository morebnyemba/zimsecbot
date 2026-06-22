from django.urls import path

from .views import PlatformAnalyticsView

urlpatterns = [
    path("admin/analytics/platform/", PlatformAnalyticsView.as_view(), name="platform-analytics"),
]
