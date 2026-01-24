"""
Tests for Deal serializers
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from src.orders.models import Deal, DealItem
from src.orders.serializers import (
    DealSerializer,
    DealCreateSerializer,
    DealStatusUpdateSerializer,
    DealDriverAssignSerializer,
    DealDriverRequestSerializer,
    DealCompleteSerializer,
    DealItemSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestDealSerializer:
    """Test DealSerializer"""
    
    def test_deal_serializer(self, deal):
        """Test deal serialization"""
        serializer = DealSerializer(deal)
        data = serializer.data
        assert 'id' in data
        assert 'seller' in data
        assert 'supplier' in data
        assert 'status' in data
        assert 'status_display' in data
        assert 'delivery_handler' in data
        assert 'delivery_handler_display' in data
        assert 'delivery_cost_split' in data
        assert 'delivery_count' in data
        assert 'items' in data
        assert 'total_amount' in data
        assert data['delivery_cost_split'] == 50  # Default value
        assert data['delivery_count'] == 1  # Default value
    
    def test_deal_serializer_with_items(self, deal, product):
        """Test deal serializer with items"""
        DealItem.objects.create(
            deal=deal,
            product=product,
            quantity=2,
            unit_price=product.price
        )
        serializer = DealSerializer(deal)
        data = serializer.data
        assert len(data['items']) == 1
        assert data['items'][0]['product_name'] == product.name
        # total_amount can be Decimal or string depending on serializer
        total = Decimal(str(data['total_amount']))
        assert total == product.price * 2
    
    def test_deal_serializer_delivery_cost_split(self, seller_user, supplier_user):
        """Test deal serializer with custom delivery_cost_split"""
        deal = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
            delivery_cost_split=75,  # Supplier pays 75%, seller pays 25%
            status=Deal.Status.DEALING
        )
        serializer = DealSerializer(deal)
        data = serializer.data
        assert data['delivery_cost_split'] == 75


@pytest.mark.django_db
class TestDealCreateSerializer:
    """Test DealCreateSerializer"""
    
    def test_deal_create_serializer_as_seller(self, seller_client, supplier_user, product):
        """Test creating deal as seller"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
            'delivery_cost_split': 60,  # Supplier pays 60%, seller pays 40%
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        response = seller_client.post('/api/orders/deals/', data, format='json')
        assert response.status_code == 201
        assert response.data['success'] is True
        deal_data = response.data['data']
        assert deal_data['delivery_cost_split'] == 60
    
    def test_deal_create_serializer_default_delivery_cost_split(self, seller_client, supplier_user, product):
        """Test creating deal with default delivery_cost_split"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        response = seller_client.post('/api/orders/deals/', data, format='json')
        assert response.status_code == 201
        deal_data = response.data['data']
        assert deal_data['delivery_cost_split'] == 50  # Default value
    
    def test_deal_create_serializer_delivery_cost_split_with_3rd_party(self, seller_client, supplier_user, product):
        """Test that delivery_cost_split is reset to 50 for 3rd party deliveries"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SELLER,  # 3rd party
            'delivery_cost_split': 80,  # This should be reset to 50
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        response = seller_client.post('/api/orders/deals/', data, format='json')
        assert response.status_code == 201
        deal_data = response.data['data']
        # For 3rd party, delivery_cost_split should be 50 (not used)
        assert deal_data['delivery_cost_split'] == 50
    
    def test_deal_create_serializer_delivery_cost_split_boundary_values(self, seller_client, supplier_user, product):
        """Test delivery_cost_split boundary values (0 and 100)"""
        # Test 0 (seller pays all)
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
            'delivery_cost_split': 0,
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        response = seller_client.post('/api/orders/deals/', data, format='json')
        assert response.status_code == 201
        deal_data = response.data['data']
        assert deal_data['delivery_cost_split'] == 0
        
        # Test 100 (supplier pays all)
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
            'delivery_cost_split': 100,
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        response = seller_client.post('/api/orders/deals/', data, format='json')
        assert response.status_code == 201
        deal_data = response.data['data']
        assert deal_data['delivery_cost_split'] == 100
    
    def test_deal_create_serializer_delivery_cost_split_invalid_range(self, seller_client, supplier_user, product):
        """Test delivery_cost_split with invalid range"""
        # Test > 100
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
            'delivery_cost_split': 101,  # Invalid
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        response = seller_client.post('/api/orders/deals/', data, format='json')
        assert response.status_code == 400
        
        # Test < 0
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
            'delivery_cost_split': -1,  # Invalid
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        response = seller_client.post('/api/orders/deals/', data, format='json')
        assert response.status_code == 400


