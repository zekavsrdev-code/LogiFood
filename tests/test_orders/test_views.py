"""Tests for Order views"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import status
from apps.orders.models import Deal, DealItem, Delivery, DeliveryItem, RequestToDriver

User = get_user_model()

pytestmark = pytest.mark.integration


@pytest.mark.django_db
class TestDealViews:
    """Test Deal views"""
    
    def test_list_deals_as_seller(self, seller_client, deal):
        response = seller_client.get('/api/orders/deals/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_deals_as_supplier(self, supplier_client, deal):
        response = supplier_client.get('/api/orders/deals/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_deals_unauthorized(self, api_client):
        response = api_client.get('/api/orders/deals/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_deal_as_seller(self, seller_client, supplier_user, product):
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
        assert deal_data['delivery_cost_split'] == 50
    
    def test_create_deal_delivery_cost_split_with_3rd_party(self, seller_client, supplier_user, product):
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SELLER,
            'delivery_cost_split': 80,
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        response = seller_client.post('/api/orders/deals/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        deal_data = response.data['data']
        assert deal_data['delivery_cost_split'] == 50
    
    def test_retrieve_deal(self, seller_client, deal):
        response = seller_client.get(f'/api/orders/deals/{deal.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'delivery_cost_split' in response.data['data']
        assert 'seller_approved' in response.data['data']
        assert 'supplier_approved' in response.data['data']

    def test_approve_deal_as_seller(self, seller_client, deal):
        response = seller_client.post(f'/api/orders/deals/{deal.id}/approve/', {}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        deal.refresh_from_db()
        assert deal.seller_approved is True
        assert deal.supplier_approved is False

    def test_approve_deal_as_supplier(self, supplier_client, deal):
        response = supplier_client.post(f'/api/orders/deals/{deal.id}/approve/', {}, format='json')
        assert response.status_code == status.HTTP_200_OK
        deal.refresh_from_db()
        assert deal.supplier_approved is True

    def test_partial_update_deal(self, seller_client, deal):
        data = {'delivery_cost_split': 70}
        response = seller_client.patch(f'/api/orders/deals/{deal.id}/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        deal.refresh_from_db()
        assert deal.delivery_cost_split == 70
    
    def test_update_deal_status(self, seller_client, deal):
        deal.seller_approved = True
        deal.supplier_approved = True
        deal.save()
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

    def test_update_deal_status_requires_both_approvals(self, seller_client, deal):
        data = {'status': Deal.Status.DONE}
        response = seller_client.put(
            f'/api/orders/deals/{deal.id}/update_status/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Both seller and supplier' in response.data.get('message', '')
    
    def test_assign_driver_to_deal(self, seller_client, deal, driver_user):
        deal.status = Deal.Status.LOOKING_FOR_DRIVER
        deal.seller_approved = True
        deal.supplier_approved = True
        deal.save()
        
        data = {'driver_id': driver_user.driver_profile.id}
        response = seller_client.put(
            f'/api/orders/deals/{deal.id}/assign_driver/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        deal.refresh_from_db()
        # Driver is now in RequestToDriver, not Deal
        accepted_request = deal.driver_requests.filter(status=RequestToDriver.Status.ACCEPTED).first()
        assert accepted_request is not None
        assert accepted_request.driver == driver_user.driver_profile
        assert deal.status == Deal.Status.DEALING
    
    def test_request_driver_for_deal(self, seller_client, deal, driver_user):
        deal.status = Deal.Status.LOOKING_FOR_DRIVER
        deal.delivery_handler = Deal.DeliveryHandler.SYSTEM_DRIVER
        deal.seller_approved = True
        deal.supplier_approved = True
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
    
    def test_request_driver_for_3rd_party_deal(self, seller_client, deal, driver_user):
        deal.status = Deal.Status.LOOKING_FOR_DRIVER
        deal.delivery_handler = Deal.DeliveryHandler.SUPPLIER
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
        assert 'deliveries' in response.data['data']
        assert 'created_count' in response.data['data']
        assert 'total_planned' in response.data['data']
        
        deal.refresh_from_db()
        assert len(response.data['data']['deliveries']) == 1
        assert deal.get_actual_delivery_count() == 1
        assert deal.delivery_count == 1
        for delivery_data in response.data['data']['deliveries']:
            assert delivery_data['status'] == Delivery.Status.ESTIMATED
    
    def test_complete_deal_with_delivery_cost_split(self, seller_client, deal, product, driver_user):
        from apps.orders.models import RequestToDriver
        # Create an accepted RequestToDriver for this test
        RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            final_price=Decimal('150.00'),
            status=RequestToDriver.Status.ACCEPTED,
            supplier_approved=True,
            seller_approved=True,
            driver_approved=True,
            created_by=deal.seller.user
        )
        
        deal.delivery_cost_split = 75
        deal.delivery_handler = Deal.DeliveryHandler.SYSTEM_DRIVER
        deal.seller_approved = True
        deal.supplier_approved = True
        deal.status = Deal.Status.DONE
        deal.delivery_count = 1
        deal.save()
        
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
        assert response.status_code == status.HTTP_201_CREATED
        deal.refresh_from_db()
        assert deal.delivery_cost_split == 75


@pytest.mark.django_db
class TestDealItemViews:
    """Test DealItem views – seller and supplier can create/update/delete; clears other party approval."""

    def test_list_deal_items_as_seller(self, seller_client, deal, product):
        DealItem.objects.create(deal=deal, product=product, quantity=5, unit_price=product.price)
        response = seller_client.get('/api/orders/deal-items/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or 'data' in response.data

    def test_list_deal_items_as_supplier(self, supplier_client, deal, product):
        DealItem.objects.create(deal=deal, product=product, quantity=5, unit_price=product.price)
        response = supplier_client.get('/api/orders/deal-items/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_deal_item_as_seller(self, seller_client, deal, product):
        data = {'deal': deal.id, 'product': product.id, 'quantity': 10}
        response = seller_client.post('/api/orders/deal-items/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        deal.refresh_from_db()
        assert deal.supplier_approved is False

    def test_create_deal_item_as_supplier(self, supplier_client, deal, product):
        data = {'deal': deal.id, 'product': product.id, 'quantity': 8}
        response = supplier_client.post('/api/orders/deal-items/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        deal.refresh_from_db()
        assert deal.seller_approved is False

    def test_update_deal_item_clears_other_approval(self, seller_client, deal, product):
        item = DealItem.objects.create(deal=deal, product=product, quantity=5, unit_price=product.price)
        deal.supplier_approved = True
        deal.save()
        response = seller_client.patch(
            f'/api/orders/deal-items/{item.id}/',
            {'quantity': 15},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        deal.refresh_from_db()
        assert deal.supplier_approved is False

    def test_delete_deal_item_clears_other_approval(self, supplier_client, deal, product):
        item = DealItem.objects.create(deal=deal, product=product, quantity=5, unit_price=product.price)
        deal.seller_approved = True
        deal.save()
        response = supplier_client.delete(f'/api/orders/deal-items/{item.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        deal.refresh_from_db()
        assert deal.seller_approved is False


@pytest.mark.django_db
class TestDeliveryViews:
    """Test Delivery views"""
    
    def test_list_deliveries_as_seller(self, seller_client, delivery):
        response = seller_client.get('/api/orders/deliveries/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_deliveries_as_supplier(self, supplier_client, delivery):
        response = supplier_client.get('/api/orders/deliveries/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_deliveries_unauthorized(self, api_client):
        response = api_client.get('/api/orders/deliveries/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_delivery_not_allowed(self, seller_client, supplier_user, product):
        data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_address': 'Test Address',
            'delivery_note': 'Test note',
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }
        response = seller_client.post('/api/orders/deliveries/', data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Deliveries must be created from deals' in str(response.data.get('detail', ''))
    
    def test_retrieve_delivery(self, seller_client, delivery):
        response = seller_client.get(f'/api/orders/deliveries/{delivery.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_update_delivery_status_as_supplier(self, supplier_client, delivery):
        data = {'status': Delivery.Status.CONFIRMED}
        response = supplier_client.put(
            f'/api/orders/deliveries/{delivery.id}/update_status/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        delivery.refresh_from_db()
        assert delivery.status == Delivery.Status.CONFIRMED
    
    def test_update_delivery_status_as_driver(self, driver_client, delivery, driver_user):
        delivery.driver_profile = driver_user.driver_profile
        delivery.driver_name = None
        delivery.driver_phone = None
        delivery.driver_vehicle_type = None
        delivery.driver_vehicle_plate = None
        delivery.driver_license_number = None
        delivery.status = Delivery.Status.PICKED_UP
        delivery.save()
        
        data = {'status': Delivery.Status.IN_TRANSIT}
        response = driver_client.put(
            f'/api/orders/deliveries/{delivery.id}/update_status/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_update_delivery_status_unauthorized(self, seller_client, delivery):
        data = {'status': Delivery.Status.CONFIRMED}
        response = seller_client.put(
            f'/api/orders/deliveries/{delivery.id}/update_status/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_assign_driver(self, supplier_client, delivery, driver_user):
        data = {'driver_id': driver_user.driver_profile.id}
        response = supplier_client.put(
            f'/api/orders/deliveries/{delivery.id}/assign_driver/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        delivery.refresh_from_db()
        assert delivery.driver_profile == driver_user.driver_profile
        assert delivery.status == Delivery.Status.READY
    
    def test_assign_driver_not_supplier(self, seller_client, delivery, driver_user):
        data = {'driver_id': driver_user.driver_profile.id}
        response = seller_client.put(
            f'/api/orders/deliveries/{delivery.id}/assign_driver/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_assign_driver_invalid_driver(self, supplier_client, delivery):
        data = {'driver_id': 99999}
        response = supplier_client.put(
            f'/api/orders/deliveries/{delivery.id}/assign_driver/',
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestRequestToDriverViews:
    """Test RequestToDriver views"""
    
    def test_list_requests_as_driver(self, driver_client, deal, driver_user):
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
        from apps.orders.models import RequestToDriver
        
        deal.supplier = supplier_user.supplier_profile
        deal.seller = seller_user.seller_profile
        deal.delivery_handler = Deal.DeliveryHandler.SYSTEM_DRIVER
        deal.save()
        
        deal.refresh_from_db()
        
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            created_by=deal.seller.user
        )
        
        request.refresh_from_db()
        
        response = supplier_client.put(
            f'/api/orders/driver-requests/{request.id}/approve/',
            {'final_price': '150.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        request.refresh_from_db()
        assert request.supplier_approved is True
        assert request.status != RequestToDriver.Status.ACCEPTED
        
        response = seller_client.put(
            f'/api/orders/driver-requests/{request.id}/approve/',
            {'final_price': '150.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        request.refresh_from_db()
        assert request.seller_approved is True
        assert request.status != RequestToDriver.Status.ACCEPTED
        
        response = driver_client.put(
            f'/api/orders/driver-requests/{request.id}/approve/',
            {'final_price': '150.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        request.refresh_from_db()
        assert request.driver_approved is True
        assert request.status == RequestToDriver.Status.ACCEPTED
        assert request.final_price == Decimal('150.00')
        
        deal.refresh_from_db()
        # Driver is now in RequestToDriver, not Deal
        from apps.orders.models import RequestToDriver
        accepted_request = deal.driver_requests.filter(status=RequestToDriver.Status.ACCEPTED).first()
        assert accepted_request is not None
        assert accepted_request.driver == driver_user.driver_profile
        assert deal.status == Deal.Status.DEALING
    
    def test_reject_request(self, supplier_client, deal, driver_user, supplier_user):
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
        request = RequestToDriver.objects.create(
            deal=deal,
            driver=driver_user.driver_profile,
            requested_price=Decimal('150.00'),
            status=RequestToDriver.Status.ACCEPTED,
            created_by=deal.seller.user
        )
        
        response = driver_client.put(
            f'/api/orders/driver-requests/{request.id}/propose_price/',
            {'proposed_price': '175.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestDeliveryDiscoveryViews:
    """Test delivery discovery (available-deliveries, accept-delivery). Supplier/driver/seller discovery is under users."""
    
    def test_list_available_deliveries(self, driver_client, delivery):
        delivery.status = Delivery.Status.READY
        delivery.driver_profile = None
        delivery.driver_name = None
        delivery.save()
        
        response = driver_client.get('/api/orders/available-deliveries/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_list_available_deliveries_not_driver(self, seller_client):
        response = seller_client.get('/api/orders/available-deliveries/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_accept_delivery(self, driver_client, delivery, driver_user):
        delivery.status = Delivery.Status.READY
        delivery.driver_profile = None
        delivery.driver_name = None
        delivery.save()
        
        response = driver_client.put(f'/api/orders/accept-delivery/{delivery.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        delivery.refresh_from_db()
        assert delivery.driver_profile is not None
        assert delivery.driver_name is None
        assert delivery.status == Delivery.Status.PICKED_UP
    
    def test_accept_delivery_not_driver(self, seller_client, delivery):
        response = seller_client.put(f'/api/orders/accept-delivery/{delivery.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_accept_delivery_already_assigned(self, driver_client, delivery, driver_user):
        delivery.driver_profile = driver_user.driver_profile
        delivery.driver_name = None
        delivery.driver_phone = None
        delivery.driver_vehicle_type = None
        delivery.driver_vehicle_plate = None
        delivery.driver_license_number = None
        delivery.status = Delivery.Status.PICKED_UP
        delivery.save()
        
        other_driver = User.objects.create_user(
            username='other_driver',
            password='pass123',
            role=User.Role.DRIVER
        )
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=other_driver)
        
        response = client.put(f'/api/orders/accept-delivery/{delivery.id}/')
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]
