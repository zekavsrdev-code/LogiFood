"""
Tests for Delivery models
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from src.orders.models import Delivery, DeliveryItem

User = get_user_model()


@pytest.mark.django_db
class TestDeliveryModel:
    """Test Delivery model"""
    
    def test_create_delivery(self, seller_user, supplier_user):
        """Test creating a delivery"""
        delivery = Delivery.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_address='Test Address',
            delivery_note='Test note',
            status=Delivery.Status.CONFIRMED
        )
        assert delivery.seller == seller_user.seller_profile
        assert delivery.supplier == supplier_user.supplier_profile
        assert delivery.status == Delivery.Status.CONFIRMED
        assert delivery.total_amount == Decimal('0.00')
        assert delivery.delivery_address == 'Test Address'
    
    def test_delivery_str(self, delivery):
        """Test delivery string representation"""
        assert 'Delivery #' in str(delivery)
        assert delivery.seller.business_name in str(delivery)
    
    def test_delivery_calculate_total(self, delivery, product):
        """Test delivery total calculation"""
        DeliveryItem.objects.create(
            delivery=delivery,
            product=product,
            quantity=2,
            unit_price=product.price
        )
        total = delivery.calculate_total()
        expected_total = product.price * 2
        assert total == expected_total
        assert delivery.total_amount == expected_total
    
    def test_delivery_status_choices(self, seller_user, supplier_user):
        """Test delivery status choices"""
        for status_value, status_label in Delivery.Status.choices:
            delivery = Delivery.objects.create(
                seller=seller_user.seller_profile,
                supplier=supplier_user.supplier_profile,
                delivery_address='Test Address',
                status=status_value
            )
            assert delivery.status == status_value
            assert delivery.get_status_display() == status_label


@pytest.mark.django_db
class TestDeliveryItemModel:
    """Test DeliveryItem model"""
    
    def test_create_delivery_item(self, delivery, product):
        """Test creating a delivery item"""
        delivery_item = DeliveryItem.objects.create(
            delivery=delivery,
            product=product,
            quantity=5,
            unit_price=product.price
        )
        assert delivery_item.delivery == delivery
        assert delivery_item.product == product
        assert delivery_item.quantity == 5
        assert delivery_item.unit_price == product.price
    
    def test_delivery_item_total_price(self, delivery, product):
        """Test delivery item total price calculation"""
        delivery_item = DeliveryItem.objects.create(
            delivery=delivery,
            product=product,
            quantity=3,
            unit_price=Decimal('10.00')
        )
        expected_total = Decimal('30.00')
        assert delivery_item.total_price == expected_total
    
    def test_delivery_item_auto_unit_price(self, delivery, product):
        """Test automatic unit price from product"""
        delivery_item = DeliveryItem.objects.create(
            delivery=delivery,
            product=product,
            quantity=2
        )
        assert delivery_item.unit_price == product.price
    
    def test_delivery_item_str(self, delivery_item):
        """Test delivery item string representation"""
        assert delivery_item.product.name in str(delivery_item)
        assert str(delivery_item.quantity) in str(delivery_item)
