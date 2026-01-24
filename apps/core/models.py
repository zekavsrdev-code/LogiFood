from django.db import models
from django.conf import settings


class TimeStampedModel(models.Model):
    """Abstract base model with created and updated timestamps, and created_by field"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='Created By',
        help_text='User who created this record'
    )

    class Meta:
        abstract = True
