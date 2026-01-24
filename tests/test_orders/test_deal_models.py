"""
Tests for Deal model - delivery_cost_split field
"""
import pytest
from django.core.exceptions import ValidationError
from src.orders.models import Deal


@pytest.mark.django_db
class TestDealDeliveryCostSplit:
    """Test Deal delivery_cost_split field"""
    
    def test_deal_delivery_cost_split_default(self, seller_user, supplier_user):
        """Test that delivery_cost_split defaults to 50"""
        deal = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
            status=Deal.Status.DEALING
        )
        assert deal.delivery_cost_split == 50
        assert deal.delivery_count == 1  # Default is now 1
    
    def test_deal_delivery_cost_split_custom_value(self, seller_user, supplier_user):
        """Test setting custom delivery_cost_split value"""
        deal = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
            delivery_cost_split=75,  # Supplier pays 75%, seller pays 25%
            status=Deal.Status.DEALING
        )
        assert deal.delivery_cost_split == 75
    
    def test_deal_delivery_cost_split_with_system_driver(self, seller_user, supplier_user, driver_user):
        """Test delivery_cost_split with system driver"""
        deal = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            driver=driver_user.driver_profile,
            delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
            delivery_cost_split=60,  # Supplier pays 60%, seller pays 40%
            status=Deal.Status.DEALING
        )
        assert deal.delivery_handler == Deal.DeliveryHandler.SYSTEM_DRIVER
        assert deal.delivery_cost_split == 60
        assert deal.driver == driver_user.driver_profile
    
    def test_deal_delivery_cost_split_with_supplier_3rd_party(self, seller_user, supplier_user):
        """Test delivery_cost_split with supplier 3rd party (should be 50, not used)"""
        deal = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_handler=Deal.DeliveryHandler.SUPPLIER,
            delivery_cost_split=80,  # This should be reset to 50 for 3rd party
            status=Deal.Status.DEALING
        )
        # For 3rd party deliveries, delivery_cost_split is not used but stored as 50
        assert deal.delivery_handler == Deal.DeliveryHandler.SUPPLIER
        # Note: The serializer will reset this to 50, but model allows any value
        # The validation happens in serializer, not model
        assert deal.delivery_cost_split == 80  # Model allows it, serializer resets it
    
    def test_deal_delivery_cost_split_with_seller_3rd_party(self, seller_user, supplier_user):
        """Test delivery_cost_split with seller 3rd party (should be 50, not used)"""
        deal = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_handler=Deal.DeliveryHandler.SELLER,
            delivery_cost_split=30,  # This should be reset to 50 for 3rd party
            status=Deal.Status.DEALING
        )
        assert deal.delivery_handler == Deal.DeliveryHandler.SELLER
        # Model allows it, serializer resets it to 50
        assert deal.delivery_cost_split == 30  # Model allows it, serializer resets it
    
    def test_deal_delivery_cost_split_boundary_values(self, seller_user, supplier_user):
        """Test delivery_cost_split boundary values (0 and 100)"""
        # Test 0 (seller pays all)
        deal1 = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
            delivery_cost_split=0,
            status=Deal.Status.DEALING
        )
        assert deal1.delivery_cost_split == 0
        
        # Test 100 (supplier pays all)
        deal2 = Deal.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
            delivery_cost_split=100,
            status=Deal.Status.DEALING
        )
        assert deal2.delivery_cost_split == 100
