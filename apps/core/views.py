from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint."""
    return Response({"status": "ok", "message": "LogiFood API is running"})


class BaseViewSet(viewsets.ModelViewSet):
    """Base viewset with common functionality"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return self.queryset.filter(is_active=True) if hasattr(self.queryset.model, 'is_active') else self.queryset
