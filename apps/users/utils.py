"""
User utility functions
"""
import secrets
import string


def generate_verification_code(length: int = 6) -> str:
    """Generate a random verification code"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def get_user_choices():
    """Return {value, label} for all user-related TextChoices (Role, VehicleType, etc.)."""
    from .models import User, DriverProfile
    return {
        "roles": [{"value": v, "label": l} for v, l in User.Role.choices],
        "vehicle_types": [{"value": v, "label": l} for v, l in DriverProfile.VehicleType.choices],
    }
