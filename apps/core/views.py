from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


class BaseViewSet(viewsets.ModelViewSet):
    """Base viewset with common functionality"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return self.queryset.filter(is_active=True) if hasattr(self.queryset.model, 'is_active') else self.queryset
