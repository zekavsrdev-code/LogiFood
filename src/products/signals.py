"""
Product app signals for cache invalidation
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Category, Product
from apps.core.cache import invalidate_model_cache


@receiver(post_save, sender=Category)
def category_cache_invalidate(sender, instance, **kwargs):
    """Invalidate category cache when category is saved"""
    invalidate_model_cache(Category, instance_id=instance.id)
    # Also invalidate parent category cache if exists
    if instance.parent:
        invalidate_model_cache(Category, instance_id=instance.parent.id)


@receiver(post_delete, sender=Category)
def category_cache_invalidate_delete(sender, instance, **kwargs):
    """Invalidate category cache when category is deleted"""
    invalidate_model_cache(Category)
    # Also invalidate parent category cache if exists
    if instance.parent:
        invalidate_model_cache(Category, instance_id=instance.parent.id)


@receiver(post_save, sender=Product)
def product_cache_invalidate(sender, instance, **kwargs):
    """Invalidate product cache when product is saved"""
    invalidate_model_cache(Product, instance_id=instance.id)
    # Also invalidate category cache if product category changed
    if instance.category:
        invalidate_model_cache(Category, instance_id=instance.category.id)


@receiver(post_delete, sender=Product)
def product_cache_invalidate_delete(sender, instance, **kwargs):
    """Invalidate product cache when product is deleted"""
    invalidate_model_cache(Product, instance_id=instance.id)
    # Also invalidate category cache if product had category
    if instance.category:
        invalidate_model_cache(Category, instance_id=instance.category.id)
