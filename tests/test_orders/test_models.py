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
            delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
            status=Deal.Status.DEALING
        )
        assert deal.seller == seller_user.seller_profile
        assert deal.supplier == supplier_user.supplier_profile
        assert deal.status == Deal.Status.DEALING
        assert deal.delivery_count == 1  # Default is 1 (each deal must have at least one delivery)
        assert deal.delivery_cost_split == 50  # Default value
    
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
    
    def test_deal_get_actual_delivery_count(self, deal):
        """Test getting actual delivery count"""
        assert deal.get_actual_delivery_count() == 0  # No deliveries created yet
        assert deal.delivery_count == 1  # Planned count is 1
        
        # Create a delivery
        from src.orders.models import Delivery
        Delivery.objects.create(
            deal=deal,
            delivery_address='Test Address',
            status=Delivery.Status.ESTIMATED,  # Default status is now ESTIMATED
            supplier_share=100,
            driver_profile=None
        )
        assert deal.get_actual_delivery_count() == 1
        assert deal.can_create_more_deliveries() is False  # Planned count reached
    
    def test_deal_can_create_more_deliveries(self, deal):
        """Test checking if more deliveries can be created"""
        # Set planned count to 3
        deal.delivery_count = 3
        deal.save()
        
        assert deal.can_create_more_deliveries() is True  # 0 < 3
        
        # Create 2 deliveries
        from src.orders.models import Delivery
        for i in range(2):
            Delivery.objects.create(
                deal=deal,
                delivery_address=f'Test Address {i}',
                status=Delivery.Status.ESTIMATED,  # Default status is now ESTIMATED
                supplier_share=100,
                driver_profile=None
            )
        
        assert deal.get_actual_delivery_count() == 2
        assert deal.can_create_more_deliveries() is True  # 2 < 3
        
        # Create one more
        Delivery.objects.create(
            deal=deal,
            delivery_address='Test Address 3',
            status=Delivery.Status.ESTIMATED,  # Default status is now ESTIMATED
            supplier_share=100,
            driver_profile=None
        )
        
        assert deal.get_actual_delivery_count() == 3
        assert deal.can_create_more_deliveries() is False  # 3 >= 3


