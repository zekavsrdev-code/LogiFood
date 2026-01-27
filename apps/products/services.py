"""Product service layer for business logic."""
from typing import Optional, List, Dict, Any
from django.db.models import QuerySet, Q

from .models import Category, Product
from apps.users.models import SupplierProfile
from apps.core.services import BaseService
from apps.core.cache import cache_get_or_set, cache_key, invalidate_model_cache
from apps.core.exceptions import BusinessLogicError
from rest_framework import status


# ==================== CATEGORY SERVICE ====================


class CategoryService(BaseService):
    """Service for category-related business logic"""
    model = Category
    
    @classmethod
    def get_active_root_categories(cls) -> QuerySet:
        """Get active root categories with cache"""
        cache_key_str = cache_key('categories', 'root', 'active')
        
        def get_category_ids():
            queryset = cls.model.objects.filter(is_active=True, parent__isnull=True)
            return list(queryset.values_list('id', flat=True))
        
        category_ids = cache_get_or_set(cache_key_str, get_category_ids, timeout=600)
        
        queryset = cls.model.objects.filter(
            id__in=category_ids, 
            is_active=True, 
            parent__isnull=True
        )
        queryset = queryset.prefetch_related('children')
        
        return queryset
    
    @classmethod
    def get_category_detail(cls, category_id: int) -> Dict[str, Any]:
        """Get category detail with children (cached)"""
        category = cls.model.objects.get(id=category_id)
        
        cache_key_str = cache_key('category', 'detail', category_id=category_id)
        
        def get_category_data():
            from .serializers import CategorySerializer
            serializer = CategorySerializer(category)
            return serializer.data
        
        data = cache_get_or_set(cache_key_str, get_category_data, timeout=600)
        return data
    
    @classmethod
    def invalidate_category_cache(cls, category: Category):
        """Invalidate cache for a category"""
        invalidate_model_cache(cls.model, instance_id=category.id)
        if category.parent:
            invalidate_model_cache(cls.model, instance_id=category.parent.id)


# ==================== PRODUCT SERVICE ====================


class ProductService(BaseService):
    """Service for product-related business logic"""
    model = Product
    
    @classmethod
    def get_active_products(cls, filters: Optional[Dict[str, Any]] = None) -> QuerySet:
        """Get active products with optional filters"""
        queryset = cls.model.objects.filter(
            is_active=True
        ).select_related('supplier', 'category')
        
        if not filters:
            return queryset
        
        if 'category__slug' in filters:
            queryset = queryset.filter(category__slug=filters['category__slug'])
        if 'supplier' in filters:
            queryset = queryset.filter(supplier_id=filters['supplier'])
        if 'min_price' in filters:
            queryset = queryset.filter(price__gte=filters['min_price'])
        if 'max_price' in filters:
            queryset = queryset.filter(price__lte=filters['max_price'])
        if 'search' in filters:
            queryset = queryset.filter(
                Q(name__icontains=filters['search']) |
                Q(description__icontains=filters['search'])
            )
        
        return queryset
    
    @classmethod
    def get_supplier_products(cls, supplier: SupplierProfile) -> QuerySet:
        """Get products for a specific supplier"""
        return cls.model.objects.filter(
            supplier=supplier,
            is_active=True
        ).select_related('category')
    
    @classmethod
    def can_supplier_access_product(cls, product: Product, user) -> bool:
        """Check if supplier can access this product"""
        return user.is_supplier and product.supplier == user.supplier_profile
    
    @classmethod
    def create_product(cls, user, validated_data: Dict[str, Any]) -> Product:
        """Create a new product"""
        if not user.is_supplier:
            raise BusinessLogicError(
                'Only suppliers can create products', 
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        validated_data.pop('supplier', None)
        validated_data.pop('created_by', None)
        
        product = cls.model.objects.create(
            supplier=user.supplier_profile,
            created_by=user,
            **validated_data
        )
        
        invalidate_model_cache(cls.model)
        return product
    
    @classmethod
    def update_product(cls, product: Product, user, validated_data: Dict[str, Any]) -> Product:
        """Update a product"""
        if not cls.can_supplier_access_product(product, user):
            raise BusinessLogicError(
                'This product does not belong to you', 
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        for key, value in validated_data.items():
            setattr(product, key, value)
        product.save()
        
        invalidate_model_cache(cls.model, instance_id=product.id)
        return product
    
    @classmethod
    def delete_product(cls, product: Product, user) -> bool:
        """Soft delete a product (sets is_active=False)"""
        if not cls.can_supplier_access_product(product, user):
            raise BusinessLogicError(
                'This product does not belong to you', 
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        product_id = product.id
        product.is_active = False
        product.save()
        
        invalidate_model_cache(cls.model, instance_id=product_id)
        return True
    
    @classmethod
    def _has_filters(cls, filters: Optional[Dict[str, Any]]) -> bool:
        """Check if any filters are applied"""
        if not filters:
            return False
        return any([
            filters.get('category__slug'),
            filters.get('supplier'),
            filters.get('min_price'),
            filters.get('max_price'),
            filters.get('search'),
        ])
    
    @classmethod
    def get_cached_product_list(cls, filters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Get cached product list if no filters are applied"""
        return None
