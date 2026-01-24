"""
Tests for Order serializers
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from src.orders.models import Order, OrderItem
from src.orders.serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderStatusUpdateSerializer,
    OrderAssignDriverSerializer,
    OrderItemSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestOrderSerializer:
    """Test OrderSerializer"""
    
    def test_order_serializer(self, order):
        """Test order serialization"""
        serializer = OrderSerializer(order)
        data = serializer.data
        assert 'id' in data
        assert 'seller_name' in data
        assert 'supplier_name' in data
        assert 'status_display' in data
        assert 'items' in data
        assert 'total_amount' in data
    
    def test_order_serializer_with_items(self, order, order_item):
        """Test order serializer with items"""
        serializer = OrderSerializer(order)
        data = serializer.data
        assert len(data['items']) == 1
        assert data['items'][0]['product_name'] == order_item.product.name


@pytest.mark.django_db
class TestOrderCreateSerializer:
    """Test OrderCreateSerializer"""
    
    def test_order_create_serializer_valid(self, seller_user, supplier_user, product):
        """Test valid order creation"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_address': 'Test Address',
            'delivery_note': 'Test note',
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        serializer = OrderCreateSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': seller_user})()}
        )
        assert serializer.is_valid()
        order = serializer.save()
        assert order.seller == seller_user.seller_profile
        assert order.supplier == supplier_user.supplier_profile
        assert order.items.count() == 1
    
    def test_order_create_serializer_invalid_supplier(self, seller_user):
        """Test order creation with invalid supplier"""
        data = {
            'supplier_id': 99999,
            'delivery_address': 'Test Address',
            'items': [{'product_id': 1, 'quantity': 1}]
        }
        serializer = OrderCreateSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': seller_user})()}
        )
        assert not serializer.is_valid()
        assert 'supplier_id' in serializer.errors
    
    def test_order_create_serializer_invalid_items(self, seller_user, supplier_user):
        """Test order creation with invalid items"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_address': 'Test Address',
            'items': [
                {'product_id': 99999, 'quantity': 1}  # Non-existent product
            ]
        }
        serializer = OrderCreateSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': seller_user})()}
        )
        # This will fail during create, not validation
        assert serializer.is_valid()  # Validation passes
        # But create will raise error (tested in views)
    
    def test_order_create_serializer_empty_items(self, seller_user, supplier_user):
        """Test order creation with empty items"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_address': 'Test Address',
            'items': []
        }
        serializer = OrderCreateSerializer(
            data=data,
            context={'request': type('obj', (object,), {'user': seller_user})()}
        )
        assert not serializer.is_valid()
        assert 'items' in serializer.errors


@pytest.mark.django_db
class TestOrderStatusUpdateSerializer:
    """Test OrderStatusUpdateSerializer"""
    
    def test_order_status_update_serializer(self):
        """Test order status update serializer"""
        data = {'status': Order.Status.CONFIRMED}
        serializer = OrderStatusUpdateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['status'] == Order.Status.CONFIRMED
    
    def test_order_status_update_invalid_status(self):
        """Test order status update with invalid status"""
        data = {'status': 'INVALID_STATUS'}
        serializer = OrderStatusUpdateSerializer(data=data)
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestOrderAssignDriverSerializer:
    """Test OrderAssignDriverSerializer"""
    
    def test_order_assign_driver_serializer(self, driver_user):
        """Test order assign driver serializer"""
        data = {'driver_id': driver_user.driver_profile.id}
        serializer = OrderAssignDriverSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['driver_id'] == driver_user.driver_profile.id
    
    def test_order_assign_driver_invalid_id(self):
        """Test order assign driver with invalid driver id"""
        data = {'driver_id': 99999}
        serializer = OrderAssignDriverSerializer(data=data)
        assert not serializer.is_valid()
        assert 'driver_id' in serializer.errors


@pytest.mark.django_db
class TestOrderItemSerializer:
    """Test OrderItemSerializer"""
    
    def test_order_item_serializer(self, order_item):
        """Test order item serialization"""
        serializer = OrderItemSerializer(order_item)
        data = serializer.data
        assert 'id' in data
        assert 'product_name' in data
        assert 'quantity' in data
        assert 'total_price' in data
        assert data['product_name'] == order_item.product.name
        assert data['total_price'] == str(order_item.total_price)
