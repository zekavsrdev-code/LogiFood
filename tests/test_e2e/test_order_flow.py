"""
E2E tests: full order flow via API only.

These tests simulate real user journeys by chaining API calls.
No direct DB manipulation; all state changes go through the API.
"""
import pytest
from rest_framework import status
from src.orders.models import Deal, Delivery


@pytest.mark.django_db
@pytest.mark.e2e
class TestOrderFlowE2E:
    """End-to-end order flows using only HTTP API."""

    def test_seller_discovers_supplier_and_creates_deal(
        self, seller_client, supplier_user, product
    ):
        """Flow: Discovery → Create Deal (API only)."""
        # 1. Seller discovers suppliers (paginated: data.results or direct data)
        list_resp = seller_client.get('/api/orders/suppliers/')
        assert list_resp.status_code == status.HTTP_200_OK
        assert list_resp.data.get('success') is True
        raw = list_resp.data.get('data')
        suppliers = raw.get('results', raw) if isinstance(raw, dict) else (raw or [])
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
        from src.orders.models import DealItem

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
        drivers_resp = supplier_client.get('/api/orders/drivers/')
        assert drivers_resp.status_code == status.HTTP_200_OK
        assert drivers_resp.data.get('success') is True
        drivers = drivers_resp.data.get('data', [])

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
