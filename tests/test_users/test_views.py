"""
Tests for User views
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()

pytestmark = pytest.mark.integration


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration"""
    
    def test_register_success(self, api_client):
        """Test successful registration"""
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newpass123',
            'password2': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'SELLER',
            'business_name': 'Test Business',
        }
        response = api_client.post('/api/auth/register/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert 'access' in response.data['data']
        assert 'refresh' in response.data['data']
    
    def test_register_password_mismatch(self, api_client):
        """Test registration with password mismatch"""
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newpass123',
            'password2': 'differentpass',
            'role': 'SELLER',
            'business_name': 'Test Business',
        }
        response = api_client.post('/api/auth/register/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogin:
    """Test user login"""
    
    def test_login_success(self, api_client, user):
        """Test successful login"""
        data = {
            'username': 'testuser',
            'password': 'testpass123',
        }
        response = api_client.post('/api/auth/login/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'access' in response.data['data']
    
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials"""
        data = {
            'username': 'wronguser',
            'password': 'wrongpass',
        }
        response = api_client.post('/api/auth/login/', data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserProfile:
    """Test user profile"""
    
    def test_get_profile(self, authenticated_client):
        """Test getting user profile"""
        response = authenticated_client.get('/api/auth/profile/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'email' in response.data['data']
    
    def test_update_profile(self, authenticated_client):
        """Test updating user profile"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
        }
        response = authenticated_client.put('/api/auth/profile/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['first_name'] == 'Updated'


@pytest.mark.django_db
class TestChangePassword:
    """Test change password"""
    
    def test_change_password_success(self, authenticated_client, user):
        """Test successful password change"""
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123',
            'new_password2': 'newpass123',
        }
        response = authenticated_client.put('/api/auth/change-password/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        # Verify password was changed
        user.refresh_from_db()
        assert user.check_password('newpass123')
    
    def test_change_password_wrong_old_password(self, authenticated_client):
        """Test change password with wrong old password"""
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass123',
            'new_password2': 'newpass123',
        }
        response = authenticated_client.put('/api/auth/change-password/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProfileListAPIView:
    """GET /api/users/profiles/?role=SUPPLIER|SELLER|DRIVER"""

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
class TestChoicesAPIView:
    """GET /api/users/choices/ (Role, VehicleType choices)."""

    def test_choices_returns_roles_and_vehicle_types(self, seller_client):
        response = seller_client.get('/api/users/choices/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        data = response.data['data']
        assert 'roles' in data
        assert 'vehicle_types' in data
        roles = data['roles']
        assert any(r['value'] == 'SUPPLIER' and r.get('label') for r in roles)
        vts = data['vehicle_types']
        assert any(v['value'] == 'CAR' and v.get('label') for v in vts)

    def test_choices_unauthorized(self, api_client):
        response = api_client.get('/api/users/choices/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
