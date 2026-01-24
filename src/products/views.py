from rest_framework import status, viewsets, generics, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductCreateSerializer,
)
from apps.core.utils import success_response
from apps.core.permissions import IsSupplier
from apps.core.pagination import StandardResultsSetPagination


# ==================== CATEGORY VIEWS ====================

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Category ViewSet - Anyone can view"""
    queryset = Category.objects.filter(is_active=True, parent__isnull=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Categories listed successfully')
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return success_response(data=response.data, message='Category detail retrieved successfully')


# ==================== PRODUCT VIEWS ====================

class ProductListView(generics.ListAPIView):
    """List all active products - Anyone can view"""
    queryset = Product.objects.filter(is_active=True).select_related('supplier', 'category')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__slug', 'supplier']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Price filtering
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Products listed successfully')


class ProductDetailView(generics.RetrieveAPIView):
    """Product detail - Anyone can view"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message='Product detail')


class SupplierProductViewSet(viewsets.ModelViewSet):
    """Supplier's own products - CRUD operations"""
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsSupplier]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Product.objects.filter(supplier=self.request.user.supplier_profile)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateSerializer
        return ProductSerializer
    
    def perform_create(self, serializer):
        serializer.save(supplier=self.request.user.supplier_profile)
    
    def perform_destroy(self, instance):
        # Soft delete - set is_active=False
        instance.is_active = False
        instance.save()
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Your products listed successfully')
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return success_response(
            data=response.data,
            message='Product added successfully',
            status_code=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return success_response(data=response.data, message='Product detail')
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return success_response(data=response.data, message='Product updated successfully')
    
    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        return success_response(data=response.data, message='Product updated successfully')
    
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return success_response(message='Product deleted successfully')