@pytest.mark.django_db
class TestDealItemSerializer:
    """Test DealItemSerializer"""
    
    def test_deal_item_serializer(self, deal, product):
        """Test deal item serialization"""
        item = DealItem.objects.create(
            deal=deal,
            product=product,
            quantity=3,
            unit_price=product.price
        )
        serializer = DealItemSerializer(item)
        data = serializer.data
        assert 'id' in data
        assert 'product' in data
        assert 'product_name' in data
        assert 'quantity' in data
        assert 'unit_price' in data
        assert 'total_price' in data
        assert data['product_name'] == product.name
        assert data['total_price'] == str(product.price * 3)


@pytest.mark.django_db
class TestDealStatusUpdateSerializer:
    """Test DealStatusUpdateSerializer"""
    
    def test_deal_status_update_serializer(self):
        """Test deal status update serializer"""
        data = {'status': Deal.Status.DEALING}
        serializer = DealStatusUpdateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['status'] == Deal.Status.DEALING
    
    def test_deal_status_update_invalid_status(self):
        """Test deal status update with invalid status"""
        data = {'status': 'INVALID_STATUS'}
        serializer = DealStatusUpdateSerializer(data=data)
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestDealDriverAssignSerializer:
    """Test DealDriverAssignSerializer"""
    
    def test_deal_driver_assign_serializer(self, driver_user):
        """Test deal driver assign serializer"""
        data = {'driver_id': driver_user.driver_profile.id}
        serializer = DealDriverAssignSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['driver_id'] == driver_user.driver_profile.id
    
    def test_deal_driver_assign_invalid_id(self):
        """Test deal driver assign with invalid driver id"""
        data = {'driver_id': 99999}
        serializer = DealDriverAssignSerializer(data=data)
        assert not serializer.is_valid()
        assert 'driver_id' in serializer.errors


@pytest.mark.django_db
class TestDealDriverRequestSerializer:
    """Test DealDriverRequestSerializer"""
    
    def test_deal_driver_request_serializer(self, driver_user):
        """Test deal driver request serializer"""
        driver_user.driver_profile.is_available = True
        driver_user.driver_profile.save()
        data = {'driver_id': driver_user.driver_profile.id}
        serializer = DealDriverRequestSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['driver_id'] == driver_user.driver_profile.id
    
    def test_deal_driver_request_invalid_id(self):
        """Test deal driver request with invalid driver id"""
        data = {'driver_id': 99999}
        serializer = DealDriverRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'driver_id' in serializer.errors
    
    def test_deal_driver_request_unavailable_driver(self, driver_user):
        """Test deal driver request with unavailable driver"""
        driver_user.driver_profile.is_available = False
        driver_user.driver_profile.save()
        data = {'driver_id': driver_user.driver_profile.id}
        serializer = DealDriverRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'driver_id' in serializer.errors


@pytest.mark.django_db
class TestDealCompleteSerializer:
    """Test DealCompleteSerializer"""
    
    def test_deal_complete_serializer(self):
        """Test deal complete serializer"""
        data = {
            'delivery_address': 'Test Address',
            'delivery_note': 'Test note',
            'supplier_share': 100
        }
        serializer = DealCompleteSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['delivery_address'] == 'Test Address'
        assert serializer.validated_data['delivery_note'] == 'Test note'
        assert serializer.validated_data['supplier_share'] == 100
    
    def test_deal_complete_serializer_default_supplier_share(self):
        """Test deal complete serializer with default supplier_share"""
        data = {
            'delivery_address': 'Test Address'
        }
        serializer = DealCompleteSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['supplier_share'] == 100  # Default
    
    def test_deal_complete_serializer_missing_delivery_address(self):
        """Test deal complete serializer without delivery_address"""
        data = {
            'supplier_share': 100
        }
        serializer = DealCompleteSerializer(data=data)
        assert not serializer.is_valid()
        assert 'delivery_address' in serializer.errors
