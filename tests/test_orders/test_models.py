"""
Tests for Deal and Delivery models
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from src.orders.models import Deal, DealItem, Delivery, DeliveryItem

User = get_user_model()


@pytest.mark.django_db
class TestDealModel:
    """Test Deal model"""
    
    def test_create_deal(self, seller_user, supplier_user):
        """Test creating a deal"""
        deal = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_address='Test Address',
            delivery_note='Test note',
            status=Deal.Status.DEALING
        )
        assert deal.seller == seller_user.seller_profile
        assert deal.supplier == supplier_user.supplier_profile
        assert deal.status == Deal.Status.DEALING
        assert deal.delivery_count == 0
    
    def test_deal_str(self, deal):
        """Test deal string representation"""
        assert 'Deal #' in str(deal)
        assert deal.seller.business_name in str(deal)
        assert deal.supplier.company_name in str(deal)
    
    def test_deal_calculate_total(self, deal, product):
        """Test deal total calculation"""
        DealItem.objects.create(
            deal=deal,
            product=product,
            quantity=2,
            unit_price=product.price
        )
        total = deal.calculate_total()
        expected_total = product.price * 2
        assert total == expected_total
    
    def test_deal_increment_delivery_count(self, deal):
        """Test deal delivery count increment"""
        assert deal.delivery_count == 0
        deal.increment_delivery_count()
        assert deal.delivery_count == 1
        deal.increment_delivery_count()
        assert deal.delivery_count == 2


@pytest.mark.django_db
class TestDeliveryModel:
    """Test Delivery model"""
    
    def test_create_delivery_from_deal(self, deal):
        """Test creating a delivery from deal"""
        delivery = Delivery.objects.create(
            deal=deal,
            delivery_address=deal.delivery_address,
            delivery_note=deal.delivery_note,
            status=Delivery.Status.CONFIRMED,
            supplier_share=100
        )
        assert delivery.deal == deal
        assert delivery.seller_profile == deal.seller
        assert delivery.supplier_profile == deal.supplier
        assert delivery.supplier_share == 100
        assert delivery.is_standalone is False
        assert delivery.status == Delivery.Status.CONFIRMED
        assert delivery.total_amount == Decimal('0.00')
        deal.refresh_from_db()
        assert deal.delivery_count == 1
    
    def test_create_standalone_delivery_with_seller(self, seller_user):
        """Test creating a standalone delivery with seller"""
        delivery = Delivery.objects.create(
            seller=seller_user.seller_profile,
            delivery_address='Standalone Address',
            delivery_note='Standalone note',
            status=Delivery.Status.CONFIRMED
        )
        assert delivery.deal is None
        assert delivery.seller == seller_user.seller_profile
        assert delivery.supplier is None
        assert delivery.is_standalone is True
        assert delivery.seller_profile == seller_user.seller_profile
    
    def test_create_standalone_delivery_with_supplier(self, supplier_user):
        """Test creating a standalone delivery with supplier"""
        delivery = Delivery.objects.create(
            supplier=supplier_user.supplier_profile,
            delivery_address='Standalone Address',
            delivery_note='Standalone note',
            status=Delivery.Status.CONFIRMED
        )
        assert delivery.deal is None
        assert delivery.supplier == supplier_user.supplier_profile
        assert delivery.seller is None
        assert delivery.is_standalone is True
        assert delivery.supplier_profile == supplier_user.supplier_profile
    
    def test_standalone_delivery_validation_error_no_owner(self):
        """Test standalone delivery validation - must have seller or supplier"""
        from django.core.exceptions import ValidationError
        delivery = Delivery(
            delivery_address='Test Address',
            status=Delivery.Status.CONFIRMED
        )
        with pytest.raises(ValidationError):
            delivery.clean()
    
    def test_standalone_delivery_validation_error_both_owners(self, seller_user, supplier_user):
        """Test standalone delivery validation - cannot have both seller and supplier"""
        from django.core.exceptions import ValidationError
        delivery = Delivery(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_address='Test Address',
            status=Delivery.Status.CONFIRMED
        )
        with pytest.raises(ValidationError):
            delivery.clean()
    
    def test_delivery_from_deal_validation_error_has_owner(self, deal, seller_user):
        """Test delivery from deal validation - should not have seller/supplier set directly"""
        from django.core.exceptions import ValidationError
        delivery = Delivery(
            deal=deal,
            seller=seller_user.seller_profile,
            delivery_address='Test Address',
            status=Delivery.Status.CONFIRMED
        )
        with pytest.raises(ValidationError):
            delivery.clean()
    
    def test_delivery_supplier_share_validation(self, deal):
        """Test supplier share validation - cannot exceed 100"""
        from django.core.exceptions import ValidationError
        delivery = Delivery(
            deal=deal,
            supplier_share=150,
            delivery_address='Test Address',
            status=Delivery.Status.CONFIRMED
        )
        with pytest.raises(ValidationError):
            delivery.clean()
    
    def test_delivery_str(self, delivery):
        """Test delivery string representation"""
        assert 'Delivery #' in str(delivery)
        assert delivery.seller_profile.business_name in str(delivery)
    
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
    
    def test_delivery_status_choices(self, deal):
        """Test delivery status choices"""
        for status_value, status_label in Delivery.Status.choices:
            delivery = Delivery.objects.create(
                deal=deal,
                delivery_address='Test Address',
                status=status_value,
                supplier_share=100
            )
            assert delivery.status == status_value
            assert delivery.get_status_display() == status_label
    
    def test_delivery_get_driver_info_with_profile(self, delivery, driver_user):
        """Test getting driver info from driver profile"""
        delivery.driver_profile = driver_user.driver_profile
        delivery.save()
        driver_info = delivery.get_driver_info()
        assert driver_info is not None
        assert driver_info['is_system_driver'] is True
        assert driver_info['name'] is not None
    
    def test_delivery_get_driver_info_manual(self, delivery):
        """Test getting driver info from manual entry"""
        delivery.driver_name = 'John Doe'
        delivery.driver_phone = '555-1234'
        delivery.driver_vehicle_plate = 'ABC-123'
        delivery.save()
        driver_info = delivery.get_driver_info()
        assert driver_info is not None
        assert driver_info['is_system_driver'] is False
        assert driver_info['name'] == 'John Doe'
    
    def test_delivery_get_driver_info_none(self, delivery):
        """Test getting driver info when no driver"""
        driver_info = delivery.get_driver_info()
        assert driver_info is None


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
