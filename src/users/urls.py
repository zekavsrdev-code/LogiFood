from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    RoleProfileView,
    ChangePasswordView,
    ToggleAvailabilityView,
)

app_name = "users"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/role/", RoleProfileView.as_view(), name="role-profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("toggle-availability/", ToggleAvailabilityView.as_view(), name="toggle-availability"),
]
