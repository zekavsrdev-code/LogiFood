"""
Tests for Product serializers
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.products.models import Category, Product
from apps.products.serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductCreateSerializer,
)

User = get_user_model()

pytestmark = pytest.mark.unit


@pytest.mark.django_db
class TestCategorySerializer:
    """Test CategorySerializer"""
    
    def test_category_serializer(self, category):
        """Test category serialization"""
        serializer = CategorySerializer(category)
        data = serializer.data
        assert 'id' in data
        assert 'name' in data
        assert 'slug' in data
        assert data['name'] == 'Test Category'
    
    def test_category_serializer_with_children(self, parent_category, child_category):
        """Test category serializer with children"""
        serializer = CategorySerializer(parent_category)
        data = serializer.data
        assert 'children' in data
        assert len(data['children']) > 0


@pytest.mark.django_db
class TestProductSerializer:
    """Test ProductSerializer"""
    
    def test_product_serializer(self, product):
        """Test product serialization"""
        serializer = ProductSerializer(product)
        data = serializer.data
        assert 'id' in data
        assert 'name' in data
        assert 'price' in data
        assert 'supplier_name' in data
        assert 'category_name' in data
        assert 'unit_display' in data
        assert data['name'] == 'Test Product'
    
    def test_product_serializer_read_only_fields(self, product):
        """Test that read-only fields are not writable"""
        serializer = ProductSerializer(product, data={'id': 999, 'slug': 'new-slug'})
        # Read-only fields should not be updated
        assert serializer.fields['id'].read_only
        assert serializer.fields['slug'].read_only


@pytest.mark.django_db
class TestProductCreateSerializer:
    """Test ProductCreateSerializer"""
    
    def test_product_create_serializer(self, supplier_user, category):
        """Test product creation serializer"""
        data = {
            'name': 'New Product',
            'description': 'New product description',
            'price': '50.00',
            'unit': Product.Unit.KG,
            'stock': 50,
            'min_order_quantity': 1,
            'category': category.id,
            'is_active': True
        }
        serializer = ProductCreateSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': supplier_user})()}
        )
        assert serializer.is_valid()
        product = serializer.save()
        assert product.name == 'New Product'
        assert product.supplier == supplier_user.supplier_profile


