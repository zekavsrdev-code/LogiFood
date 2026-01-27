"""
Tests for users profile list and choices: /api/users/profiles/?role= ve /api/users/choices/.
"""
import pytest
from rest_framework import status

pytestmark = pytest.mark.integration


@pytest.mark.django_db
class TestProfileDiscoveryView:
    """Test GET /api/users/profiles/?role=SUPPLIER|SELLER|DRIVER"""

    def test_list_suppliers(self, seller_client, supplier_user):
        response = seller_client.get('/api/users/profiles/', {'role': 'SUPPLIER'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    def test_list_suppliers_unauthorized(self, api_client):
        response = api_client.get('/api/users/profiles/', {'role': 'SUPPLIER'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_drivers(self, supplier_client, driver_user):
        response = supplier_client.get('/api/users/profiles/', {'role': 'DRIVER'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    def test_list_drivers_not_supplier(self, seller_client):
        response = seller_client.get('/api/users/profiles/', {'role': 'DRIVER'})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_sellers(self, supplier_client, seller_user):
        response = supplier_client.get('/api/users/profiles/', {'role': 'SELLER'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    def test_list_sellers_unauthorized(self, api_client):
        response = api_client.get('/api/users/profiles/', {'role': 'SELLER'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_role_required(self, seller_client):
        response = seller_client.get('/api/users/profiles/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_role_invalid(self, seller_client):
        response = seller_client.get('/api/users/profiles/', {'role': 'INVALID'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserChoicesView:
    """Test GET /api/users/choices/ — Role, VehicleType vb."""

    def test_choices_returns_roles_and_vehicle_types(self, seller_client):
        response = seller_client.get('/api/users/choices/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        data = response.data['data']
        assert 'roles' in data
        assert 'vehicle_types' in data
        roles = data['roles']
        assert any(r['value'] == 'SUPPLIER' and 'Tedarikçi' in r.get('label', '') for r in roles)
        vts = data['vehicle_types']
        assert any(v['value'] == 'CAR' and 'Otomobil' in v.get('label', '') for v in vts)

    def test_choices_unauthorized(self, api_client):
        response = api_client.get('/api/users/choices/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
