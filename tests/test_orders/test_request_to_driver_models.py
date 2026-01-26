"""
Tests for RequestToDriver model
"""
import pytest
from decimal import Decimal
from src.orders.models import Deal, RequestToDriver


@pytest.mark.django_db
class TestRequestToDriverModel:
    """Test RequestToDriver model"""
    
    def test_create_request(self, deal, driver_user):
        """Test creating a driver request"""
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
        """Test supplier can approve request"""
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        # Supplier should be able to approve
        assert request.can_approve(supplier_user) is True
    
    def test_can_approve_seller(self, deal, seller_user, driver_user):
        """Test seller can approve request"""
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        # Seller should be able to approve
        assert request.can_approve(seller_user) is True
    
    def test_can_approve_driver(self, deal, driver_user):
        """Test driver can approve request"""
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        # Driver should be able to approve
        assert request.can_approve(driver_user) is True
    
    def test_can_approve_unauthorized(self, deal, driver_user, api_client):
        """Test unauthorized user cannot approve"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Create another user (not supplier, seller, or driver)
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
        
        # Other user should not be able to approve
        assert request.can_approve(other_user) is False
    
    def test_is_fully_approved_all_parties(self, deal, driver_user):
        """Test is_fully_approved when all 3 parties approve"""
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        assert request.is_fully_approved() is False  # Not yet approved
        
        request.supplier_approved = True
        request.save()
        assert request.is_fully_approved() is False  # Still missing seller and driver
        
        request.seller_approved = True
        request.save()
        assert request.is_fully_approved() is False  # Still missing driver
        
        request.driver_approved = True
        request.save()
        assert request.is_fully_approved() is True  # All 3 approved
    
    def test_accept_request(self, deal, driver_user):
        """Test accepting a fully approved request"""
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
        """Test accepting a request that is not fully approved should raise error"""
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            supplier_approved=True,
            seller_approved=True,
            driver_approved=False,  # Driver not approved
            created_by=deal.seller.user
        )
        
        assert request.is_fully_approved() is False
        
        with pytest.raises(ValueError, match="Request must be fully approved"):
            request.accept(Decimal('150.00'))
    
    def test_unique_together_deal_driver(self, deal, driver_user):
        """Test that same driver cannot have multiple requests for same deal"""
        RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        # Try to create another request for same deal and driver
        with pytest.raises(Exception):  # IntegrityError
            RequestToDriver.objects.create(
                deal=deal,
                driver=driver_user.driver_profile,
                requested_price=Decimal('200.00'),
                created_by=deal.seller.user
            )
    
    def test_3rd_party_delivery_handler(self, deal, driver_user):
        """Test that requests are only valid for SYSTEM_DRIVER delivery_handler"""
        # Change deal to 3rd party
        deal.delivery_handler = Deal.DeliveryHandler.SUPPLIER
        deal.save()
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        # Should not be able to approve for 3rd party deliveries
        assert request.can_approve(deal.seller.user) is False
        assert request.is_fully_approved() is False
