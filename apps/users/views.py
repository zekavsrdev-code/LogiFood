"""User authentication and profile management views"""
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from apps.core.schema import openapi_parameters_from_filterset
from .models import User, SupplierProfile, SellerProfile, DriverProfile
from .serializers import (
    UserRegistrationSerializer,
    ChangePasswordSerializer,
    UserWithProfileSerializer,
    SupplierProfileSerializer,
    SellerProfileSerializer,
    DriverProfileSerializer,
    SupplierProfileListSerializer,
    DriverProfileListSerializer,
    SellerProfileListSerializer,
    LoginInputSerializer,
    ProfileUpdateInputSerializer,
)
from .filters import (
    ProfileListSchemaFilter,
    SupplierProfileListFilter,
    DriverProfileListFilter,
    SellerProfileListFilter,
)
from .services import UserService
from apps.core.serializers import EmptySerializer
from apps.core.utils import success_response, error_response
from apps.core.exceptions import BusinessLogicError
from apps.core.pagination import StandardResultsSetPagination
from apps.core.permissions import IsSupplier


# =============================================================================
# AUTHENTICATION VIEWS
# =============================================================================


class RegisterView(generics.CreateAPIView):
    """User registration endpoint"""
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
        token_data = UserService.get_or_create_token(user)
        return success_response(
            {
                "user": UserWithProfileSerializer(user).data,
                **token_data,
            },
            message="Registration successful",
            status_code=status.HTTP_201_CREATED,
        )


class LoginView(generics.GenericAPIView):
    """User login endpoint. POST with credentials, returns user + tokens."""
    serializer_class = LoginInputSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid request",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = UserService.authenticate_user(username, password)

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

        token_data = UserService.get_or_create_token(user)
        return success_response(
            {
                "user": UserWithProfileSerializer(user).data,
                **token_data,
            },
            message="Login successful",
        )


class LogoutView(generics.GenericAPIView):
    """User logout endpoint. POST with Authorization: Token <token> — deletes token."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        Token.objects.filter(user=request.user).delete()
        return success_response(message="Logout successful")


# =============================================================================
# PROFILE VIEWS
# =============================================================================


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile management endpoint"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
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
    """
    Role-based profile management endpoint.
    
    GET: Retrieve role-specific profile (Supplier/Seller/Driver)
    PUT/PATCH: Update role-specific profile
    
    Automatically determines profile type based on user's role.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SupplierProfileSerializer

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


class ChangePasswordView(generics.UpdateAPIView):
    """Password change endpoint"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
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
    """Driver availability toggle endpoint"""
    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer

    def get_object(self):
        user = self.request.user
        if not user.is_driver:
            return None
        return user.driver_profile

    def update(self, request, *args, **kwargs):
        """Toggle driver availability status."""
        user = request.user
        try:
            is_available = UserService.toggle_driver_availability(user)
            status_text = "available" if is_available else "busy"
            return success_response(
                data={"is_available": is_available},
                message=f'Your status has been updated to "{status_text}"',
            )
        except BusinessLogicError as e:
            return error_response(
                message=str(e.detail),
                status_code=e.status_code
            )


# =============================================================================
# PROFILE LIST (serializer + FilterSet by role)
# =============================================================================


@extend_schema(parameters=openapi_parameters_from_filterset(ProfileListSchemaFilter))
class ProfileListAPIView(generics.ListAPIView):
    """
    GET /api/users/profiles/?role=SUPPLIER|SELLER|DRIVER.
    Filters: city, search (SUPPLIER/SELLER), vehicle_type (DRIVER). Driven by serializers/filters.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]

    def list(self, request, *args, **kwargs):
        role = (request.query_params.get("role") or "").strip().upper()
        role_values = [c[0] for c in User.Role.choices]
        if role not in role_values:
            return error_response(
                message=f"Query param 'role' is required and must be one of: {', '.join(role_values)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message="Profiles listed successfully")

    def get_queryset(self):
        role = (self.request.query_params.get("role") or "").strip().upper()
        if role == User.Role.SUPPLIER:
            return (
                SupplierProfile.objects.filter(is_active=True)
                .select_related("user")
                .order_by("id")
            )
        if role == User.Role.DRIVER:
            return (
                DriverProfile.objects.filter(
                    is_active=True, is_available=True
                )
                .select_related("user")
                .order_by("id")
            )
        if role == User.Role.SELLER:
            return (
                SellerProfile.objects.filter(is_active=True)
                .select_related("user")
                .order_by("id")
            )
        return SupplierProfile.objects.none()

    def get_serializer_class(self):
        role = (self.request.query_params.get("role") or "").strip().upper()
        if role == User.Role.SUPPLIER:
            return SupplierProfileListSerializer
        if role == User.Role.DRIVER:
            return DriverProfileListSerializer
        if role == User.Role.SELLER:
            return SellerProfileListSerializer
        return SupplierProfileListSerializer

    def get_filterset_class(self):
        role = (self.request.query_params.get("role") or "").strip().upper()
        if role == User.Role.SUPPLIER:
            return SupplierProfileListFilter
        if role == User.Role.DRIVER:
            return DriverProfileListFilter
        if role == User.Role.SELLER:
            return SellerProfileListFilter
        return ProfileListSchemaFilter
