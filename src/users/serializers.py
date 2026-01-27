from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import extend_schema_field

from .models import User, SupplierProfile, SellerProfile, DriverProfile


class UserSerializer(serializers.ModelSerializer):
    """User Serializer"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 
            'phone_number', 'avatar', 'role', 'role_display', 
            'is_verified', 'created_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at', 'role']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration request - role-based (SUPPLIER, SELLER, DRIVER)."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
        help_text="Password",
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        label="Password confirmation",
        style={"input_type": "password"},
        help_text="Password confirmation",
    )
    role = serializers.ChoiceField(
        choices=User.Role.choices,
        required=True,
        help_text="Role: SUPPLIER, SELLER, DRIVER",
    )
    
    # Fields for Supplier
    company_name = serializers.CharField(required=False, allow_blank=True)
    
    # Fields for Seller
    business_name = serializers.CharField(required=False, allow_blank=True)
    business_type = serializers.CharField(required=False, allow_blank=True)
    
    # Fields for Driver
    license_number = serializers.CharField(required=False, allow_blank=True)
    vehicle_type = serializers.ChoiceField(choices=DriverProfile.VehicleType.choices, required=False)
    vehicle_plate = serializers.CharField(required=False, allow_blank=True)
    
    # Common fields
    address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2', 'first_name', 'last_name', 
            'phone_number', 'role',
            # Role-based fields
            'company_name', 'business_name', 'business_type',
            'license_number', 'vehicle_type', 'vehicle_plate',
            'address', 'city'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        
        role = attrs.get('role')
        
        # Role-based required field validation
        if role == User.Role.SUPPLIER:
            if not attrs.get('company_name'):
                raise serializers.ValidationError({"company_name": "Company name is required for suppliers."})
        
        elif role == User.Role.SELLER:
            if not attrs.get('business_name'):
                raise serializers.ValidationError({"business_name": "Business name is required for sellers."})
        
        elif role == User.Role.DRIVER:
            if not attrs.get('license_number'):
                raise serializers.ValidationError({"license_number": "License number is required for drivers."})
        
        return attrs
    
    def create(self, validated_data):
        """
        Create user with role-based profile.
        
        Delegates to UserService for business logic.
        """
        from .services import UserService
        return UserService.register_user(validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    """Password change request."""

    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text="Current password",
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
        help_text="New password",
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
        label="New password confirmation",
        style={"input_type": "password"},
        help_text="New password confirmation",
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        return attrs


# ==================== AUTH SERIALIZERS ====================

class LoginInputSerializer(serializers.Serializer):
    """Login request - username and password."""

    username = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="Username",
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text="Password",
    )


class LogoutInputSerializer(serializers.Serializer):
    """Logout request - refresh token for logout."""

    refresh_token = serializers.CharField(
        required=True,
        help_text="JWT refresh token (will be invalidated for logout)",
    )


class ProfileUpdateInputSerializer(serializers.Serializer):
    """Profile update request - supports partial updates."""

    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True)


# ==================== PROFILE SERIALIZERS ====================

class SupplierProfileSerializer(serializers.ModelSerializer):
    """Supplier Profile Serializer"""
    username = serializers.CharField(source='user.username', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    
    class Meta:
        model = SupplierProfile
        fields = [
            'id', 'username', 'phone_number', 'company_name', 'tax_number',
            'address', 'city', 'description', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SellerProfileSerializer(serializers.ModelSerializer):
    """Seller Profile Serializer"""
    username = serializers.CharField(source='user.username', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    
    class Meta:
        model = SellerProfile
        fields = [
            'id', 'username', 'phone_number', 'business_name', 'business_type',
            'tax_number', 'address', 'city', 'description', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DriverProfileSerializer(serializers.ModelSerializer):
    """Driver Profile Serializer"""
    username = serializers.CharField(source='user.username', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    vehicle_type_display = serializers.CharField(source='get_vehicle_type_display', read_only=True)
    
    class Meta:
        model = DriverProfile
        fields = [
            'id', 'username', 'phone_number', 'license_number', 'vehicle_type',
            'vehicle_type_display', 'vehicle_plate', 'city', 'is_available', 
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserWithProfileSerializer(serializers.ModelSerializer):
    """User and Profile Serializer - with detailed profile information."""

    role_display = serializers.CharField(source="get_role_display", read_only=True)
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "role",
            "role_display",
            "is_verified",
            "profile",
            "created_at",
        ]
        read_only_fields = ["id", "is_verified", "created_at", "role"]

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_profile(self, obj):
        if obj.role == User.Role.SUPPLIER and hasattr(obj, "supplier_profile"):
            return SupplierProfileSerializer(obj.supplier_profile).data
        if obj.role == User.Role.SELLER and hasattr(obj, "seller_profile"):
            return SellerProfileSerializer(obj.seller_profile).data
        if obj.role == User.Role.DRIVER and hasattr(obj, "driver_profile"):
            return DriverProfileSerializer(obj.driver_profile).data
        return None
