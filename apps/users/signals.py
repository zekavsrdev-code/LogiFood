"""User app signals."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, SupplierProfile, SellerProfile, DriverProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create profile based on user role when user is created."""
    if created:
        if instance.role == User.Role.SUPPLIER:
            SupplierProfile.objects.get_or_create(
                user=instance,
                defaults={"company_name": instance.username},
            )
        elif instance.role == User.Role.SELLER:
            SellerProfile.objects.get_or_create(
                user=instance,
                defaults={"business_name": instance.username},
            )
        elif instance.role == User.Role.DRIVER:
            DriverProfile.objects.get_or_create(
                user=instance,
                defaults={"license_number": ""},
            )
