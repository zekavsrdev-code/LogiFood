"""
Base service layer for business logic
"""
from typing import Optional, List, Dict, Any
from django.db import models


class BaseService:
    """Base service class for common operations"""
    
    model: models.Model = None
    
    @classmethod
    def get_by_id(cls, pk: int) -> Optional[models.Model]:
        """Get object by primary key"""
        try:
            return cls.model.objects.get(pk=pk)
        except cls.model.DoesNotExist:
            return None
    
    @classmethod
    def get_all(cls, filters: Optional[Dict[str, Any]] = None) -> List[models.Model]:
        """Get all objects with optional filters"""
        queryset = cls.model.objects.all()
        if filters:
            queryset = queryset.filter(**filters)
        return list(queryset)
    
    @classmethod
    def create(cls, **kwargs) -> models.Model:
        """Create a new object"""
        return cls.model.objects.create(**kwargs)
    
    @classmethod
    def update(cls, instance: models.Model, **kwargs) -> models.Model:
        """Update an existing object"""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance
    
    @classmethod
    def delete(cls, instance: models.Model) -> bool:
        """Delete an object"""
        instance.delete()
        return True
