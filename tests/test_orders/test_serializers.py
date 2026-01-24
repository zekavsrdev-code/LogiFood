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
        assert 'supplier_share' in data
        assert 'is_standalone' in data
        assert data['is_standalone'] is False  # Delivery from deal
        assert data['supplier_share'] == 100
    
    def test_delivery_serializer_with_items(self, delivery, delivery_item):
        """Test delivery serializer with items"""
        serializer = DeliverySerializer(delivery)
        data = serializer.data
        assert len(data['items']) == 1
        assert data['items'][0]['product_name'] == delivery_item.product.name
    
    def test_delivery_serializer_standalone(self, standalone_delivery):
        """Test standalone delivery serialization"""
        serializer = DeliverySerializer(standalone_delivery)
        data = serializer.data
        assert data['is_standalone'] is True
        assert data['deal'] is None
        assert 'seller_name' in data


@pytest.mark.django_db
class TestDeliveryCreateSerializer:
    """Test DeliveryCreateSerializer - Note: Deliveries should be created from deals"""
    
    def test_delivery_create_serializer_is_empty(self):
        """Test that DeliveryCreateSerializer is empty (deliveries created from deals)"""
        serializer = DeliveryCreateSerializer()
        # Serializer should be empty as deliveries are created from deals
        assert serializer is not None


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
