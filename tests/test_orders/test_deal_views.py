"""
Tests for Deal views
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import status
from src.orders.models import Deal, DealItem, Delivery

User = get_user_model()


@pytest.mark.django_db
class TestDealViews:
    """Test Deal views"""
    
    def test_list_deals_as_seller(self, seller_client, deal):
        """Test listing deals as seller"""
        response = seller_client.get('/api/orders/deals/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_deals_as_supplier(self, supplier_client, deal):
        """Test listing deals as supplier"""
        response = supplier_client.get('/api/orders/deals/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_deals_unauthorized(self, api_client):
        """Test listing deals without authentication"""
        response = api_client.get('/api/orders/deals/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_deal_as_seller(self, seller_client, supplier_user, product):
        """Test creating deal as seller"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
            'delivery_cost_split': 60,
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        response = seller_client.post('/api/orders/deals/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        deal_data = response.data['data']
        assert deal_data['delivery_cost_split'] == 60
    
    def test_create_deal_with_default_delivery_cost_split(self, seller_client, supplier_user, product):
        """Test creating deal with default delivery_cost_split"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        response = seller_client.post('/api/orders/deals/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        deal_data = response.data['data']
        assert deal_data['delivery_cost_split'] == 50  # Default
    
    def test_create_deal_delivery_cost_split_with_3rd_party(self, seller_client, supplier_user, product):
        """Test that delivery_cost_split is reset for 3rd party deliveries"""
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SELLER,  # 3rd party
            'delivery_cost_split': 80,  # Should be reset to 50
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        response = seller_client.post('/api/orders/deals/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        deal_data = response.data['data']
        assert deal_data['delivery_cost_split'] == 50  # Reset for 3rd party
    
    def test_retrieve_deal(self, seller_client, deal):
        """Test retrieving a deal"""
        response = seller_client.get(f'/api/orders/deals/{deal.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'delivery_cost_split' in response.data['data']
    
    def test_update_deal_status(self, seller_client, deal):
        """Test updating deal status"""
        data = {'status': Deal.Status.DONE}
        response = seller_client.put(
            f'/api/orders/deals/{deal.id}/update_status/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        deal.refresh_from_db()
        assert deal.status == Deal.Status.DONE
    
    def test_assign_driver_to_deal(self, seller_client, deal, driver_user):
        """Test assigning driver to deal"""
        # First set deal to LOOKING_FOR_DRIVER
        deal.status = Deal.Status.LOOKING_FOR_DRIVER
        deal.driver = None
        deal.save()
        
        data = {'driver_id': driver_user.driver_profile.id, 'requested_price': '150.00'}
        response = seller_client.put(
            f'/api/orders/deals/{deal.id}/assign_driver/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        deal.refresh_from_db()
        assert deal.driver == driver_user.driver_profile
        assert deal.status == Deal.Status.DEALING
    
    def test_request_driver_for_deal(self, seller_client, deal, driver_user):
        """Test requesting driver for deal"""
        # Set deal to LOOKING_FOR_DRIVER
        deal.status = Deal.Status.LOOKING_FOR_DRIVER
        deal.driver = None
        deal.delivery_handler = Deal.DeliveryHandler.SYSTEM_DRIVER
        deal.save()
        
        driver_user.driver_profile.is_available = True
        driver_user.driver_profile.save()
        
        data = {'driver_id': driver_user.driver_profile.id, 'requested_price': '150.00'}
        response = seller_client.put(
            f'/api/orders/deals/{deal.id}/request_driver/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        # Note: Driver is not directly assigned, a RequestToDriver is created instead
        # The deal status should remain LOOKING_FOR_DRIVER until all parties approve
    
    def test_request_driver_for_3rd_party_deal(self, seller_client, deal, driver_user):
        """Test requesting driver for 3rd party deal (should fail)"""
        # Set deal to 3rd party
        deal.status = Deal.Status.LOOKING_FOR_DRIVER
        deal.driver = None
        deal.delivery_handler = Deal.DeliveryHandler.SUPPLIER  # 3rd party
        deal.save()
        
        driver_user.driver_profile.is_available = True
        driver_user.driver_profile.save()
        
        data = {'driver_id': driver_user.driver_profile.id, 'requested_price': '150.00'}
        response = seller_client.put(
            f'/api/orders/deals/{deal.id}/request_driver/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert '3rd party' in response.data.get('message', '').lower()
    
    def test_complete_deal(self, seller_client, deal, product):
        """Test completing a deal and creating delivery"""
        # Add item to deal
        DealItem.objects.create(
            deal=deal,
            product=product,
            quantity=2,
            unit_price=product.price
        )
        
        # Set deal to DONE
        # delivery_count is 1 by default (each deal must have at least one delivery)
        # But we need to reset it to 1 to allow completion (since default is 1)
        deal.status = Deal.Status.DONE
        deal.delivery_count = 1  # Reset to default (1) to allow completion
        deal.save()
        
        data = {
            'delivery_address': 'Test Address',
            'delivery_note': 'Test note',
            'supplier_share': 100
        }
        response = seller_client.post(
            f'/api/orders/deals/{deal.id}/complete/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert 'deal' in response.data['data']
        assert 'deliveries' in response.data['data']  # Now returns 'deliveries' (plural) as multiple deliveries can be created
        assert 'created_count' in response.data['data']
        assert 'total_planned' in response.data['data']
        
        # Check that deliveries were created
        deal.refresh_from_db()
        assert len(response.data['data']['deliveries']) == 1  # delivery_count is 1, so 1 delivery created
        assert deal.get_actual_delivery_count() == 1  # 1 delivery created
        assert deal.delivery_count == 1  # Planned count is still 1
        # Check that all deliveries have ESTIMATED status
        for delivery_data in response.data['data']['deliveries']:
            assert delivery_data['status'] == Delivery.Status.ESTIMATED
    
    def test_complete_deal_with_delivery_cost_split(self, seller_client, deal, product, driver_user):
        """Test completing deal with delivery_cost_split from deal"""
        # Set deal with custom delivery_cost_split
        deal.delivery_cost_split = 75  # Supplier pays 75%
        deal.driver = driver_user.driver_profile
        deal.delivery_handler = Deal.DeliveryHandler.SYSTEM_DRIVER
        deal.status = Deal.Status.DONE  # Must be DONE
        deal.delivery_count = 1  # Planned: 1 delivery
        deal.save()
        
        # Add item to deal
        DealItem.objects.create(
            deal=deal,
            product=product,
            quantity=2,
            unit_price=product.price
        )
        
        data = {
            'delivery_address': 'Test Address',
            'supplier_share': 100
        }
        response = seller_client.post(
            f'/api/orders/deals/{deal.id}/complete/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED, f"Response: {response.data}"
        # Check that deal's delivery_cost_split is preserved
        deal.refresh_from_db()
        assert deal.delivery_cost_split == 75
