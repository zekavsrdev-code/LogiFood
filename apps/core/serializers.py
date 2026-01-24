"""
Common serializers used across the application
"""
from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    """Base serializer with common fields"""
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        abstract = True


class EmptySerializer(serializers.Serializer):
    """
    Empty serializer for endpoints that don't require a request body.
    Used for schema introspection in API documentation.
    Example: toggle-availability PUT endpoint
    """
    pass
