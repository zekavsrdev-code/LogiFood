"""Tests for Order services"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.orders.models import Deal, Delivery, RequestToDriver
from apps.orders.services import (
    DealService,
    DeliveryService,
    RequestToDriverService,
)
from apps.core.exceptions import BusinessLogicError
from rest_framework import status

User = get_user_model()

pytestmark = pytest.mark.unit


@pytest.mark.django_db
class TestDealService:
    """Test DealService"""
    
    def test_get_user_deals_as_supplier(self, supplier_user, deal):
        deals = DealService.get_user_deals(supplier_user)
        assert deal in deals
        assert deals.count() >= 1
    
    def test_get_user_deals_as_seller(self, seller_user, deal):
        deals = DealService.get_user_deals(seller_user)
        assert deal in deals
        assert deals.count() >= 1
    
    def test_get_user_deals_unauthorized(self):
        other_user = User.objects.create_user(
            username='other_user',
            password='pass123',
            role=User.Role.SELLER
        )
        deals = DealService.get_user_deals(other_user)
        assert deals.count() == 0
    
    def test_can_user_access_deal_supplier(self, supplier_user, deal):
        assert DealService.can_user_access_deal(deal, supplier_user) is True
    
    def test_can_user_access_deal_seller(self, seller_user, deal):
        assert DealService.can_user_access_deal(deal, seller_user) is True
    
    def test_can_user_access_deal_unauthorized(self, deal):
        other_user = User.objects.create_user(
            username='other_user',
            password='pass123',
            role=User.Role.SELLER
        )
        assert DealService.can_user_access_deal(deal, other_user) is False
    
    def test_create_deal(self, seller_user, supplier_user, product):
        validated_data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'seller_id': seller_user.seller_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        deal = DealService.create_deal(seller_user, validated_data)
        assert deal.seller == seller_user.seller_profile
        assert deal.supplier == supplier_user.supplier_profile
        assert deal.delivery_handler == Deal.DeliveryHandler.SYSTEM_DRIVER
        assert deal.items.count() == 1
    
    def test_create_deal_with_3rd_party(self, seller_user, supplier_user, product):
        validated_data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'seller_id': seller_user.seller_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SELLER,
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        deal = DealService.create_deal(seller_user, validated_data)
        assert deal.delivery_handler == Deal.DeliveryHandler.SELLER
        assert deal.delivery_cost_split == 50
        # Driver is now in RequestToDriver, not Deal
        assert deal.driver_requests.filter(status=RequestToDriver.Status.ACCEPTED).count() == 0
    
    def test_update_deal_status(self, seller_user, deal):
        deal.seller_approved = True
        deal.supplier_approved = True
        deal.save()
        updated_deal = DealService.update_deal_status(deal, seller_user, Deal.Status.DONE)
        assert updated_deal.status == Deal.Status.DONE

    def test_update_deal_status_requires_both_approvals(self, seller_user, deal):
        with pytest.raises(BusinessLogicError) as exc:
            DealService.update_deal_status(deal, seller_user, Deal.Status.DONE)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Both seller and supplier' in str(exc.value.detail)

    def test_update_deal_status_looking_for_driver_requires_approvals(self, seller_user, deal):
        with pytest.raises(BusinessLogicError) as exc:
            DealService.update_deal_status(deal, seller_user, Deal.Status.LOOKING_FOR_DRIVER)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_deal_status_unauthorized(self, deal):
        deal.seller_approved = True
        deal.supplier_approved = True
        deal.save()
        other_user = User.objects.create_user(
            username='other_user',
            password='pass123',
            role=User.Role.SELLER
        )
        with pytest.raises(BusinessLogicError) as exc:
            DealService.update_deal_status(deal, other_user, Deal.Status.DONE)
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN

    def test_approve_deal_seller(self, seller_user, deal):
        assert deal.seller_approved is False
        updated = DealService.approve_deal(deal, seller_user)
        updated.refresh_from_db()
        assert updated.seller_approved is True
        assert updated.supplier_approved is False

    def test_approve_deal_supplier(self, supplier_user, deal):
        assert deal.supplier_approved is False
        updated = DealService.approve_deal(deal, supplier_user)
        updated.refresh_from_db()
        assert updated.supplier_approved is True
        assert updated.seller_approved is False

    def test_update_deal_clears_other_approval(self, seller_user, supplier_user, deal):
        deal.supplier_approved = True
        deal.save()
        updated = DealService.update_deal(deal, seller_user, delivery_cost_split=60)
        updated.refresh_from_db()
        assert updated.delivery_cost_split == 60
        assert updated.supplier_approved is False
        assert updated.seller_approved is False

    def test_update_deal_non_dealing_rejected(self, seller_user, deal):
        deal.status = Deal.Status.LOOKING_FOR_DRIVER
        deal.seller_approved = True
        deal.supplier_approved = True
        deal.save()
        with pytest.raises(BusinessLogicError) as exc:
            DealService.update_deal(deal, seller_user, delivery_cost_split=60)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_assign_driver_to_deal(self, seller_user, deal, driver_user):
        deal.status = Deal.Status.LOOKING_FOR_DRIVER
        deal.seller_approved = True
        deal.supplier_approved = True
        deal.save()
        
        updated_deal = DealService.assign_driver_to_deal(deal, seller_user, driver_user.driver_profile.id)
        # Driver is now in RequestToDriver, not Deal
        accepted_request = updated_deal.driver_requests.filter(status=RequestToDriver.Status.ACCEPTED).first()
        assert accepted_request is not None
        assert accepted_request.driver == driver_user.driver_profile
        # assign_driver_to_deal auto-approves all parties, so if deal has both_parties_approved, it becomes DONE
        assert updated_deal.status == Deal.Status.DONE
    
    def test_request_driver_for_deal(self, seller_user, deal, driver_user):
        deal.status = Deal.Status.LOOKING_FOR_DRIVER
        deal.delivery_handler = Deal.DeliveryHandler.SYSTEM_DRIVER
        deal.seller_approved = True
        deal.supplier_approved = True
        deal.save()
        
        request = DealService.request_driver_for_deal(
            deal, 
            seller_user, 
            driver_user.driver_profile.id, 
            150.00
        )
        assert request.deal == deal
        assert request.driver == driver_user.driver_profile
        assert request.requested_price == Decimal('150.00')
        assert request.status == RequestToDriver.Status.PENDING
        # Seller created the request, so seller_approved should be True
        assert request.seller_approved is True
        assert request.supplier_approved is False
        assert request.driver_approved is False
    
    def test_request_driver_for_deal_by_supplier(self, supplier_user, deal, driver_user):
        """Test that supplier can create request and auto-approve"""
        deal.status = Deal.Status.LOOKING_FOR_DRIVER
        deal.delivery_handler = Deal.DeliveryHandler.SYSTEM_DRIVER
        deal.seller_approved = True
        deal.supplier_approved = True
        deal.save()
        
        request = DealService.request_driver_for_deal(
            deal, 
            supplier_user, 
            driver_user.driver_profile.id, 
            200.00
        )
        assert request.deal == deal
        assert request.driver == driver_user.driver_profile
        assert request.requested_price == Decimal('200.00')
        assert request.status == RequestToDriver.Status.PENDING
        # Supplier created the request, so supplier_approved should be True
        assert request.supplier_approved is True
        assert request.seller_approved is False
        assert request.driver_approved is False
    
    def test_request_driver_for_3rd_party_deal(self, seller_user, deal, driver_user):
        deal.status = Deal.Status.LOOKING_FOR_DRIVER
        deal.delivery_handler = Deal.DeliveryHandler.SUPPLIER
        deal.save()
        
        with pytest.raises(BusinessLogicError) as exc:
            DealService.request_driver_for_deal(deal, seller_user, driver_user.driver_profile.id, 150.00)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_complete_deal(self, seller_user, deal, product):
        from apps.orders.models import DealItem
        DealItem.objects.create(
            deal=deal,
            product=product,
            quantity=2,
            unit_price=product.price
        )
        deal.seller_approved = True
        deal.supplier_approved = True
        deal.status = Deal.Status.DONE
        deal.delivery_count = 1
        deal.save()
        
        deliveries = DealService.complete_deal(
            deal,
            seller_user,
            'Test Address',
            'Test note',
            100
        )
        assert len(deliveries) == 1
        assert deliveries[0].deal == deal
        assert deliveries[0].delivery_address == 'Test Address'
        assert deliveries[0].status == Delivery.Status.ESTIMATED


@pytest.mark.django_db
class TestDeliveryService:
    """Test DeliveryService"""
    
    def test_get_user_deliveries_as_supplier(self, supplier_user, delivery):
        deliveries = DeliveryService.get_user_deliveries(supplier_user)
        assert delivery in deliveries
    
    def test_get_user_deliveries_as_seller(self, seller_user, delivery):
        deliveries = DeliveryService.get_user_deliveries(seller_user)
        assert delivery in deliveries
    
    def test_get_user_deliveries_as_driver(self, driver_user, delivery):
        delivery.driver_profile = driver_user.driver_profile
        delivery.save()
        deliveries = DeliveryService.get_user_deliveries(driver_user)
        assert delivery in deliveries
    
    def test_can_user_access_delivery_supplier(self, supplier_user, delivery):
        assert DeliveryService.can_user_access_delivery(delivery, supplier_user) is True
    
    def test_can_user_access_delivery_seller(self, seller_user, delivery):
        assert DeliveryService.can_user_access_delivery(delivery, seller_user) is True
    
    def test_can_user_access_delivery_driver(self, driver_user, delivery):
        delivery.driver_profile = driver_user.driver_profile
        delivery.save()
        assert DeliveryService.can_user_access_delivery(delivery, driver_user) is True
    
    def test_update_delivery_status(self, supplier_user, delivery):
        updated_delivery = DeliveryService.update_delivery_status(
            delivery, 
            supplier_user, 
            Delivery.Status.CONFIRMED
        )
        assert updated_delivery.status == Delivery.Status.CONFIRMED
    
    def test_update_delivery_status_unauthorized(self, seller_user, delivery):
        with pytest.raises(BusinessLogicError) as exc:
            DeliveryService.update_delivery_status(delivery, seller_user, Delivery.Status.CONFIRMED)
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    
    def test_assign_driver_to_delivery(self, supplier_user, delivery, driver_user):
        updated_delivery = DeliveryService.assign_driver_to_delivery(
            delivery,
            supplier_user,
            driver_user.driver_profile.id
        )
        assert updated_delivery.driver_profile == driver_user.driver_profile
        assert updated_delivery.status == Delivery.Status.READY
    
    def test_get_available_deliveries(self, driver_user, delivery):
        delivery.status = Delivery.Status.READY
        delivery.driver_profile = None
        delivery.driver_name = None
        delivery.save()
        
        deliveries = DeliveryService.get_available_deliveries(driver_user)
        assert delivery in deliveries
    
    def test_accept_delivery(self, driver_user, delivery):
        delivery.status = Delivery.Status.READY
        delivery.driver_profile = None
        delivery.driver_name = None
        delivery.save()
        
        updated_delivery = DeliveryService.accept_delivery(delivery, driver_user)
        assert updated_delivery.driver_profile == driver_user.driver_profile
        assert updated_delivery.status == Delivery.Status.PICKED_UP
    
    def test_accept_delivery_not_driver(self, seller_user, delivery):
        with pytest.raises(BusinessLogicError) as exc:
            DeliveryService.accept_delivery(delivery, seller_user)
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    
    def test_accept_delivery_already_assigned(self, driver_user, delivery):
        delivery.driver_profile = driver_user.driver_profile
        delivery.save()
        
        with pytest.raises(BusinessLogicError) as exc:
            DeliveryService.accept_delivery(delivery, driver_user)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestRequestToDriverService:
    """Test RequestToDriverService"""
    
    def test_get_user_requests_as_driver(self, driver_user, deal):
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        requests = RequestToDriverService.get_user_requests(driver_user)
        assert request in requests
    
    def test_get_user_requests_as_supplier(self, supplier_user, deal, driver_user):
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.supplier.user
        )
        
        requests = RequestToDriverService.get_user_requests(supplier_user)
        assert request in requests
    
    def test_propose_price(self, driver_user, deal):
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        updated_request = RequestToDriverService.propose_price(request, driver_user, 175.00)
        assert updated_request.driver_proposed_price == Decimal('175.00')
        assert updated_request.status == RequestToDriver.Status.DRIVER_PROPOSED
    
    def test_propose_price_unauthorized(self, supplier_user, deal, driver_user):
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        with pytest.raises(BusinessLogicError) as exc:
            RequestToDriverService.propose_price(request, supplier_user, 175.00)
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    
    def test_approve_request_supplier(self, supplier_user, deal, driver_user):
        deal.supplier = supplier_user.supplier_profile
        deal.save()
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        updated_request = RequestToDriverService.approve_request(request, supplier_user, 150.00)
        assert updated_request.supplier_approved is True
    
    def test_approve_request_seller(self, seller_user, deal, driver_user):
        deal.seller = seller_user.seller_profile
        deal.save()
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        updated_request = RequestToDriverService.approve_request(request, seller_user, 150.00)
        assert updated_request.seller_approved is True
    
    def test_approve_request_driver(self, driver_user, deal):
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        updated_request = RequestToDriverService.approve_request(request, driver_user, 150.00)
        assert updated_request.driver_approved is True
    
    def test_fully_approved_all_parties(self, supplier_user, seller_user, driver_user, deal):
        deal.supplier = supplier_user.supplier_profile
        deal.seller = seller_user.seller_profile
        deal.delivery_handler = Deal.DeliveryHandler.SYSTEM_DRIVER
        # Set both parties approved for deal to test DONE status transition
        deal.seller_approved = True
        deal.supplier_approved = True
        deal.save()
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        RequestToDriverService.approve_request(request, supplier_user, 150.00)
        request.refresh_from_db()
        assert request.supplier_approved is True
        
        RequestToDriverService.approve_request(request, seller_user, 150.00)
        request.refresh_from_db()
        assert request.seller_approved is True
        
        RequestToDriverService.approve_request(request, driver_user, 150.00)
        request.refresh_from_db()
        assert request.driver_approved is True
        assert request.status == RequestToDriver.Status.ACCEPTED
        
        deal.refresh_from_db()
        # Driver is now in RequestToDriver, not Deal
        accepted_request = deal.driver_requests.filter(status=RequestToDriver.Status.ACCEPTED).first()
        assert accepted_request is not None
        assert accepted_request.driver == driver_user.driver_profile
        # Deal should be DONE if both parties approved
        assert deal.status == Deal.Status.DONE
    
    def test_reject_request(self, supplier_user, deal, driver_user):
        deal.supplier = supplier_user.supplier_profile
        deal.save()
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        updated_request = RequestToDriverService.reject_request(request, supplier_user)
        assert updated_request.status == RequestToDriver.Status.REJECTED
    
    def test_reject_request_unauthorized(self, deal, driver_user):
        other_user = User.objects.create_user(
            username='other_user',
            password='pass123',
            role=User.Role.SELLER
        )
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        with pytest.raises(BusinessLogicError) as exc:
            RequestToDriverService.reject_request(request, other_user)
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_pending_approvals_all_pending(self, deal, driver_user):
        """Test get_pending_approvals when no one has approved"""
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        pending = RequestToDriverService.get_pending_approvals(request)
        assert len(pending) == 3
        assert 'supplier' in pending
        assert 'seller' in pending
        assert 'driver' in pending
    
    def test_get_pending_approvals_partial(self, supplier_user, deal, driver_user):
        """Test get_pending_approvals when some parties have approved"""
        deal.supplier = supplier_user.supplier_profile
        deal.save()
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            supplier_approved=True,
            created_by=deal.seller.user
        )
        
        pending = RequestToDriverService.get_pending_approvals(request)
        assert len(pending) == 2
        assert 'supplier' not in pending
        assert 'seller' in pending
        assert 'driver' in pending
    
    def test_get_pending_approvals_all_approved(self, supplier_user, seller_user, driver_user, deal):
        """Test get_pending_approvals when all parties have approved"""
        deal.supplier = supplier_user.supplier_profile
        deal.seller = seller_user.seller_profile
        deal.save()
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            supplier_approved=True,
            seller_approved=True,
            driver_approved=True,
            created_by=deal.seller.user
        )
        
        pending = RequestToDriverService.get_pending_approvals(request)
        assert len(pending) == 0
    
    def test_propose_price_from_counter_offered_status(self, driver_user, deal):
        """Test propose_price when status is COUNTER_OFFERED (for future use)"""
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            status=RequestToDriver.Status.COUNTER_OFFERED,
            created_by=deal.seller.user
        )
        
        updated_request = RequestToDriverService.propose_price(request, driver_user, 200.00)
        assert updated_request.driver_proposed_price == Decimal('200.00')
        assert updated_request.status == RequestToDriver.Status.DRIVER_PROPOSED
    
    def test_counter_offer_flow_with_driver_proposed_price(self, supplier_user, seller_user, driver_user, deal):
        """Test full counter offer flow: request → driver proposes → all approve"""
        deal.supplier = supplier_user.supplier_profile
        deal.seller = seller_user.seller_profile
        deal.delivery_handler = Deal.DeliveryHandler.SYSTEM_DRIVER
        deal.save()
        
        # 1. Create request with initial price
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        assert request.status == RequestToDriver.Status.PENDING
        
        # 2. Driver proposes counter offer
        updated_request = RequestToDriverService.propose_price(request, driver_user, 200.00)
        assert updated_request.driver_proposed_price == Decimal('200.00')
        assert updated_request.status == RequestToDriver.Status.DRIVER_PROPOSED
        
        # 3. All parties approve the driver's proposed price
        RequestToDriverService.approve_request(updated_request, supplier_user, 200.00)
        updated_request.refresh_from_db()
        assert updated_request.supplier_approved is True
        
        RequestToDriverService.approve_request(updated_request, seller_user, 200.00)
        updated_request.refresh_from_db()
        assert updated_request.seller_approved is True
        
        RequestToDriverService.approve_request(updated_request, driver_user, 200.00)
        updated_request.refresh_from_db()
        assert updated_request.driver_approved is True
        assert updated_request.status == RequestToDriver.Status.ACCEPTED
        assert updated_request.final_price == Decimal('200.00')  # Driver's proposed price is used
    
    def test_propose_price_invalid_status(self, driver_user, deal):
        """Test propose_price fails when status is not PENDING or COUNTER_OFFERED"""
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            status=RequestToDriver.Status.ACCEPTED,
            created_by=deal.seller.user
        )
        
        with pytest.raises(BusinessLogicError) as exc:
            RequestToDriverService.propose_price(request, driver_user, 175.00)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_propose_price_rejected_status(self, driver_user, deal):
        """Test propose_price fails when status is REJECTED"""
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            status=RequestToDriver.Status.REJECTED,
            created_by=deal.seller.user
        )
        
        with pytest.raises(BusinessLogicError) as exc:
            RequestToDriverService.propose_price(request, driver_user, 175.00)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
