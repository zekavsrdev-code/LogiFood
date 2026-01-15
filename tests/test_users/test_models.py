"""
Tests for User model
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test User model"""
    
    def test_create_user(self):
        """Test creating a user"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        assert user.email == 'test@example.com'
        assert user.username == 'testuser'
        assert user.check_password('testpass123')
        assert not user.is_staff
        assert not user.is_superuser
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass123'
        )
        assert user.is_staff
        assert user.is_superuser
    
    def test_user_str(self):
        """Test user string representation"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        assert str(user) == 'test@example.com'
    
    def test_user_email_unique(self):
        """Test that email must be unique"""
        User.objects.create_user(
            email='test@example.com',
            username='testuser1',
            password='testpass123'
        )
        with pytest.raises(Exception):  # IntegrityError
            User.objects.create_user(
                email='test@example.com',
                username='testuser2',
                password='testpass123'
            )
