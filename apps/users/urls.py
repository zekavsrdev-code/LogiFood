from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    RoleProfileView,
    ChangePasswordView,
    ToggleAvailabilityView,
    ProfileListAPIView,
)

app_name = "users"

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/profile/", ProfileView.as_view(), name="profile"),
    path("auth/profile/role/", RoleProfileView.as_view(), name="role-profile"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("auth/toggle-availability/", ToggleAvailabilityView.as_view(), name="toggle-availability"),
    path("users/profiles/", ProfileListAPIView.as_view(), name="profile-list"),
]
