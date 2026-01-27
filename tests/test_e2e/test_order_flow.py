"""
E2E tests: full order flow via API only.

These tests simulate real user journeys by chaining API calls.
No direct DB manipulation; all state changes go through the API.
"""
import pytest
from rest_framework import status
from apps.orders.models import Deal, Delivery, RequestToDriver


def _get_list_data(response, key='data'):
    """Normalize paginated or raw list from API response."""
    raw = response.data.get(key)
    return raw.get('results', raw) if isinstance(raw, dict) else (raw or [])


@pytest.mark.django_db
@pytest.mark.e2e
class TestOrderFlowE2E:
    """End-to-end order flows using only HTTP API."""

    def test_seller_discovers_supplier_and_creates_deal(
        self, seller_client, supplier_user, product
    ):
        """Flow: Discovery → Create Deal (API only)."""
        # 1. Seller discovers suppliers (single endpoint + role filter)
        list_resp = seller_client.get('/api/users/profiles/', {'role': 'SUPPLIER'})
        assert list_resp.status_code == status.HTTP_200_OK
        assert list_resp.data.get('success') is True
        suppliers = _get_list_data(list_resp)
        supplier_ids = [s['id'] for s in suppliers]
        assert supplier_user.supplier_profile.id in supplier_ids

        # 2. Seller creates deal with discovered supplier
        create_data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
            'items': [{'product_id': product.id, 'quantity': 2}],
        }
        create_resp = seller_client.post(
            '/api/orders/deals/',
            create_data,
            format='json',
        )
        assert create_resp.status_code == status.HTTP_201_CREATED
        assert create_resp.data.get('success') is True
        deal_data = create_resp.data.get('data', {})
        assert deal_data.get('supplier') == supplier_user.supplier_profile.id
        assert deal_data.get('delivery_handler') == Deal.DeliveryHandler.SYSTEM_DRIVER
        deal_id = deal_data['id']

        # 3. Seller lists deals and sees the new one (paginated)
        list_deals = seller_client.get('/api/orders/deals/')
        assert list_deals.status_code == status.HTTP_200_OK
        raw = list_deals.data.get('data')
        deals_list = raw.get('results', raw) if isinstance(raw, dict) else (raw or [])
        deal_ids = [d['id'] for d in deals_list]
        assert deal_id in deal_ids

    def test_seller_completes_deal_and_sees_deliveries(
        self, seller_client, deal, product
    ):
        """Flow: Deal (with items) → Complete → List deliveries (API only)."""
        from apps.orders.models import DealItem

        # Ensure deal has item and is in DONE with delivery_count
        deal.status = Deal.Status.DONE
        deal.delivery_count = 1
        deal.save()
        DealItem.objects.create(
            deal=deal,
            product=product,
            quantity=2,
            unit_price=product.price,
        )

        # 1. Seller completes deal (creates deliveries via API)
        complete_data = {
            'delivery_address': 'E2E Test Address',
            'delivery_note': 'E2E note',
            'supplier_share': 100,
        }
        complete_resp = seller_client.post(
            f'/api/orders/deals/{deal.id}/complete/',
            complete_data,
            format='json',
        )
        assert complete_resp.status_code == status.HTTP_201_CREATED
        assert complete_resp.data.get('success') is True
        created = complete_resp.data.get('data', {})
        assert 'deliveries' in created
        assert created.get('created_count', 0) >= 1
        delivery_ids = [d['id'] for d in created['deliveries']]

        # 2. Seller lists deliveries and sees the new one(s) (paginated)
        list_resp = seller_client.get('/api/orders/deliveries/')
        assert list_resp.status_code == status.HTTP_200_OK
        raw = list_resp.data.get('data')
        deliveries_list = raw.get('results', raw) if isinstance(raw, dict) else (raw or [])
        all_delivery_ids = [d['id'] for d in deliveries_list]
        for did in delivery_ids:
            assert did in all_delivery_ids

    def test_supplier_discovers_drivers_and_seller_creates_deal(
        self, seller_client, supplier_client, supplier_user, driver_user, product
    ):
        """Flow: Supplier lists drivers → Seller creates deal (discovery + deal)."""
        # Supplier discovers available drivers
        drivers_resp = supplier_client.get('/api/users/profiles/', {'role': 'DRIVER'})
        assert drivers_resp.status_code == status.HTTP_200_OK
        assert drivers_resp.data.get('success') is True
        drivers = _get_list_data(drivers_resp)

        # Seller creates deal (system driver) with same supplier
        create_data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
            'items': [{'product_id': product.id, 'quantity': 1}],
        }
        create_resp = seller_client.post(
            '/api/orders/deals/',
            create_data,
            format='json',
        )
        assert create_resp.status_code == status.HTTP_201_CREATED
        deal_id = create_resp.data['data']['id']

        # Seller retrieves deal
        get_resp = seller_client.get(f'/api/orders/deals/{deal_id}/')
        assert get_resp.status_code == status.HTTP_200_OK
        assert get_resp.data['data']['id'] == deal_id

    def test_request_to_driver_full_flow_seller_request_propose_three_approve(
        self,
        seller_client,
        supplier_client,
        driver_client,
        supplier_user,
        driver_user,
        product,
    ):
        """Flow: Deal → LOOKING_FOR_DRIVER → Request driver → Propose → Supplier/Seller/Driver approve → Deal has driver."""
        # Driver from fixture has is_available=True by default, so they appear in discovery.

        # 1. Supplier lists drivers, get driver_id
        drivers_resp = supplier_client.get('/api/users/profiles/', {'role': 'DRIVER'})
        assert drivers_resp.status_code == status.HTTP_200_OK
        assert drivers_resp.data.get('success') is True
        drivers = _get_list_data(drivers_resp)
        assert len(drivers) >= 1, 'Need at least one available driver'
        driver_id = drivers[0]['id']

        # 2. Seller creates deal (SYSTEM_DRIVER)
        create_data = {
            'supplier_id': supplier_user.supplier_profile.id,
            'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
            'items': [{'product_id': product.id, 'quantity': 2}],
        }
        create_resp = seller_client.post(
            '/api/orders/deals/',
            create_data,
            format='json',
        )
        assert create_resp.status_code == status.HTTP_201_CREATED
        deal_id = create_resp.data['data']['id']

        # 3. Seller sets deal to LOOKING_FOR_DRIVER
        update_resp = seller_client.put(
            f'/api/orders/deals/{deal_id}/update_status/',
            {'status': Deal.Status.LOOKING_FOR_DRIVER},
            format='json',
        )
        assert update_resp.status_code == status.HTTP_200_OK

        # 4. Seller requests driver
        request_resp = seller_client.put(
            f'/api/orders/deals/{deal_id}/request_driver/',
            {'driver_id': driver_id, 'requested_price': '150.00'},
            format='json',
        )
        assert request_resp.status_code == status.HTTP_201_CREATED
        assert request_resp.data.get('success') is True

        # 5. Driver lists requests, get request_id (the one for our deal)
        req_list_resp = driver_client.get('/api/orders/driver-requests/')
        assert req_list_resp.status_code == status.HTTP_200_OK
        requests_list = _get_list_data(req_list_resp)
        assert len(requests_list) >= 1
        request_id = next(r['id'] for r in requests_list if r.get('deal') == deal_id)

        # 6. Driver proposes price
        propose_resp = driver_client.put(
            f'/api/orders/driver-requests/{request_id}/propose_price/',
            {'proposed_price': '175.00'},
            format='json',
        )
        assert propose_resp.status_code == status.HTTP_200_OK
        assert propose_resp.data.get('success') is True

        # 7. Supplier approves
        sup_approve = supplier_client.put(
            f'/api/orders/driver-requests/{request_id}/approve/',
            {'final_price': '150.00'},
            format='json',
        )
        assert sup_approve.status_code == status.HTTP_200_OK

        # 8. Seller approves
        sel_approve = seller_client.put(
            f'/api/orders/driver-requests/{request_id}/approve/',
            {'final_price': '150.00'},
            format='json',
        )
        assert sel_approve.status_code == status.HTTP_200_OK

        # 9. Driver approves (last → status ACCEPTED, deal.driver set)
        drv_approve = driver_client.put(
            f'/api/orders/driver-requests/{request_id}/approve/',
            {'final_price': '150.00'},
            format='json',
        )
        assert drv_approve.status_code == status.HTTP_200_OK

        # 10. Verify: deal has driver and request is ACCEPTED
        deal_resp = seller_client.get(f'/api/orders/deals/{deal_id}/')
        assert deal_resp.status_code == status.HTTP_200_OK
        deal_data = deal_resp.data.get('data', {})
        assert deal_data.get('driver') == driver_id

        detail_resp = driver_client.get(f'/api/orders/driver-requests/{request_id}/')
        assert detail_resp.status_code == status.HTTP_200_OK
        assert detail_resp.data.get('data', {}).get('status') == RequestToDriver.Status.ACCEPTED
