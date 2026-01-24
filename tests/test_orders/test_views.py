"""
Tests for Delivery views
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import status
from src.orders.models import Delivery, DeliveryItem

User = get_user_model()


@pytest.mark.django_db
class TestDeliveryViews:
    """Test Delivery views"""
    
    def test_list_deliveries_as_seller(self, seller_client, delivery):
        """Test listing deliveries as seller"""
        response = seller_client.get('/api/orders/deliveries/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_deliveries_as_supplier(self, supplier_client, delivery):
        """Test listing deliveries as supplier"""
        response = supplier_client.get('/api/orders/deliveries/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_deliveries_unauthorized(self, api_client):
        """Test listing deliveries without authentication"""
        response = api_client.get('/api/orders/deliveries/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_delivery_not_allowed(self, seller_client, supplier_user, product):
        """Test that creating delivery directly is not allowed (must be from deal)"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_address': 'Test Address',
            'delivery_note': 'Test note',
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        response = seller_client.post('/api/orders/deliveries/', data, format='json')
        # Should return 403 as deliveries must be created from deals
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Deliveries must be created from deals' in str(response.data.get('detail', ''))
    
    def test_create_delivery_invalid_supplier(self, seller_client):
        """Test creating delivery with invalid supplier - should return 403 (not allowed)"""
        data = {
            'supplier_id': 99999,
            'delivery_address': 'Test Address',
            'items': [{'product_id': 1, 'quantity': 1}]
        }
        response = seller_client.post('/api/orders/deliveries/', data, format='json')
        # Should return 403 as deliveries must be created from deals
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_delivery_not_seller(self, supplier_client, supplier_user):
        """Test creating delivery as non-seller - should return 403 (not allowed)"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_address': 'Test Address',
            'items': [{'product_id': 1, 'quantity': 1}]
        }
        response = supplier_client.post('/api/orders/deliveries/', data, format='json')
        # Should return 403 as deliveries must be created from deals
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_retrieve_delivery(self, seller_client, delivery):
        """Test retrieving a delivery"""
        response = seller_client.get(f'/api/orders/deliveries/{delivery.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_update_delivery_status_as_supplier(self, supplier_client, delivery):
        """Test updating delivery status as supplier"""
        data = {'status': Delivery.Status.CONFIRMED}
        response = supplier_client.put(
            f'/api/orders/deliveries/{delivery.id}/update_status/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        delivery.refresh_from_db()
        assert delivery.status == Delivery.Status.CONFIRMED  # Updated from ESTIMATED to CONFIRMED
    
    def test_update_delivery_status_as_driver(self, driver_client, delivery, driver_user):
        """Test updating delivery status as driver"""
        delivery.driver_profile = driver_user.driver_profile
        # Manual fields should be None when using system driver
        delivery.driver_name = None
        delivery.driver_phone = None
        delivery.driver_vehicle_type = None
        delivery.driver_vehicle_plate = None
        delivery.driver_license_number = None
        delivery.status = Delivery.Status.PICKED_UP
        delivery.save()
        
        data = {'status': Delivery.Status.IN_TRANSIT}
        response = driver_client.put(
            f'/api/orders/deliveries/{delivery.id}/update_status/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_update_delivery_status_unauthorized(self, seller_client, delivery):
        """Test updating delivery status as seller (unauthorized)"""
        data = {'status': Delivery.Status.CONFIRMED}
        response = seller_client.put(
            f'/api/orders/deliveries/{delivery.id}/update_status/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_assign_driver(self, supplier_client, delivery, driver_user):
        """Test assigning driver to delivery"""
        data = {'driver_id': driver_user.driver_profile.id}
        response = supplier_client.put(
            f'/api/orders/deliveries/{delivery.id}/assign_driver/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        delivery.refresh_from_db()
        assert delivery.driver_profile == driver_user.driver_profile
        assert delivery.status == Delivery.Status.READY
    
    def test_assign_driver_not_supplier(self, seller_client, delivery, driver_user):
        """Test assigning driver as non-supplier"""
        data = {'driver_id': driver_user.driver_profile.id}
        response = seller_client.put(
            f'/api/orders/deliveries/{delivery.id}/assign_driver/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_assign_driver_invalid_driver(self, supplier_client, delivery):
        """Test assigning invalid driver"""
        data = {'driver_id': 99999}
        response = supplier_client.put(
            f'/api/orders/deliveries/{delivery.id}/assign_driver/',
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
    
    def test_list_available_deliveries(self, driver_client, delivery):
        """Test listing available deliveries for driver"""
        # Set delivery to READY status and ensure no driver
        delivery.status = Delivery.Status.READY
        delivery.driver_profile = None
        delivery.driver_name = None
        delivery.save()
        
        response = driver_client.get('/api/orders/available-deliveries/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_available_deliveries_not_driver(self, seller_client):
        """Test listing available deliveries as non-driver"""
        response = seller_client.get('/api/orders/available-deliveries/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_accept_delivery(self, driver_client, delivery, driver_user):
        """Test accepting a delivery"""
        # Set delivery to READY status and ensure no driver
        delivery.status = Delivery.Status.READY
        delivery.driver_profile = None
        delivery.driver_name = None
        delivery.save()
        
        response = driver_client.put(f'/api/orders/accept-delivery/{delivery.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        delivery.refresh_from_db()
        assert delivery.driver_profile is not None
        # When system driver is assigned, manual fields should be None
        assert delivery.driver_name is None
        assert delivery.status == Delivery.Status.PICKED_UP
    
    def test_accept_delivery_not_driver(self, seller_client, delivery):
        """Test accepting delivery as non-driver"""
        response = seller_client.put(f'/api/orders/accept-delivery/{delivery.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_accept_delivery_already_assigned(self, driver_client, delivery, driver_user):
        """Test accepting an already assigned delivery"""
        delivery.driver_profile = driver_user.driver_profile
        # Manual fields should be None when using system driver
        delivery.driver_name = None
        delivery.driver_phone = None
        delivery.driver_vehicle_type = None
        delivery.driver_vehicle_plate = None
        delivery.driver_license_number = None
        delivery.status = Delivery.Status.PICKED_UP
        delivery.save()
        
        # Create another driver
        other_driver = User.objects.create_user(
            username='other_driver',
            password='pass123',
            role=User.Role.DRIVER
        )
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=other_driver)
        
        response = client.put(f'/api/orders/accept-delivery/{delivery.id}/')
        # Should return 404 or 400 as delivery is already assigned
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]
