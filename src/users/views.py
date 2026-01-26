"""
User authentication and profile management views.

All views use DRF generic views following best practices:
- CreateAPIView for POST operations
- UpdateAPIView for PUT/PATCH operations
- RetrieveUpdateAPIView for GET/PUT/PATCH operations
- GenericAPIView only when custom logic is required
"""
from rest_framework import status, generics
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
# AUTHENTICATION VIEWS
# =============================================================================


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    
    Supports role-based registration for SUPPLIER, SELLER, and DRIVER.
    Returns JWT tokens upon successful registration.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Handle user registration and return JWT tokens."""
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


class LoginView(generics.CreateAPIView):
    """
    User login endpoint.
    
    Authenticates user with username and password.
    Returns JWT access and refresh tokens upon successful authentication.
    """
    serializer_class = LoginInputSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Handle user login and return JWT tokens."""
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


class LogoutView(generics.CreateAPIView):
    """
    User logout endpoint.
    
    Blacklists the provided refresh token to invalidate the session.
    """
    serializer_class = LogoutInputSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Handle user logout by blacklisting refresh token."""
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
# PROFILE VIEWS
# =============================================================================


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    User profile management endpoint.
    
    GET: Retrieve current user's profile information
    PUT/PATCH: Update current user's profile information
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on request method."""
        if self.request.method in ["PUT", "PATCH"]:
            return ProfileUpdateInputSerializer
        return UserWithProfileSerializer

    def get_object(self):
        """Return the current authenticated user."""
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        """Retrieve current user's profile."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Profile information")

    def update(self, request, *args, **kwargs):
        """Update current user's profile."""
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
    """
    Role-based profile management endpoint.
    
    GET: Retrieve role-specific profile (Supplier/Seller/Driver)
    PUT/PATCH: Update role-specific profile
    
    Automatically determines profile type based on user's role.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SupplierProfileSerializer  # Default for schema introspection

    def get_serializer_class(self):
        """Return appropriate serializer based on user's role."""
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
        """Return the role-specific profile for current user."""
        user = self.request.user
        if user.is_supplier:
            return user.supplier_profile
        if user.is_seller:
            return user.seller_profile
        if user.is_driver:
            return user.driver_profile
        return None

    def retrieve(self, request, *args, **kwargs):
        """Retrieve role-specific profile."""
        instance = self.get_object()
        if instance is None:
            return error_response(
                message="Profile not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Role profile")

    def update(self, request, *args, **kwargs):
        """Update role-specific profile."""
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


class ChangePasswordView(generics.UpdateAPIView):
    """
    Password change endpoint.
    
    PUT/PATCH: Change user's password after validating old password.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Return the current authenticated user."""
        return self.request.user

    def update(self, request, *args, **kwargs):
        """Handle password change with old password validation."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Password change failed",
                errors=serializer.errors,
            )

        user = self.get_object()
        if not user.check_password(serializer.validated_data["old_password"]):
            return error_response(
                message="Current password is incorrect",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return success_response(message="Password changed successfully")


class ToggleAvailabilityView(generics.UpdateAPIView):
    """
    Driver availability toggle endpoint.
    
    PUT/PATCH: Toggle driver's availability status (available ↔ busy).
    Only accessible by drivers.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer  # No body required; for schema introspection

    def get_object(self):
        """Return the current driver's profile."""
        user = self.request.user
        if not user.is_driver:
            return None
        return user.driver_profile

    def update(self, request, *args, **kwargs):
        """Toggle driver availability status."""
        driver_profile = self.get_object()
        if driver_profile is None:
            return error_response(
                message="This operation is only for drivers",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        driver_profile.is_available = not driver_profile.is_available
        driver_profile.save()

        status_text = "available" if driver_profile.is_available else "busy"
        return success_response(
            data={"is_available": driver_profile.is_available},
            message=f'Your status has been updated to "{status_text}"',
        )
