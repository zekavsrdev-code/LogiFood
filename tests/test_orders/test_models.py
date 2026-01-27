"""Tests for Order models"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.orders.models import Deal, DealItem, Delivery, DeliveryItem, RequestToDriver

User = get_user_model()

pytestmark = pytest.mark.unit


@pytest.mark.django_db
class TestDealModel:
    """Test Deal model"""
    
    def test_create_deal(self, seller_user, supplier_user):
        deal = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
            status=Deal.Status.DEALING
        )
        assert deal.seller == seller_user.seller_profile
        assert deal.supplier == supplier_user.supplier_profile
        assert deal.status == Deal.Status.DEALING
        assert deal.delivery_count == 1
        assert deal.delivery_cost_split == 50
    
    def test_deal_str(self, deal):
        assert 'Deal #' in str(deal)
        assert deal.seller.business_name in str(deal)
        assert deal.supplier.company_name in str(deal)
    
    def test_deal_calculate_total(self, deal, product):
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
        assert deal.get_actual_delivery_count() == 0
        assert deal.delivery_count == 1
        
        Delivery.objects.create(
            deal=deal,
            delivery_address='Test Address',
            status=Delivery.Status.ESTIMATED,
            supplier_share=100,
            driver_profile=None
        )
        assert deal.get_actual_delivery_count() == 1
        assert deal.can_create_more_deliveries() is False
    
    def test_deal_can_create_more_deliveries(self, deal):
        deal.delivery_count = 3
        deal.save()
        
        assert deal.can_create_more_deliveries() is True
        
        for i in range(2):
            Delivery.objects.create(
                deal=deal,
                delivery_address=f'Test Address {i}',
                status=Delivery.Status.ESTIMATED,
                supplier_share=100,
                driver_profile=None
            )
        
        assert deal.get_actual_delivery_count() == 2
        assert deal.can_create_more_deliveries() is True
        
        Delivery.objects.create(
            deal=deal,
            delivery_address='Test Address 3',
            status=Delivery.Status.ESTIMATED,
            supplier_share=100,
            driver_profile=None
        )
        
        assert deal.get_actual_delivery_count() == 3
        assert deal.can_create_more_deliveries() is False
    
    def test_deal_delivery_cost_split_default(self, seller_user, supplier_user):
        deal = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
            status=Deal.Status.DEALING
        )
        assert deal.delivery_cost_split == 50
        assert deal.delivery_count == 1
    
    def test_deal_delivery_cost_split_custom_value(self, seller_user, supplier_user):
        deal = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
            delivery_cost_split=75,
            status=Deal.Status.DEALING
        )
        assert deal.delivery_cost_split == 75
    
    def test_deal_delivery_cost_split_with_system_driver(self, seller_user, supplier_user, driver_user):
        deal = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            driver=driver_user.driver_profile,
            delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
            delivery_cost_split=60,
            status=Deal.Status.DEALING
        )
        assert deal.delivery_handler == Deal.DeliveryHandler.SYSTEM_DRIVER
        assert deal.delivery_cost_split == 60
        assert deal.driver == driver_user.driver_profile
    
    def test_deal_delivery_cost_split_boundary_values(self, seller_user, supplier_user):
        deal1 = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
            delivery_cost_split=0,
            status=Deal.Status.DEALING
        )
        assert deal1.delivery_cost_split == 0
        
        deal2 = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
            delivery_cost_split=100,
            status=Deal.Status.DEALING
        )
        assert deal2.delivery_cost_split == 100


@pytest.mark.django_db
class TestDeliveryModel:
    """Test Delivery model"""
    
    def test_create_delivery_from_deal(self, deal):
        initial_actual_count = deal.get_actual_delivery_count()
        planned_count = deal.delivery_count
        delivery = Delivery.objects.create(
            deal=deal,
            delivery_address='Test Address',
            delivery_note='Test note',
            status=Delivery.Status.ESTIMATED,
            supplier_share=100,
            driver_profile=None,
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
        assert delivery.is_3rd_party_delivery is True
        assert delivery.status == Delivery.Status.ESTIMATED
        assert delivery.total_amount == Decimal('0.00')
        deal.refresh_from_db()
        assert deal.get_actual_delivery_count() == initial_actual_count + 1
        assert deal.delivery_count == planned_count
    
    def test_delivery_validation_error_no_deal(self):
        delivery = Delivery(
            delivery_address='Test Address',
            status=Delivery.Status.ESTIMATED
        )
        with pytest.raises(ValidationError):
            delivery.clean()
    
    def test_delivery_validation_error_driver_profile_and_manual_fields(self, deal, driver_user):
        delivery = Delivery(
            deal=deal,
            delivery_address='Test Address',
            status=Delivery.Status.ESTIMATED,
            driver_profile=driver_user.driver_profile,
            driver_name='Manual Driver',
            driver_phone='1234567890'
        )
        with pytest.raises(ValidationError):
            delivery.clean()
    
    def test_delivery_supplier_share_validation(self, deal):
        delivery = Delivery(
            deal=deal,
            delivery_address='Test Address',
            supplier_share=150,
            status=Delivery.Status.ESTIMATED,
            driver_profile=None
        )
        with pytest.raises(ValidationError):
            delivery.clean()
    
    def test_delivery_str(self, delivery):
        assert 'Delivery #' in str(delivery)
        assert delivery.seller_profile.business_name in str(delivery)
    
    def test_delivery_calculate_total(self, delivery, product):
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
        delivery = Delivery.objects.create(
            deal=deal,
            delivery_address='Test Address',
            status=Delivery.Status.CONFIRMED,
            driver_profile=None
        )
        assert delivery.status == Delivery.Status.CONFIRMED
    
    def test_delivery_get_driver_info_with_profile(self, delivery, driver_user):
        delivery.driver_profile = driver_user.driver_profile
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
        delivery.driver_profile = None
        delivery.driver_name = None
        delivery.save()
        driver_info = delivery.get_driver_info()
        assert driver_info is None


@pytest.mark.django_db
class TestDeliveryItemModel:
    """Test DeliveryItem model"""
    
    def test_create_delivery_item(self, delivery, product):
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
        item = DeliveryItem.objects.create(
            delivery=delivery,
            product=product,
            quantity=3,
            unit_price=Decimal('10.50')
        )
        expected_total = Decimal('10.50') * 3
        assert item.total_price == expected_total
    
    def test_delivery_item_auto_unit_price(self, delivery, product):
        item = DeliveryItem(
            delivery=delivery,
            product=product,
            quantity=2
        )
        item.save()
        assert item.unit_price == product.price
    
    def test_delivery_item_str(self, delivery_item):
        assert str(delivery_item) == f"{delivery_item.product.name} x {delivery_item.quantity}"


@pytest.mark.django_db
class TestRequestToDriverModel:
    """Test RequestToDriver model"""
    
    def test_create_request(self, deal, driver_user):
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        assert request.deal == deal
        assert request.driver == driver_user.driver_profile
        assert request.requested_price == Decimal('150.00')
        assert request.status == RequestToDriver.Status.PENDING
        assert request.supplier_approved is False
        assert request.seller_approved is False
        assert request.driver_approved is False
        assert request.created_by == deal.seller.user
    
    def test_can_approve_supplier(self, deal, supplier_user, driver_user):
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        assert request.can_approve(supplier_user) is True
    
    def test_can_approve_seller(self, deal, seller_user, driver_user):
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        assert request.can_approve(seller_user) is True
    
    def test_can_approve_driver(self, deal, driver_user):
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        assert request.can_approve(driver_user) is True
    
    def test_can_approve_unauthorized(self, deal, driver_user):
        other_user = User.objects.create_user(
            username='other_user',
            email='other@example.com',
            password='testpass123'
        )
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        assert request.can_approve(other_user) is False
    
    def test_is_fully_approved_all_parties(self, deal, driver_user):
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        assert request.is_fully_approved() is False
        
        request.supplier_approved = True
        request.save()
        assert request.is_fully_approved() is False
        
        request.seller_approved = True
        request.save()
        assert request.is_fully_approved() is False
        
        request.driver_approved = True
        request.save()
        assert request.is_fully_approved() is True
    
    def test_accept_request(self, deal, driver_user):
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            supplier_approved=True,
            seller_approved=True,
            driver_approved=True,
            created_by=deal.seller.user
        )
        
        assert request.is_fully_approved() is True
        
        request.accept(Decimal('150.00'))
        
        assert request.status == RequestToDriver.Status.ACCEPTED
        assert request.final_price == Decimal('150.00')
        
        deal.refresh_from_db()
        assert deal.driver == driver_user.driver_profile
        assert deal.status == Deal.Status.DEALING
    
    def test_accept_not_fully_approved(self, deal, driver_user):
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            supplier_approved=True,
            seller_approved=True,
            driver_approved=False,
            created_by=deal.seller.user
        )
        
        assert request.is_fully_approved() is False
        
        with pytest.raises(ValueError, match="Request must be fully approved"):
            request.accept(Decimal('150.00'))
    
    def test_unique_together_deal_driver(self, deal, driver_user):
        RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        with pytest.raises(Exception):
            RequestToDriver.objects.create(
                deal=deal,
                driver=driver_user.driver_profile,
                requested_price=Decimal('200.00'),
                created_by=deal.seller.user
            )
    
    def test_3rd_party_delivery_handler(self, deal, driver_user):
        deal.delivery_handler = Deal.DeliveryHandler.SUPPLIER
        deal.save()
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        assert request.can_approve(deal.seller.user) is False
        assert request.is_fully_approved() is False