@pytest.mark.django_db
class TestDeliveryModel:
    """Test Delivery model"""
    
    def test_create_delivery_from_deal(self, deal):
        """Test creating a delivery from deal"""
        initial_actual_count = deal.get_actual_delivery_count()  # Actual delivery count (should be 0 initially)
        planned_count = deal.delivery_count  # Planned delivery count (should be 1 by default)
        delivery = Delivery.objects.create(
            deal=deal,
            delivery_address='Test Address',
            delivery_note='Test note',
            status=Delivery.Status.ESTIMATED,  # Default status is now ESTIMATED
            supplier_share=100,
            driver_profile=None,  # No driver for this test
            driver_name=None,
            driver_phone=None,
            driver_vehicle_type=None,
            driver_vehicle_plate=None,
            driver_license_number=None
        )
        assert delivery.deal == deal
        assert delivery.seller_profile == deal.seller
        assert delivery.supplier_profile == deal.supplier
        assert delivery.supplier_share == 100
        assert delivery.is_3rd_party_delivery is True  # No driver_profile means 3rd party
        assert delivery.status == Delivery.Status.ESTIMATED
        assert delivery.total_amount == Decimal('0.00')
        deal.refresh_from_db()
        # delivery_count is now the planned count, not actual count
        # Actual count should be incremented by 1
        assert deal.get_actual_delivery_count() == initial_actual_count + 1
        assert deal.delivery_count == planned_count  # Planned count doesn't change
    
    def test_delivery_validation_error_no_deal(self):
        """Test delivery validation - must have deal"""
        delivery = Delivery(
            delivery_address='Test Address',
            status=Delivery.Status.ESTIMATED  # Default status is now ESTIMATED
        )
        with pytest.raises(ValidationError):
            delivery.clean()
    
    def test_delivery_validation_error_driver_profile_and_manual_fields(self, deal, driver_user):
        """Test delivery validation - cannot use both driver_profile and manual driver fields"""
        delivery = Delivery(
            deal=deal,
            delivery_address='Test Address',
            status=Delivery.Status.ESTIMATED,  # Default status is now ESTIMATED
            driver_profile=driver_user.driver_profile,
            driver_name='Manual Driver',  # This should cause validation error
            driver_phone='1234567890'
        )
        with pytest.raises(ValidationError):
            delivery.clean()
    
    def test_delivery_supplier_share_validation(self, deal):
        """Test delivery supplier share validation"""
        delivery = Delivery(
            deal=deal,
            delivery_address='Test Address',
            supplier_share=150,  # Invalid: > 100
            status=Delivery.Status.ESTIMATED,  # Default status is now ESTIMATED
            driver_profile=None
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
        delivery.calculate_total()
        expected_total = product.price * 2
        assert delivery.total_amount == expected_total
    
    def test_delivery_status_choices(self, deal):
        """Test delivery status choices"""
        delivery = Delivery.objects.create(
            deal=deal,
            delivery_address='Test Address',
            status=Delivery.Status.CONFIRMED,
            driver_profile=None
        )
        assert delivery.status == Delivery.Status.CONFIRMED
    
    def test_delivery_get_driver_info_with_profile(self, delivery, driver_user):
        """Test getting driver info when driver_profile is set"""
        delivery.driver_profile = driver_user.driver_profile
        # Manual fields should be None when using system driver
        delivery.driver_name = None
        delivery.driver_phone = None
        delivery.driver_vehicle_type = None
        delivery.driver_vehicle_plate = None
        delivery.driver_license_number = None
        delivery.save()
        driver_info = delivery.get_driver_info()
        assert driver_info is not None
        assert driver_info['is_system_driver'] is True
        assert driver_info['name'] is not None
    
    def test_delivery_get_driver_info_manual(self, delivery):
        """Test getting driver info when manual driver fields are set (3rd party)"""
        delivery.driver_profile = None
        delivery.driver_name = 'John Doe'
        delivery.driver_phone = '1234567890'
        delivery.driver_vehicle_type = 'Van'
        delivery.driver_vehicle_plate = 'ABC123'
        delivery.driver_license_number = 'DL123456'
        delivery.save()
        driver_info = delivery.get_driver_info()
        assert driver_info is not None
        assert driver_info['is_system_driver'] is False
        assert driver_info['name'] == 'John Doe'
    
    def test_delivery_get_driver_info_none(self, delivery):
        """Test getting driver info when no driver is set"""
        delivery.driver_profile = None
        delivery.driver_name = None
        delivery.save()
        driver_info = delivery.get_driver_info()
        assert driver_info is None


@pytest.mark.django_db
class TestDeliveryItemModel:
    """Test DeliveryItem model"""
    
    def test_create_delivery_item(self, delivery, product):
        """Test creating a delivery item"""
        item = DeliveryItem.objects.create(
            delivery=delivery,
            product=product,
            quantity=5,
            unit_price=product.price
        )
        assert item.delivery == delivery
        assert item.product == product
        assert item.quantity == 5
        assert item.unit_price == product.price
        assert item.total_price == product.price * 5
    
    def test_delivery_item_total_price(self, delivery, product):
        """Test delivery item total price calculation"""
        item = DeliveryItem.objects.create(
            delivery=delivery,
            product=product,
            quantity=3,
            unit_price=Decimal('10.50')
        )
        expected_total = Decimal('10.50') * 3
        assert item.total_price == expected_total
    
    def test_delivery_item_auto_unit_price(self, delivery, product):
        """Test delivery item auto unit price from product"""
        item = DeliveryItem(
            delivery=delivery,
            product=product,
            quantity=2
        )
        item.save()
        assert item.unit_price == product.price
    
    def test_delivery_item_str(self, delivery_item):
        """Test delivery item string representation"""
        assert str(delivery_item) == f"{delivery_item.product.name} x {delivery_item.quantity}"
