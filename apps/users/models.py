from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    """Custom User Model with Role System"""
    
    class Role(models.TextChoices):
        SUPPLIER = 'SUPPLIER', 'Supplier'
        SELLER = 'SELLER', 'Seller'
        DRIVER = 'DRIVER', 'Driver'
    
    email = models.EmailField(blank=True, null=True, unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SELLER)
    
    # Login will be done with username
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_supplier(self):
        return self.role == self.Role.SUPPLIER
    
    @property
    def is_seller(self):
        return self.role == self.Role.SELLER
    
    @property
    def is_driver(self):
        return self.role == self.Role.DRIVER


class SupplierProfile(TimeStampedModel):
    """Supplier Profile - Supplies products"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supplier_profile')
    company_name = models.CharField(max_length=255, verbose_name='Company name')
    tax_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='Tax number')
    address = models.TextField(blank=True, null=True, verbose_name='Address')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='City')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'supplier_profiles'
        verbose_name = 'Supplier profile'
        verbose_name_plural = 'Supplier profiles'
    
    def __str__(self):
        return self.company_name


class SellerProfile(TimeStampedModel):
    """Seller Profile - Sells products (market, restaurant, etc.)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    business_name = models.CharField(max_length=255, verbose_name='Business name')
    business_type = models.CharField(max_length=100, blank=True, null=True, verbose_name='Business type')
    tax_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='Tax number')
    address = models.TextField(blank=True, null=True, verbose_name='Address')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='City')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'seller_profiles'
        verbose_name = 'Seller profile'
        verbose_name_plural = 'Seller profiles'
    
    def __str__(self):
        return self.business_name


class DriverProfile(TimeStampedModel):
    """Driver Profile - Transports products"""
    
    class VehicleType(models.TextChoices):
        MOTORCYCLE = 'MOTORCYCLE', 'Motorcycle'
        CAR = 'CAR', 'Car'
        VAN = 'VAN', 'Van'
        TRUCK = 'TRUCK', 'Truck'
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    license_number = models.CharField(max_length=50, verbose_name='License number')
    vehicle_type = models.CharField(max_length=20, choices=VehicleType.choices, default=VehicleType.CAR, verbose_name='Vehicle type')
    vehicle_plate = models.CharField(max_length=20, blank=True, null=True, verbose_name='License plate')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='City')
    is_available = models.BooleanField(default=True, verbose_name='Available')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'driver_profiles'
        verbose_name = 'Driver profile'
        verbose_name_plural = 'Driver profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_vehicle_type_display()}"
