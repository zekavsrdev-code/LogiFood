"""
Product and category views.

All views use DRF generic views and viewsets following best practices:
- ViewSets for CRUD operations
- Generic views for read-only or specific operations
"""
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
from apps.core.cache import cache_get_or_set, cache_key, invalidate_model_cache


# ==================== CATEGORY VIEWS ====================


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Category ViewSet - Read-only operations.
    
    GET /api/products/categories/ - List all active root categories
    GET /api/products/categories/{id}/ - Retrieve category detail with children
    """
    queryset = Category.objects.filter(is_active=True, parent__isnull=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Get categories with cache."""
        cache_key_str = cache_key('categories', 'root', 'active')
        
        def get_categories():
            return list(Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('children'))
        
        categories = cache_get_or_set(cache_key_str, get_categories, timeout=600)  # 10 minutes
        return categories
    
    def list(self, request, *args, **kwargs):
        """List all active root categories."""
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Categories listed successfully')
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve category detail with nested children."""
        instance = self.get_object()
        
        # Cache category detail with children
        cache_key_str = cache_key('category', 'detail', category_id=instance.id)
        
        def get_category_data():
            serializer = self.get_serializer(instance)
            return serializer.data
        
        data = cache_get_or_set(cache_key_str, get_category_data, timeout=600)  # 10 minutes
        return success_response(data=data, message='Category detail retrieved successfully')


# ==================== PRODUCT VIEWS ====================


class ProductListView(generics.ListAPIView):
    """
    Product list endpoint - Public access.
    
    GET /api/products/products/ - List all active products with filtering and search
    """
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
        """Apply custom price filtering."""
        queryset = super().get_queryset()
        
        # Price range filtering
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List all active products with applied filters."""
        # Only cache if no filters are applied (most common case)
        has_filters = any([
            request.query_params.get('category__slug'),
            request.query_params.get('supplier'),
            request.query_params.get('min_price'),
            request.query_params.get('max_price'),
            request.query_params.get('search'),
        ])
        
        if not has_filters:
            # Cache unfiltered product list
            cache_key_str = cache_key('products', 'list', 'active')
            
            def get_products():
                queryset = self.get_queryset()
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data).data
                serializer = self.get_serializer(queryset, many=True)
                return serializer.data
            
            data = cache_get_or_set(cache_key_str, get_products, timeout=300)  # 5 minutes
            return success_response(data=data, message='Products listed successfully')
        
        # Use normal flow for filtered queries
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Products listed successfully')


class ProductDetailView(generics.RetrieveAPIView):
    """
    Product detail endpoint - Public access.
    
    GET /api/products/products/{id}/ - Retrieve product detail
    """
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve product detail."""
        instance = self.get_object()
        
        # Cache product detail
        cache_key_str = cache_key('product', 'detail', product_id=instance.id)
        
        def get_product_data():
            serializer = self.get_serializer(instance)
            return serializer.data
        
        data = cache_get_or_set(cache_key_str, get_product_data, timeout=300)  # 5 minutes
        return success_response(data=data, message='Product detail')


class SupplierProductViewSet(viewsets.ModelViewSet):
    """
    Supplier's product management ViewSet.
    
    Full CRUD operations for supplier's own products:
    - GET /api/products/supplier-products/ - List supplier's products
    - POST /api/products/supplier-products/ - Create new product
    - GET /api/products/supplier-products/{id}/ - Retrieve product detail
    - PUT /api/products/supplier-products/{id}/ - Update product
    - PATCH /api/products/supplier-products/{id}/ - Partial update product
    - DELETE /api/products/supplier-products/{id}/ - Soft delete product (sets is_active=False)
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsSupplier]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return only products belonging to the authenticated supplier."""
        return Product.objects.filter(supplier=self.request.user.supplier_profile)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateSerializer
        return ProductSerializer
    
    def perform_create(self, serializer):
        """Set supplier and created_by when creating a product."""
        instance = serializer.save(
            supplier=self.request.user.supplier_profile,
            created_by=self.request.user
        )
        # Invalidate product caches
        invalidate_model_cache(Product)
    
    def perform_destroy(self, instance):
        """Soft delete - set is_active=False instead of actual deletion."""
        instance.is_active = False
        instance.save()
    
    def list(self, request, *args, **kwargs):
        """List supplier's products."""
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Your products listed successfully')
    
    def create(self, request, *args, **kwargs):
        """Create a new product."""
        response = super().create(request, *args, **kwargs)
        return success_response(
            data=response.data,
            message='Product added successfully',
            status_code=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve product detail."""
        response = super().retrieve(request, *args, **kwargs)
        return success_response(data=response.data, message='Product detail')
    
    def update(self, request, *args, **kwargs):
        """Update product."""
        instance = self.get_object()
        response = super().update(request, *args, **kwargs)
        # Invalidate cache for this product and product list
        invalidate_model_cache(Product, instance_id=instance.id)
        return success_response(data=response.data, message='Product updated successfully')
    
    def partial_update(self, request, *args, **kwargs):
        """Partially update product."""
        instance = self.get_object()
        response = super().partial_update(request, *args, **kwargs)
        # Invalidate cache for this product and product list
        invalidate_model_cache(Product, instance_id=instance.id)
        return success_response(data=response.data, message='Product updated successfully')
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete product."""
        instance = self.get_object()
        super().destroy(request, *args, **kwargs)
        # Invalidate cache for this product and product list
        invalidate_model_cache(Product, instance_id=instance.id)
        return success_response(message='Product deleted successfully')
