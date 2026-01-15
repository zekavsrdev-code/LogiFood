"""
User service layer for business logic
"""
from typing import Optional
from django.contrib.auth import get_user_model
from apps.core.services import BaseService

User = get_user_model()


class UserService(BaseService):
    """User service for user-related operations"""
    model = User
    
    @classmethod
    def get_by_email(cls, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            return cls.model.objects.get(email=email)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def verify_user(cls, user: User) -> User:
        """Verify user account"""
        user.is_verified = True
        user.save()
        return user
