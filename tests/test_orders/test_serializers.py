"""
Tests for Delivery serializers
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from src.orders.models import Delivery, DeliveryItem
from src.orders.serializers import (
    DeliverySerializer,
    DeliveryCreateSerializer,
    DeliveryStatusUpdateSerializer,
    DeliveryAssignDriverSerializer,
    DeliveryItemSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestDeliverySerializer:
    """Test DeliverySerializer"""
    
    def test_delivery_serializer(self, delivery):
        """Test delivery serialization"""
        serializer = DeliverySerializer(delivery)
        data = serializer.data
        assert 'id' in data
        assert 'seller_name' in data
        assert 'supplier_name' in data
        assert 'status_display' in data
        assert 'items' in data
        assert 'total_amount' in data
    
    def test_delivery_serializer_with_items(self, delivery, delivery_item):
        """Test delivery serializer with items"""
        serializer = DeliverySerializer(delivery)
        data = serializer.data
        assert len(data['items']) == 1
        assert data['items'][0]['product_name'] == delivery_item.product.name


@pytest.mark.django_db
class TestDeliveryCreateSerializer:
    """Test DeliveryCreateSerializer"""
    
    def test_delivery_create_serializer_valid(self, seller_user, supplier_user, product):
        """Test valid delivery creation"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_address': 'Test Address',
            'delivery_note': 'Test note',
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        serializer = DeliveryCreateSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': seller_user})()}
        )
        assert serializer.is_valid()
        delivery = serializer.save()
        assert delivery.seller == seller_user.seller_profile
        assert delivery.supplier == supplier_user.supplier_profile
        assert delivery.items.count() == 1
    
    def test_delivery_create_serializer_invalid_supplier(self, seller_user):
        """Test delivery creation with invalid supplier"""
        data = {
            'supplier_id': 99999,
            'delivery_address': 'Test Address',
            'items': [{'product_id': 1, 'quantity': 1}]
        }
        serializer = DeliveryCreateSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': seller_user})()}
        )
        assert not serializer.is_valid()
        assert 'supplier_id' in serializer.errors
    
    def test_delivery_create_serializer_invalid_items(self, seller_user, supplier_user):
        """Test delivery creation with invalid items"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_address': 'Test Address',
            'items': [
                {'product_id': 99999, 'quantity': 1}  # Non-existent product
            ]
        }
        serializer = DeliveryCreateSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': seller_user})()}
        )
        # This will fail during create, not validation
        assert serializer.is_valid()  # Validation passes
        # But create will raise error (tested in views)
    
    def test_delivery_create_serializer_empty_items(self, seller_user, supplier_user):
        """Test delivery creation with empty items"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_address': 'Test Address',
            'items': []
        }
        serializer = DeliveryCreateSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': seller_user})()}
        )
        assert not serializer.is_valid()
        assert 'items' in serializer.errors


@pytest.mark.django_db
class TestDeliveryStatusUpdateSerializer:
    """Test DeliveryStatusUpdateSerializer"""
    
    def test_delivery_status_update_serializer(self):
        """Test delivery status update serializer"""
        data = {'status': Delivery.Status.CONFIRMED}
        serializer = DeliveryStatusUpdateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['status'] == Delivery.Status.CONFIRMED
    
    def test_delivery_status_update_invalid_status(self):
        """Test delivery status update with invalid status"""
        data = {'status': 'INVALID_STATUS'}
        serializer = DeliveryStatusUpdateSerializer(data=data)
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestDeliveryAssignDriverSerializer:
    """Test DeliveryAssignDriverSerializer"""
    
    def test_delivery_assign_driver_serializer(self, driver_user):
        """Test delivery assign driver serializer"""
        data = {'driver_id': driver_user.driver_profile.id}
        serializer = DeliveryAssignDriverSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['driver_id'] == driver_user.driver_profile.id
    
    def test_delivery_assign_driver_invalid_id(self):
        """Test delivery assign driver with invalid driver id"""
        data = {'driver_id': 99999}
        serializer = DeliveryAssignDriverSerializer(data=data)
        assert not serializer.is_valid()
        assert 'driver_id' in serializer.errors


@pytest.mark.django_db
class TestDeliveryItemSerializer:
    """Test DeliveryItemSerializer"""
    
    def test_delivery_item_serializer(self, delivery_item):
        """Test delivery item serialization"""
        serializer = DeliveryItemSerializer(delivery_item)
        data = serializer.data
        assert 'id' in data
        assert 'product_name' in data
        assert 'quantity' in data
        assert 'total_price' in data
        assert data['product_name'] == delivery_item.product.name
        assert data['total_price'] == str(delivery_item.total_price)
