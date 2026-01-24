"""
Custom permissions for the application
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.user == request.user if hasattr(obj, 'user') else False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsSupplier(permissions.BasePermission):
    """
    Sadece Tedarikçiler için izin
    """
    message = 'Bu işlem sadece tedarikçiler için geçerlidir.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_supplier
        )


class IsSeller(permissions.BasePermission):
    """
    Sadece Satıcılar için izin
    """
    message = 'Bu işlem sadece satıcılar için geçerlidir.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_seller
        )


class IsDriver(permissions.BasePermission):
    """
    Sadece Sürücüler için izin
    """
    message = 'Bu işlem sadece sürücüler için geçerlidir.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_driver
        )
