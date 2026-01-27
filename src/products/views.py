"""Product and category views"""
from rest_framework import status, viewsets, generics, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductCreateSerializer,
)
from .services import CategoryService, ProductService
from apps.core.utils import success_response
from apps.core.permissions import IsSupplier
from apps.core.pagination import StandardResultsSetPagination
from apps.core.exceptions import BusinessLogicError
from apps.core.cache import cache_get_or_set, cache_key


# ==================== CATEGORY VIEWS ====================


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Category ViewSet - Read-only operations"""
    queryset = Category.objects.filter(is_active=True, parent__isnull=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        return CategoryService.get_active_root_categories()
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Categories listed successfully')
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = CategoryService.get_category_detail(instance.id)
        return success_response(data=data, message='Category detail retrieved successfully')


# ==================== PRODUCT VIEWS ====================


class ProductListView(generics.ListAPIView):
    """Product list endpoint - Public access"""
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
        filters = {}
        if 'category__slug' in self.request.query_params:
            filters['category__slug'] = self.request.query_params['category__slug']
        if 'supplier' in self.request.query_params:
            filters['supplier'] = self.request.query_params['supplier']
        if 'min_price' in self.request.query_params:
            filters['min_price'] = self.request.query_params['min_price']
        if 'max_price' in self.request.query_params:
            filters['max_price'] = self.request.query_params['max_price']
        if 'search' in self.request.query_params:
            filters['search'] = self.request.query_params['search']
        
        return ProductService.get_active_products(filters)
    
    def list(self, request, *args, **kwargs):
        has_filters = any([
            request.query_params.get('category__slug'),
            request.query_params.get('supplier'),
            request.query_params.get('min_price'),
            request.query_params.get('max_price'),
            request.query_params.get('search'),
        ])
        
        if not has_filters:
            cache_key_str = cache_key('products', 'list', 'active')
            
            def get_products():
                queryset = self.get_queryset()
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data).data
                serializer = self.get_serializer(queryset, many=True)
                return serializer.data
            
            data = cache_get_or_set(cache_key_str, get_products, timeout=300)
            return success_response(data=data, message='Products listed successfully')
        
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Products listed successfully')


class ProductDetailView(generics.RetrieveAPIView):
    """Product detail endpoint - Public access"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        cache_key_str = cache_key('product', 'detail', product_id=instance.id)
        
        def get_product_data():
            serializer = self.get_serializer(instance)
            return serializer.data
        
        data = cache_get_or_set(cache_key_str, get_product_data, timeout=300)
        return success_response(data=data, message='Product detail')


class SupplierProductViewSet(viewsets.ModelViewSet):
    """Supplier's product management ViewSet"""
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsSupplier]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return ProductService.get_supplier_products(self.request.user.supplier_profile)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateSerializer
        return ProductSerializer
    
    def perform_create(self, serializer):
        try:
            product = ProductService.create_product(
                self.request.user,
                serializer.validated_data
            )
            serializer.instance = product
        except BusinessLogicError as e:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(str(e.detail))
    
    def perform_destroy(self, instance):
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
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_product = ProductService.update_product(
                instance,
                request.user,
                serializer.validated_data
            )
            response_serializer = ProductSerializer(updated_product)
            return success_response(
                data=response_serializer.data,
                message='Product updated successfully'
            )
        except BusinessLogicError as e:
            from apps.core.utils import error_response
            return error_response(
                message=str(e.detail),
                status_code=e.status_code
            )
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_product = ProductService.update_product(
                instance,
                request.user,
                serializer.validated_data
            )
            response_serializer = ProductSerializer(updated_product)
            return success_response(
                data=response_serializer.data,
                message='Product updated successfully'
            )
        except BusinessLogicError as e:
            from apps.core.utils import error_response
            return error_response(
                message=str(e.detail),
                status_code=e.status_code
            )
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        try:
            ProductService.delete_product(instance, request.user)
            return success_response(message='Product deleted successfully')
        except BusinessLogicError as e:
            from apps.core.utils import error_response
            return error_response(
                message=str(e.detail),
                status_code=e.status_code
            )
