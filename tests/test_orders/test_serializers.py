"""Tests for Order serializers"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.orders.models import Deal, DealItem, Delivery, DeliveryItem
from apps.orders.serializers import (
    DealSerializer,
    DealCreateSerializer,
    DealStatusUpdateSerializer,
    DealDriverAssignSerializer,
    DealDriverRequestSerializer,
    DealCompleteSerializer,
    DealItemSerializer,
    DeliverySerializer,
    DeliveryCreateSerializer,
    DeliveryStatusUpdateSerializer,
    DeliveryAssignDriverSerializer,
    DeliveryItemSerializer,
    RequestToDriverSerializer,
    RequestToDriverProposePriceSerializer,
    RequestToDriverApproveSerializer,
)

User = get_user_model()

pytestmark = pytest.mark.unit


@pytest.mark.django_db
class TestDealSerializer:
    """Test DealSerializer"""
    
    def test_deal_serializer(self, deal):
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
        assert 'seller_approved' in data
        assert 'supplier_approved' in data
        assert 'items' in data
        assert 'goods_total' in data
        assert 'delivery_fee' in data
        assert 'supplier_delivery_share' in data
        assert 'seller_delivery_share' in data
        assert data['delivery_cost_split'] == 50
        assert data['delivery_count'] == 1
        assert data['seller_approved'] is False
        assert data['supplier_approved'] is False
    
    def test_deal_serializer_with_items(self, deal, product):
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
        total = Decimal(str(data['goods_total']))
        assert total == product.price * 2
    
    def test_deal_serializer_delivery_cost_split(self, seller_user, supplier_user):
        deal = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
            delivery_cost_split=75,
            status=Deal.Status.DEALING
        )
        serializer = DealSerializer(deal)
        data = serializer.data
        assert data['delivery_cost_split'] == 75


@pytest.mark.django_db
class TestDealCreateSerializer:
    """Test DealCreateSerializer (unit: serializer instance, no HTTP)."""

    def _request_with_user(self, user):
        return type('Request', (object,), {'user': user})()

    def test_deal_create_serializer_valid_delivery_cost_split(self, seller_user, supplier_user, product):
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
            'delivery_cost_split': 60,
            'items': [{'product_id': product.id, 'quantity': 2}],
        }
        ser = DealCreateSerializer(
            data=data,
            context={'request': self._request_with_user(seller_user)},
        )
        assert ser.is_valid(), ser.errors
        deal = ser.save()
        assert deal.delivery_cost_split == 60

    def test_deal_create_serializer_default_delivery_cost_split(self, seller_user, supplier_user, product):
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
            'items': [{'product_id': product.id, 'quantity': 2}],
        }
        ser = DealCreateSerializer(
            data=data,
            context={'request': self._request_with_user(seller_user)},
        )
        assert ser.is_valid(), ser.errors
        deal = ser.save()
        assert deal.delivery_cost_split == 50

    def test_deal_create_serializer_3rd_party_ignores_delivery_cost_split(self, seller_user, supplier_user, product):
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SELLER,
            'delivery_cost_split': 80,
            'items': [{'product_id': product.id, 'quantity': 2}],
        }
        ser = DealCreateSerializer(
            data=data,
            context={'request': self._request_with_user(seller_user)},
        )
        assert ser.is_valid(), ser.errors
        deal = ser.save()
        assert deal.delivery_cost_split == 50


@pytest.mark.django_db
class TestDealItemSerializer:
    """Test DealItemSerializer"""
    
    def test_deal_item_serializer(self, deal, product):
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
        data = {'status': Deal.Status.DEALING}
        serializer = DealStatusUpdateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['status'] == Deal.Status.DEALING
    
    def test_deal_status_update_invalid_status(self):
        data = {'status': 'INVALID_STATUS'}
        serializer = DealStatusUpdateSerializer(data=data)
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestDealDriverAssignSerializer:
    """Test DealDriverAssignSerializer"""
    
    def test_deal_driver_assign_serializer(self, driver_user):
        data = {'driver_id': driver_user.driver_profile.id}
        serializer = DealDriverAssignSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['driver_id'] == driver_user.driver_profile.id
    
    def test_deal_driver_assign_invalid_id(self):
        data = {'driver_id': 99999}
        serializer = DealDriverAssignSerializer(data=data)
        assert not serializer.is_valid()
        assert 'driver_id' in serializer.errors


@pytest.mark.django_db
class TestDealDriverRequestSerializer:
    """Test DealDriverRequestSerializer"""
    
    def test_deal_driver_request_serializer(self, driver_user):
        driver_user.driver_profile.is_available = True
        driver_user.driver_profile.save()
        data = {'driver_id': driver_user.driver_profile.id, 'requested_price': '150.00'}
        serializer = DealDriverRequestSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['driver_id'] == driver_user.driver_profile.id
        assert serializer.validated_data['requested_price'] == Decimal('150.00')
    
    def test_deal_driver_request_invalid_id(self):
        data = {'driver_id': 99999}
        serializer = DealDriverRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'driver_id' in serializer.errors


@pytest.mark.django_db
class TestDealCompleteSerializer:
    """Test DealCompleteSerializer"""
    
    def test_deal_complete_serializer(self):
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
        data = {
            'delivery_address': 'Test Address'
        }
        serializer = DealCompleteSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['supplier_share'] == 100
    
    def test_deal_complete_serializer_missing_delivery_address(self):
        data = {
            'supplier_share': 100
        }
        serializer = DealCompleteSerializer(data=data)
        assert not serializer.is_valid()
        assert 'delivery_address' in serializer.errors


@pytest.mark.django_db
class TestDeliverySerializer:
    """Test DeliverySerializer"""
    
    def test_delivery_serializer(self, delivery):
        serializer = DeliverySerializer(delivery)
        data = serializer.data
        assert 'id' in data
        assert 'seller_name' in data
        assert 'supplier_name' in data
        assert 'status_display' in data
        assert 'items' in data
        assert 'supplier_share' in data
        assert 'is_3rd_party_delivery' in data
        assert data['supplier_share'] == 100
    
    def test_delivery_serializer_with_items(self, delivery, delivery_item):
        serializer = DeliverySerializer(delivery)
        data = serializer.data
        assert len(data['items']) == 1
        assert data['items'][0]['product_name'] == delivery_item.product.name
    
    def test_delivery_serializer_3rd_party(self, deal):
        delivery = Delivery.objects.create(
            deal=deal,
            delivery_address='Test Address',
            status=Delivery.Status.ESTIMATED,
            driver_profile=None,
            driver_name=None,
            driver_phone=None
        )
        serializer = DeliverySerializer(delivery)
        data = serializer.data
        assert data['is_3rd_party_delivery'] is True
        assert data['deal'] is not None
        assert 'seller_name' in data


@pytest.mark.django_db
class TestDeliveryCreateSerializer:
    """Test DeliveryCreateSerializer"""
    
    def test_delivery_create_serializer_is_empty(self):
        serializer = DeliveryCreateSerializer()
        assert serializer is not None


@pytest.mark.django_db
class TestDeliveryStatusUpdateSerializer:
    """Test DeliveryStatusUpdateSerializer"""
    
    def test_delivery_status_update_serializer(self):
        data = {'status': Delivery.Status.CONFIRMED}
        serializer = DeliveryStatusUpdateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['status'] == Delivery.Status.CONFIRMED
    
    def test_delivery_status_update_invalid_status(self):
        data = {'status': 'INVALID_STATUS'}
        serializer = DeliveryStatusUpdateSerializer(data=data)
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestDeliveryAssignDriverSerializer:
    """Test DeliveryAssignDriverSerializer"""
    
    def test_delivery_assign_driver_serializer(self, driver_user):
        data = {'driver_id': driver_user.driver_profile.id}
        serializer = DeliveryAssignDriverSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['driver_id'] == driver_user.driver_profile.id
    
    def test_delivery_assign_driver_invalid_id(self):
        data = {'driver_id': 99999}
        serializer = DeliveryAssignDriverSerializer(data=data)
        assert not serializer.is_valid()
        assert 'driver_id' in serializer.errors


@pytest.mark.django_db
class TestDeliveryItemSerializer:
    """Test DeliveryItemSerializer"""
    
    def test_delivery_item_serializer(self, delivery_item):
        serializer = DeliveryItemSerializer(delivery_item)
        data = serializer.data
        assert 'id' in data
        assert 'product_name' in data
        assert 'quantity' in data
        assert 'total_price' in data
        assert data['product_name'] == delivery_item.product.name
        assert data['total_price'] == str(delivery_item.total_price)


@pytest.mark.django_db
class TestRequestToDriverSerializer:
    """Test RequestToDriverSerializer"""
    
    def test_request_to_driver_serializer(self, deal, driver_user):
        from apps.orders.models import RequestToDriver
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        serializer = RequestToDriverSerializer(request)
        data = serializer.data
        assert 'id' in data
        assert 'deal' in data
        assert 'driver' in data
        assert 'requested_price' in data
        assert 'status' in data


@pytest.mark.django_db
class TestRequestToDriverProposePriceSerializer:
    """Test RequestToDriverProposePriceSerializer"""
    
    def test_propose_price_serializer(self):
        data = {'proposed_price': '175.00'}
        serializer = RequestToDriverProposePriceSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['proposed_price'] == Decimal('175.00')


@pytest.mark.django_db
class TestRequestToDriverApproveSerializer:
    """Test RequestToDriverApproveSerializer"""
    
    def test_approve_serializer(self):
        data = {'final_price': '150.00'}
        serializer = RequestToDriverApproveSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['final_price'] == Decimal('150.00')
    
    def test_approve_serializer_without_final_price(self):
        data = {}
        serializer = RequestToDriverApproveSerializer(data=data)
        assert serializer.is_valid()
