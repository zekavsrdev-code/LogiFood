"""
Tests for Order views
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import status
from src.orders.models import Order, OrderItem

User = get_user_model()


@pytest.mark.django_db
class TestOrderViews:
    """Test Order views"""
    
    def test_list_orders_as_seller(self, seller_client, order):
        """Test listing orders as seller"""
        response = seller_client.get('/api/orders/orders/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_orders_as_supplier(self, supplier_client, order):
        """Test listing orders as supplier"""
        response = supplier_client.get('/api/orders/orders/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_orders_unauthorized(self, api_client):
        """Test listing orders without authentication"""
        response = api_client.get('/api/orders/orders/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_order(self, seller_client, supplier_user, product):
        """Test creating an order"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_address': 'Test Address',
            'delivery_note': 'Test note',
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        response = seller_client.post('/api/orders/orders/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['seller_name'] is not None
    
    def test_create_order_invalid_supplier(self, seller_client):
        """Test creating order with invalid supplier"""
        data = {
            'supplier_id': 99999,
            'delivery_address': 'Test Address',
            'items': [{'product_id': 1, 'quantity': 1}]
        }
        response = seller_client.post('/api/orders/orders/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_order_not_seller(self, supplier_client, supplier_user):
        """Test creating order as non-seller"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_address': 'Test Address',
            'items': [{'product_id': 1, 'quantity': 1}]
        }
        response = supplier_client.post('/api/orders/orders/', data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_retrieve_order(self, seller_client, order):
        """Test retrieving an order"""
        response = seller_client.get(f'/api/orders/orders/{order.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_update_order_status_as_supplier(self, supplier_client, order):
        """Test updating order status as supplier"""
        data = {'status': Order.Status.CONFIRMED}
        response = supplier_client.put(
            f'/api/orders/orders/{order.id}/update_status/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        order.refresh_from_db()
        assert order.status == Order.Status.CONFIRMED
    
    def test_update_order_status_as_driver(self, driver_client, order, driver_user):
        """Test updating order status as driver"""
        order.driver = driver_user.driver_profile
        order.status = Order.Status.PICKED_UP
        order.save()
        
        data = {'status': Order.Status.IN_TRANSIT}
        response = driver_client.put(
            f'/api/orders/orders/{order.id}/update_status/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_update_order_status_unauthorized(self, seller_client, order):
        """Test updating order status as seller (unauthorized)"""
        data = {'status': Order.Status.CONFIRMED}
        response = seller_client.put(
            f'/api/orders/orders/{order.id}/update_status/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_assign_driver(self, supplier_client, order, driver_user):
        """Test assigning driver to order"""
        data = {'driver_id': driver_user.driver_profile.id}
        response = supplier_client.put(
            f'/api/orders/orders/{order.id}/assign_driver/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        order.refresh_from_db()
        assert order.driver == driver_user.driver_profile
        assert order.status == Order.Status.READY
    
    def test_assign_driver_not_supplier(self, seller_client, order, driver_user):
        """Test assigning driver as non-supplier"""
        data = {'driver_id': driver_user.driver_profile.id}
        response = seller_client.put(
            f'/api/orders/orders/{order.id}/assign_driver/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_assign_driver_invalid_driver(self, supplier_client, order):
        """Test assigning invalid driver"""
        data = {'driver_id': 99999}
        response = supplier_client.put(
            f'/api/orders/orders/{order.id}/assign_driver/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestDiscoveryViews:
    """Test Discovery views"""
    
    def test_list_suppliers(self, seller_client, supplier_user):
        """Test listing suppliers"""
        response = seller_client.get('/api/orders/suppliers/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_suppliers_unauthorized(self, api_client):
        """Test listing suppliers without authentication"""
        response = api_client.get('/api/orders/suppliers/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_drivers(self, supplier_client, driver_user):
        """Test listing drivers"""
        response = supplier_client.get('/api/orders/drivers/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_drivers_not_supplier(self, seller_client):
        """Test listing drivers as non-supplier"""
        response = seller_client.get('/api/orders/drivers/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_list_available_orders(self, driver_client, order, supplier_user, seller_user):
        """Test listing available orders for driver"""
        # Set order to READY status
        order.status = Order.Status.READY
        order.save()
        
        response = driver_client.get('/api/orders/available-orders/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_available_orders_not_driver(self, seller_client):
        """Test listing available orders as non-driver"""
        response = seller_client.get('/api/orders/available-orders/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_accept_order(self, driver_client, order, supplier_user, seller_user):
        """Test accepting an order"""
        # Set order to READY status
        order.status = Order.Status.READY
        order.save()
        
        response = driver_client.put(f'/api/orders/accept-order/{order.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        order.refresh_from_db()
        assert order.driver is not None
        assert order.status == Order.Status.PICKED_UP
    
    def test_accept_order_not_driver(self, seller_client, order):
        """Test accepting order as non-driver"""
        response = seller_client.put(f'/api/orders/accept-order/{order.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_accept_order_already_assigned(self, driver_client, order, driver_user, supplier_user, seller_user):
        """Test accepting an already assigned order"""
        order.driver = driver_user.driver_profile
        order.status = Order.Status.PICKED_UP
        order.save()
        
        # Create another driver
        other_driver = User.objects.create_user(
            username='other_driver',
            password='pass123',
            role=User.Role.DRIVER
        )
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=other_driver)
        
        response = client.put(f'/api/orders/accept-order/{order.id}/')
        # Should return 404 or 400 as order is already assigned
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]
