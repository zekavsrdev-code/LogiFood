from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.core.models import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    """Custom User Model with Role System"""
    
    class Role(models.TextChoices):
        SUPPLIER = 'SUPPLIER', 'Tedarikçi'
        SELLER = 'SELLER', 'Satıcı'
        DRIVER = 'DRIVER', 'Sürücü'
    
    email = models.EmailField(blank=True, null=True)
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
    company_name = models.CharField(max_length=255, verbose_name='Şirket Adı')
    tax_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='Vergi Numarası')
    address = models.TextField(blank=True, null=True, verbose_name='Adres')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='Şehir')
    description = models.TextField(blank=True, null=True, verbose_name='Açıklama')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'supplier_profiles'
        verbose_name = 'Tedarikçi Profili'
        verbose_name_plural = 'Tedarikçi Profilleri'
    
    def __str__(self):
        return self.company_name


class SellerProfile(TimeStampedModel):
    """Seller Profile - Sells products (market, restaurant, etc.)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    business_name = models.CharField(max_length=255, verbose_name='İşletme Adı')
    business_type = models.CharField(max_length=100, blank=True, null=True, verbose_name='İşletme Türü')
    tax_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='Vergi Numarası')
    address = models.TextField(blank=True, null=True, verbose_name='Adres')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='Şehir')
    description = models.TextField(blank=True, null=True, verbose_name='Açıklama')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'seller_profiles'
        verbose_name = 'Satıcı Profili'
        verbose_name_plural = 'Satıcı Profilleri'
    
    def __str__(self):
        return self.business_name


class DriverProfile(TimeStampedModel):
    """Driver Profile - Transports products"""
    
    class VehicleType(models.TextChoices):
        MOTORCYCLE = 'MOTORCYCLE', 'Motosiklet'
        CAR = 'CAR', 'Otomobil'
        VAN = 'VAN', 'Minivan'
        TRUCK = 'TRUCK', 'Kamyon'
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    license_number = models.CharField(max_length=50, verbose_name='Ehliyet Numarası')
    vehicle_type = models.CharField(max_length=20, choices=VehicleType.choices, default=VehicleType.CAR, verbose_name='Araç Tipi')
    vehicle_plate = models.CharField(max_length=20, blank=True, null=True, verbose_name='Plaka')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='Şehir')
    is_available = models.BooleanField(default=True, verbose_name='Müsait mi?')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'driver_profiles'
        verbose_name = 'Sürücü Profili'
        verbose_name_plural = 'Sürücü Profilleri'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_vehicle_type_display()}"


# Signal to create role-based profile
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create profile based on user role when user is created"""
    if created:
        if instance.role == User.Role.SUPPLIER:
            SupplierProfile.objects.get_or_create(
                user=instance,
                defaults={'company_name': instance.username}
            )
        elif instance.role == User.Role.SELLER:
            SellerProfile.objects.get_or_create(
                user=instance,
                defaults={'business_name': instance.username}
            )
        elif instance.role == User.Role.DRIVER:
            DriverProfile.objects.get_or_create(
                user=instance,
                defaults={'license_number': ''}
            )
