"""
Tests for User serializers
"""
import pytest
from django.contrib.auth import get_user_model
from src.users.serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestUserSerializer:
    """Test UserSerializer"""
    
    def test_user_serializer(self, user):
        """Test user serialization"""
        serializer = UserSerializer(user)
        data = serializer.data
        assert 'email' in data
        assert 'username' in data
        assert 'id' in data
        assert 'password' not in data  # Password should not be in output


@pytest.mark.django_db
class TestUserRegistrationSerializer:
    """Test UserRegistrationSerializer"""
    
    def test_valid_registration_data(self):
        """Test valid registration data"""
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'New',
            'last_name': 'User',
        }
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()
    
    def test_password_mismatch(self):
        """Test password mismatch"""
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'TestPass123!',
            'password2': 'DifferentPass123!',
        }
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors


@pytest.mark.django_db
class TestChangePasswordSerializer:
    """Test ChangePasswordSerializer"""
    
    def test_valid_password_change(self):
        """Test valid password change data"""
        data = {
            'old_password': 'oldpass123',
            'new_password': 'NewPass123!',
            'new_password2': 'NewPass123!',
        }
        serializer = ChangePasswordSerializer(data=data)
        assert serializer.is_valid()
    
    def test_password_mismatch(self):
        """Test password mismatch in change password"""
        data = {
            'old_password': 'oldpass123',
            'new_password': 'NewPass123!',
            'new_password2': 'DifferentPass123!',
        }
        serializer = ChangePasswordSerializer(data=data)
        assert not serializer.is_valid()
        assert 'new_password' in serializer.errors
