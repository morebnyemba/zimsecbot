from django.urls import path

from .views import PlatformAnalyticsView, StudentAnalyticsView

urlpatterns = [
    path("admin/analytics/platform/", PlatformAnalyticsView.as_view(), name="platform-analytics"),
    path("analytics/me/", StudentAnalyticsView.as_view(), name="student-analytics"),
]
