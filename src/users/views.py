from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import User, SupplierProfile, SellerProfile, DriverProfile
from .serializers import (
    UserRegistrationSerializer,
    ChangePasswordSerializer,
    UserWithProfileSerializer,
    SupplierProfileSerializer,
    SellerProfileSerializer,
    DriverProfileSerializer,
    LoginInputSerializer,
    LogoutInputSerializer,
    ProfileUpdateInputSerializer,
)
from apps.core.serializers import EmptySerializer
from apps.core.utils import success_response, error_response


# =============================================================================
# AUTH
# =============================================================================


class RegisterView(generics.CreateAPIView):
    """Role-based user registration. SUPPLIER/SELLER/DRIVER."""

    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Registration failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return success_response(
            {
                "user": UserWithProfileSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            message="Registration successful",
            status_code=status.HTTP_201_CREATED,
        )


class LoginView(generics.GenericAPIView):
    """Login with username and password. Returns JWT access and refresh tokens."""

    serializer_class = LoginInputSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid request",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = authenticate(request, username=username, password=password)

        if user is None:
            return error_response(
                message="Invalid credentials",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return error_response(
                message="Account is not active",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return success_response(
            {
                "user": UserWithProfileSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            message="Login successful",
        )


class LogoutView(generics.GenericAPIView):
    """Logout with refresh token. Token is added to blacklist."""

    serializer_class = LogoutInputSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="refresh_token required",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(serializer.validated_data["refresh_token"])
            token.blacklist()
            return success_response(message="Logout successful")
        except Exception:
            return error_response(
                message="Invalid or expired token",
                status_code=status.HTTP_400_BAD_REQUEST,
            )


# =============================================================================
# PROFILE
# =============================================================================


class ProfileView(generics.RetrieveUpdateAPIView):
    """View (GET) and update (PUT) user profile."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "PUT":
            return ProfileUpdateInputSerializer
        return UserWithProfileSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Profile information")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=partial)
        if not serializer.is_valid():
            return error_response(
                message="Update failed",
                errors=serializer.errors,
            )

        for key, value in serializer.validated_data.items():
            setattr(instance, key, value)
        instance.save()

        return success_response(
            data=UserWithProfileSerializer(instance).data,
            message="Profile updated",
        )


class RoleProfileView(generics.RetrieveUpdateAPIView):
    """View and update role-based profile (Supplier/Seller/Driver)."""

    permission_classes = [IsAuthenticated]
    serializer_class = SupplierProfileSerializer  # Default (for schema introspection)

    def get_serializer_class(self):
        if not self.request.user.is_authenticated:
            return SupplierProfileSerializer
        user = self.request.user
        if user.is_supplier:
            return SupplierProfileSerializer
        if user.is_seller:
            return SellerProfileSerializer
        if user.is_driver:
            return DriverProfileSerializer
        return SupplierProfileSerializer

    def get_object(self):
        user = self.request.user
        if user.is_supplier:
            return user.supplier_profile
        if user.is_seller:
            return user.seller_profile
        if user.is_driver:
            return user.driver_profile
        return None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return error_response(
                message="Profile not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Role profile")

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return error_response(
                message="Profile not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        partial = kwargs.pop("partial", True)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return error_response(
                message="Update failed",
                errors=serializer.errors,
            )
        serializer.save()
        return success_response(data=serializer.data, message="Profile updated")


class ChangePasswordView(generics.GenericAPIView):
    """Change password. Old password is validated."""

    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Password change failed",
                errors=serializer.errors,
            )

        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return error_response(
                message="Current password is incorrect",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return success_response(message="Password changed successfully")


class ToggleAvailabilityView(generics.GenericAPIView):
    """Toggle driver availability status (available ↔ busy)."""

    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer  # No PUT body; for schema introspection

    def put(self, request):
        user = request.user
        if not user.is_driver:
            return error_response(
                message="This operation is only for drivers",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        driver_profile = user.driver_profile
        driver_profile.is_available = not driver_profile.is_available
        driver_profile.save()

        status_text = "available" if driver_profile.is_available else "busy"
        return success_response(
            data={"is_available": driver_profile.is_available},
            message=f'Your status has been updated to "{status_text}"',
        )
