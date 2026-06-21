from django.urls import path

from .views import LogoutView, MyProfileView, RegisterView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("profile/me/", MyProfileView.as_view(), name="my-profile"),
]
