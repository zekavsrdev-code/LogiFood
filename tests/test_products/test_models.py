"""
Tests for Product models
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.products.models import Category, Product

User = get_user_model()

pytestmark = pytest.mark.unit


@pytest.mark.django_db
class TestCategoryModel:
    """Test Category model"""
    
    def test_create_category(self):
        """Test creating a category"""
        category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            description='Test description',
            is_active=True
        )
        assert category.name == 'Test Category'
        assert category.slug == 'test-category'
        assert category.is_active is True
        assert str(category) == 'Test Category'
    
    def test_category_with_parent(self, parent_category):
        """Test creating a category with parent"""
        child = Category.objects.create(
            name='Child Category',
            slug='child-category',
            parent=parent_category,
            is_active=True
        )
        assert child.parent == parent_category
        assert child in parent_category.children.all()
    
    def test_category_str(self, category):
        """Test category string representation"""
        assert str(category) == 'Test Category'


@pytest.mark.django_db
class TestProductModel:
    """Test Product model"""
    
    def test_create_product(self, supplier_user, category):
        """Test creating a product"""
        product = Product.objects.create(
            supplier=supplier_user.supplier_profile,
            category=category,
            name='Test Product',
            description='Test description',
            price=Decimal('99.99'),
            unit=Product.Unit.KG,
            min_order_quantity=1
        )
        assert product.name == 'Test Product'
        assert product.price == Decimal('99.99')
        assert product.unit == Product.Unit.KG
        assert product.is_active is True
        assert product.supplier == supplier_user.supplier_profile
    
    def test_product_slug_auto_generation(self, supplier_user, category):
        """Test automatic slug generation"""
        product = Product.objects.create(
            supplier=supplier_user.supplier_profile,
            category=category,
            name='Test Product Name',
            price=Decimal('50.00')
        )
        assert product.slug == 'test-product-name'
    
    def test_product_str(self, product, supplier_user):
        """Test product string representation"""
        assert supplier_user.supplier_profile.company_name in str(product)
        assert product.name in str(product)
    
    def test_product_unit_choices(self, supplier_user, category):
        """Test product unit choices"""
        for unit_value, unit_label in Product.Unit.choices:
            product = Product.objects.create(
                supplier=supplier_user.supplier_profile,
                category=category,
                name=f'Product {unit_value}',
                price=Decimal('10.00'),
                unit=unit_value
            )
            assert product.unit == unit_value
            assert product.get_unit_display() == unit_label


