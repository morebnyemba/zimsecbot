from django.urls import path

from .views import SchoolAnalyticsView, SchoolListCreateView, SchoolSeatListCreateView

urlpatterns = [
    path("schools/", SchoolListCreateView.as_view(), name="school-list-create"),
    path(
        "schools/<uuid:school_id>/seats/", SchoolSeatListCreateView.as_view(), name="school-seats"
    ),
    path(
        "schools/<uuid:school_id>/analytics/",
        SchoolAnalyticsView.as_view(),
        name="school-analytics",
    ),
]
