"""Tests for Product services"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from src.products.models import Category, Product
from src.products.services import CategoryService, ProductService
from apps.core.exceptions import BusinessLogicError
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestCategoryService:
    """Test CategoryService"""
    
    def test_get_active_root_categories(self, parent_category):
        categories = CategoryService.get_active_root_categories()
        assert parent_category in categories
        assert categories.count() >= 1
    
    def test_get_category_detail(self, parent_category, child_category):
        data = CategoryService.get_category_detail(parent_category.id)
        assert 'id' in data
        assert 'name' in data
        assert 'children' in data
        assert len(data['children']) >= 1
    
    def test_invalidate_category_cache(self, category):
        CategoryService.invalidate_category_cache(category)
        assert True


@pytest.mark.django_db
class TestProductService:
    """Test ProductService"""
    
    def test_get_active_products(self, product):
        products = ProductService.get_active_products()
        assert product in products
        assert products.count() >= 1
    
    def test_get_active_products_with_filters(self, product, category):
        filters = {'category__slug': category.slug}
        products = ProductService.get_active_products(filters)
        assert product in products
    
    def test_get_active_products_price_filter(self, product):
        filters = {'min_price': 0, 'max_price': 200}
        products = ProductService.get_active_products(filters)
        assert product in products
    
    def test_get_active_products_search(self, product):
        filters = {'search': product.name}
        products = ProductService.get_active_products(filters)
        assert product in products
    
    def test_get_supplier_products(self, supplier_user, product):
        products = ProductService.get_supplier_products(supplier_user.supplier_profile)
        assert product in products
        assert products.count() >= 1
    
    def test_can_supplier_access_product(self, supplier_user, product):
        assert ProductService.can_supplier_access_product(product, supplier_user) is True
    
    def test_can_supplier_access_product_unauthorized(self, seller_user, product):
        assert ProductService.can_supplier_access_product(product, seller_user) is False
    
    def test_create_product(self, supplier_user, category):
        validated_data = {
            'name': 'New Product',
            'description': 'New product description',
            'price': Decimal('50.00'),
            'unit': Product.Unit.KG,
            'stock': 50,
            'min_order_quantity': 1,
            'category': category,
            'is_active': True
        }
        product = ProductService.create_product(supplier_user, validated_data)
        assert product.name == 'New Product'
        assert product.supplier == supplier_user.supplier_profile
        assert product.created_by == supplier_user
    
    def test_create_product_not_supplier(self, seller_user, category):
        validated_data = {
            'name': 'New Product',
            'price': Decimal('50.00'),
            'category': category
        }
        with pytest.raises(BusinessLogicError) as exc:
            ProductService.create_product(seller_user, validated_data)
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_product(self, supplier_user, product):
        validated_data = {
            'name': 'Updated Product',
            'price': Decimal('75.00')
        }
        updated_product = ProductService.update_product(product, supplier_user, validated_data)
        assert updated_product.name == 'Updated Product'
        assert updated_product.price == Decimal('75.00')
    
    def test_update_product_unauthorized(self, seller_user, product):
        validated_data = {'name': 'Updated Product'}
        with pytest.raises(BusinessLogicError) as exc:
            ProductService.update_product(product, seller_user, validated_data)
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_product(self, supplier_user, product):
        result = ProductService.delete_product(product, supplier_user)
        assert result is True
        product.refresh_from_db()
        assert product.is_active is False
    
    def test_delete_product_unauthorized(self, seller_user, product):
        with pytest.raises(BusinessLogicError) as exc:
            ProductService.delete_product(product, seller_user)
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
