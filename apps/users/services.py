from typing import Optional, List, Dict, Any
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from apps.core.services import BaseService
from apps.core.exceptions import BusinessLogicError
from rest_framework import status

User = get_user_model()


class UserService(BaseService):
    """User service for user-related operations"""
    model = User
    
    @classmethod
    def get_by_email(cls, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            return cls.model.objects.get(email=email)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def verify_user(cls, user: User) -> User:
        """Verify user account"""
        user.is_verified = True
        user.save()
        return user
    
    @classmethod
    def register_user(cls, validated_data: dict) -> User:
        """Register a new user with role-based profile"""
        from .models import SupplierProfile, SellerProfile, DriverProfile
        
        password2 = validated_data.pop('password2', None)
        company_name = validated_data.pop('company_name', None)
        business_name = validated_data.pop('business_name', None)
        business_type = validated_data.pop('business_type', None)
        license_number = validated_data.pop('license_number', None)
        vehicle_type = validated_data.pop('vehicle_type', None)
        vehicle_plate = validated_data.pop('vehicle_plate', None)
        address = validated_data.pop('address', None)
        city = validated_data.pop('city', None)
        
        user = cls.model.objects.create_user(**validated_data)
        
        if user.role == User.Role.SUPPLIER:
            profile = user.supplier_profile
            profile.company_name = company_name or user.username
            profile.address = address
            profile.city = city
            profile.save()
        elif user.role == User.Role.SELLER:
            profile = user.seller_profile
            profile.business_name = business_name or user.username
            profile.business_type = business_type
            profile.address = address
            profile.city = city
            profile.save()
        elif user.role == User.Role.DRIVER:
            profile = user.driver_profile
            profile.license_number = license_number or ''
            profile.vehicle_type = vehicle_type or DriverProfile.VehicleType.CAR
            profile.vehicle_plate = vehicle_plate
            profile.city = city
            profile.save()
        
        return user
    
    @classmethod
    def authenticate_user(cls, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        return authenticate(username=username, password=password)
    
    @classmethod
    def generate_tokens(cls, user: User) -> dict:
        """Generate JWT tokens for user"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    
    @classmethod
    def change_password(cls, user: User, old_password: str, new_password: str) -> User:
        """Change user password"""
        if not user.check_password(old_password):
            raise BusinessLogicError(
                'Current password is incorrect',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        return user
    
    @classmethod
    def toggle_driver_availability(cls, user: User) -> bool:
        """Toggle driver availability status"""
        if not user.is_driver:
            raise BusinessLogicError(
                'This operation is only for drivers',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        driver_profile = user.driver_profile
        driver_profile.is_available = not driver_profile.is_available
        driver_profile.save()
        
        return driver_profile.is_available

    # -------------------------------------------------------------------------
    # Profile list (filtre ile: role, city, search, vehicle_type)
    # -------------------------------------------------------------------------

    @classmethod
    def list_profiles(
        cls,
        role: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Role filtresine göre profil listesi. role: SUPPLIER, SELLER, DRIVER."""
        role = (role or "").strip().upper()
        filters = filters or {}
        if role == User.Role.SUPPLIER:
            return cls._list_suppliers(filters)
        if role == User.Role.DRIVER:
            return cls._list_drivers(filters)
        if role == User.Role.SELLER:
            return cls._list_sellers(filters)
        return []

    @classmethod
    def _list_suppliers(cls, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        from .models import SupplierProfile

        qs = SupplierProfile.objects.filter(is_active=True).select_related("user")
        if filters.get("city"):
            qs = qs.filter(city__icontains=filters["city"])
        if filters.get("search"):
            qs = qs.filter(
                Q(company_name__icontains=filters["search"])
                | Q(description__icontains=filters["search"])
            )
        return [
            {
                "id": s.id,
                "company_name": s.company_name,
                "city": s.city,
                "description": s.description,
                "product_count": s.products.filter(is_active=True).count(),
            }
            for s in qs
        ]

    @classmethod
    def _list_drivers(cls, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        from .models import DriverProfile

        qs = DriverProfile.objects.filter(
            is_active=True, is_available=True
        ).select_related("user")
        if filters.get("city"):
            qs = qs.filter(city__icontains=filters["city"])
        if filters.get("vehicle_type"):
            qs = qs.filter(vehicle_type=filters["vehicle_type"])
        return [
            {
                "id": d.id,
                "name": d.user.get_full_name() or d.user.username,
                "phone": d.user.phone_number,
                "city": d.city,
                "vehicle_type": d.vehicle_type,
                "vehicle_type_display": d.get_vehicle_type_display(),
                "vehicle_plate": d.vehicle_plate,
            }
            for d in qs
        ]

    @classmethod
    def _list_sellers(cls, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        from .models import SellerProfile

        qs = SellerProfile.objects.filter(is_active=True).select_related("user")
        if filters.get("city"):
            qs = qs.filter(city__icontains=filters["city"])
        if filters.get("search"):
            qs = qs.filter(
                Q(business_name__icontains=filters["search"])
                | Q(description__icontains=filters["search"])
            )
        return [
            {
                "id": s.id,
                "business_name": s.business_name,
                "business_type": s.business_type,
                "city": s.city,
                "description": s.description,
            }
            for s in qs
        ]
