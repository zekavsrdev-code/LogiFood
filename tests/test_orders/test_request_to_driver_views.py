"""
Tests for RequestToDriver views
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import status
from src.orders.models import Deal, RequestToDriver

User = get_user_model()


@pytest.mark.django_db
class TestRequestToDriverViews:
    """Test RequestToDriver views"""
    
    def test_list_requests_as_driver(self, driver_client, deal, driver_user):
        """Test listing requests as driver"""
        from src.orders.models import RequestToDriver
        
        # Create a request for this driver
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        response = driver_client.get('/api/orders/driver-requests/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']['results']) == 1
    
    def test_list_requests_as_supplier(self, supplier_client, deal, driver_user):
        """Test listing requests as supplier"""
        from src.orders.models import RequestToDriver
        
        # Create a request
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.supplier.user
        )
        
        response = supplier_client.get('/api/orders/driver-requests/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_requests_as_seller(self, seller_client, deal, driver_user):
        """Test listing requests as seller"""
        from src.orders.models import RequestToDriver
        
        # Create a request
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        response = seller_client.get('/api/orders/driver-requests/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_retrieve_request(self, driver_client, deal, driver_user):
        """Test retrieving a specific request"""
        from src.orders.models import RequestToDriver
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        response = driver_client.get(f'/api/orders/driver-requests/{request.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['id'] == request.id
    
    def test_propose_price_as_driver(self, driver_client, deal, driver_user):
        """Test driver proposing a price"""
        from src.orders.models import RequestToDriver
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        response = driver_client.put(
            f'/api/orders/driver-requests/{request.id}/propose_price/',
            {'proposed_price': '175.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        request.refresh_from_db()
        assert request.driver_proposed_price == Decimal('175.00')
        assert request.status == RequestToDriver.Status.DRIVER_PROPOSED
    
    def test_propose_price_unauthorized(self, supplier_client, deal, driver_user):
        """Test proposing price as non-driver"""
        from src.orders.models import RequestToDriver
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        response = supplier_client.put(
            f'/api/orders/driver-requests/{request.id}/propose_price/',
            {'proposed_price': '175.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_approve_as_supplier(self, supplier_client, deal, driver_user, supplier_user):
        """Test supplier approving a request"""
        from src.orders.models import RequestToDriver
        
        # Ensure deal belongs to supplier
        deal.supplier = supplier_user.supplier_profile
        deal.save()
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        response = supplier_client.put(
            f'/api/orders/driver-requests/{request.id}/approve/',
            {'final_price': '150.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        request.refresh_from_db()
        assert request.supplier_approved is True
    
    def test_approve_as_seller(self, seller_client, deal, driver_user, seller_user):
        """Test seller approving a request"""
        from src.orders.models import RequestToDriver
        
        # Ensure deal belongs to seller
        deal.seller = seller_user.seller_profile
        deal.save()
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        response = seller_client.put(
            f'/api/orders/driver-requests/{request.id}/approve/',
            {'final_price': '150.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        request.refresh_from_db()
        assert request.seller_approved is True
    
    def test_approve_as_driver(self, driver_client, deal, driver_user):
        """Test driver approving a request"""
        from src.orders.models import RequestToDriver
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        response = driver_client.put(
            f'/api/orders/driver-requests/{request.id}/approve/',
            {'final_price': '150.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        request.refresh_from_db()
        assert request.driver_approved is True
    
    def test_fully_approved_all_parties(self, supplier_client, seller_client, driver_client, deal, driver_user, supplier_user, seller_user):
        """Test all 3 parties approving a request"""
        from src.orders.models import RequestToDriver
        
        # Ensure deal belongs to supplier and seller
        deal.supplier = supplier_user.supplier_profile
        deal.seller = seller_user.seller_profile
        deal.delivery_handler = Deal.DeliveryHandler.SYSTEM_DRIVER
        deal.save()
        
        # Refresh deal to ensure all changes are saved
        deal.refresh_from_db()
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        # Refresh request to ensure it has the latest deal reference
        request.refresh_from_db()
        
        # Supplier approves
        response = supplier_client.put(
            f'/api/orders/driver-requests/{request.id}/approve/',
            {'final_price': '150.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        request.refresh_from_db()
        assert request.supplier_approved is True
        assert request.status != RequestToDriver.Status.ACCEPTED  # Not yet fully approved
        
        # Seller approves
        response = seller_client.put(
            f'/api/orders/driver-requests/{request.id}/approve/',
            {'final_price': '150.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        request.refresh_from_db()
        assert request.seller_approved is True
        assert request.status != RequestToDriver.Status.ACCEPTED  # Still not fully approved (driver missing)
        
        # Driver approves
        response = driver_client.put(
            f'/api/orders/driver-requests/{request.id}/approve/',
            {'final_price': '150.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        request.refresh_from_db()
        assert request.driver_approved is True
        assert request.status == RequestToDriver.Status.ACCEPTED  # Now fully approved
        assert request.final_price == Decimal('150.00')
        
        # Check that driver is assigned to deal
        deal.refresh_from_db()
        assert deal.driver == driver_user.driver_profile
        assert deal.status == Deal.Status.DEALING
    
    def test_reject_request(self, supplier_client, deal, driver_user, supplier_user):
        """Test rejecting a request"""
        from src.orders.models import RequestToDriver
        
        # Ensure deal belongs to supplier
        deal.supplier = supplier_user.supplier_profile
        deal.save()
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        response = supplier_client.put(
            f'/api/orders/driver-requests/{request.id}/reject/',
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        request.refresh_from_db()
        assert request.status == RequestToDriver.Status.REJECTED
    
    def test_approve_unauthorized(self, api_client, deal, driver_user):
        """Test approving without authentication"""
        from src.orders.models import RequestToDriver
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        response = api_client.put(
            f'/api/orders/driver-requests/{request.id}/approve/',
            {'final_price': '150.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_propose_price_invalid_status(self, driver_client, deal, driver_user):
        """Test proposing price for request in invalid status"""
        from src.orders.models import RequestToDriver
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            status=RequestToDriver.Status.ACCEPTED,  # Already accepted
            created_by=deal.seller.user
        )
        
        response = driver_client.put(
            f'/api/orders/driver-requests/{request.id}/propose_price/',
            {'proposed_price': '175.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
