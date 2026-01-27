"""
Tests for User services
"""
import pytest
from django.contrib.auth import get_user_model

from apps.users.services import UserService

User = get_user_model()
pytestmark = pytest.mark.unit


@pytest.mark.django_db
class TestUserService:
    """Test UserService"""
    
    def test_get_by_id(self, user):
        """Test getting user by ID"""
        found_user = UserService.get_by_id(user.id)
        assert found_user is not None
        assert found_user.id == user.id
    
    def test_get_by_id_not_found(self):
        """Test getting non-existent user"""
        found_user = UserService.get_by_id(99999)
        assert found_user is None
    
    def test_get_by_email(self, user):
        """Test getting user by email"""
        found_user = UserService.get_by_email(user.email)
        assert found_user is not None
        assert found_user.email == user.email
    
    def test_get_by_email_not_found(self):
        """Test getting user with non-existent email"""
        found_user = UserService.get_by_email('nonexistent@example.com')
        assert found_user is None
    
    def test_verify_user(self, user):
        """Test verifying user"""
        assert user.is_verified is False
        verified_user = UserService.verify_user(user)
        assert verified_user.is_verified is True
