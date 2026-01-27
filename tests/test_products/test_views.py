"""
Tests for Product views
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import status
from apps.products.models import Category, Product

User = get_user_model()

pytestmark = pytest.mark.integration


@pytest.mark.django_db
class TestCategoryViews:
    """Test Category views"""
    
    def test_list_categories(self, api_client, parent_category):
        """Test listing categories"""
        response = api_client.get('/api/products/categories/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']['results']) > 0
    
    def test_retrieve_category(self, api_client, parent_category):
        """Test retrieving a category"""
        response = api_client.get(f'/api/products/categories/{parent_category.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['name'] == 'Parent Category'
    
    def test_category_search(self, api_client, parent_category):
        """Test category search"""
        response = api_client.get('/api/products/categories/?search=Parent')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True


@pytest.mark.django_db
class TestProductViews:
    """Test Product views"""
    
    def test_list_products(self, api_client, product):
        """Test listing products"""
        response = api_client.get('/api/products/items/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']['results']) > 0
    
    def test_retrieve_product(self, api_client, product):
        """Test retrieving a product"""
        response = api_client.get(f'/api/products/items/{product.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['name'] == 'Test Product'
    
    def test_product_search(self, api_client, product):
        """Test product search"""
        response = api_client.get('/api/products/items/?search=Test')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_product_filter_by_category(self, api_client, product, category):
        """Test filtering products by category"""
        response = api_client.get(f'/api/products/items/?category__slug={category.slug}')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_product_price_filter(self, api_client, product):
        """Test filtering products by price"""
        response = api_client.get('/api/products/items/?min_price=50&max_price=150')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_product_ordering(self, api_client, product):
        """Test ordering products"""
        response = api_client.get('/api/products/items/?ordering=price')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True


@pytest.mark.django_db
class TestSupplierProductViews:
    """Test Supplier Product views"""
    
    def test_list_supplier_products(self, supplier_client, product):
        """Test listing supplier's own products"""
        response = supplier_client.get('/api/products/my-products/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_supplier_products_unauthorized(self, api_client):
        """Test listing products without authentication"""
        response = api_client.get('/api/products/my-products/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_supplier_products_wrong_role(self, seller_client):
        """Test listing products with wrong role"""
        response = seller_client.get('/api/products/my-products/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_product(self, supplier_client, category):
        """Test creating a product"""
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
        response = supplier_client.post('/api/products/my-products/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['name'] == 'New Product'
    
    def test_create_product_invalid_data(self, supplier_client):
        """Test creating product with invalid data"""
        data = {
            'name': '',  # Invalid: empty name
            'price': '50.00'
        }
        response = supplier_client.post('/api/products/my-products/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_retrieve_supplier_product(self, supplier_client, product):
        """Test retrieving supplier's own product"""
        response = supplier_client.get(f'/api/products/my-products/{product.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_update_product(self, supplier_client, product):
        """Test updating a product"""
        data = {
            'name': 'Updated Product',
            'price': '75.00',
            'stock': 100
        }
        response = supplier_client.put(f'/api/products/my-products/{product.id}/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['name'] == 'Updated Product'
    
    def test_partial_update_product(self, supplier_client, product):
        """Test partially updating a product"""
        data = {'price': '85.00'}
        response = supplier_client.patch(f'/api/products/my-products/{product.id}/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_delete_product(self, supplier_client, product):
        """Test soft deleting a product"""
        response = supplier_client.delete(f'/api/products/my-products/{product.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        # Verify soft delete
        product.refresh_from_db()
        assert product.is_active is False
    
    def test_supplier_cannot_access_other_supplier_product(self, supplier_client, supplier_user, category):
        """Test supplier cannot access another supplier's product"""
        other_supplier = User.objects.create_user(
            username='other_supplier',
            password='pass123',
            role=User.Role.SUPPLIER
        )
        other_product = Product.objects.create(
            supplier=other_supplier.supplier_profile,
            category=category,
            name='Other Product',
            price=Decimal('100.00')
        )
        response = supplier_client.get(f'/api/products/my-products/{other_product.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


