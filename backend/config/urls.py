from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/login/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("api/v1/auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.subjects.urls")),
    path("api/v1/", include("apps.papers.urls")),
    path("api/v1/", include("apps.notes.urls")),
    path("api/v1/", include("apps.questions.urls")),
    path("api/v1/", include("apps.quizzes.urls")),
    path("api/v1/", include("apps.audit.urls")),
    path("api/v1/", include("apps.analytics.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
