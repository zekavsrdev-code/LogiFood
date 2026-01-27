from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SupplierProfile, SellerProfile, DriverProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """User Admin Configuration"""
    list_display = ['username', 'email', 'role', 'first_name', 'last_name', 'is_staff', 'is_verified', 'created_at']
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_verified', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Additional Info', {'fields': ('role', 'phone_number', 'avatar', 'is_verified')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role & Additional Info', {'fields': ('role', 'email', 'phone_number')}),
    )


@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    """Supplier profile admin"""
    list_display = ['company_name', 'user', 'city', 'is_active', 'created_at']
    list_filter = ['is_active', 'city', 'created_at']
    search_fields = ['company_name', 'user__username', 'tax_number']
    ordering = ['-created_at']
    raw_id_fields = ['user']


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    """Seller profile admin"""
    list_display = ['business_name', 'user', 'business_type', 'city', 'is_active', 'created_at']
    list_filter = ['is_active', 'business_type', 'city', 'created_at']
    search_fields = ['business_name', 'user__username', 'tax_number']
    ordering = ['-created_at']
    raw_id_fields = ['user']


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    """Driver profile admin"""
    list_display = ['user', 'vehicle_type', 'vehicle_plate', 'city', 'is_available', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_available', 'vehicle_type', 'city', 'created_at']
    search_fields = ['user__username', 'license_number', 'vehicle_plate']
    ordering = ['-created_at']
    raw_id_fields = ['user']
