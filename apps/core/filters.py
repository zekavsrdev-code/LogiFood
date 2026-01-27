"""
Shared filter infrastructure. All app FilterSets can inherit from BaseModelFilterSet;
use SearchFilterMixin when filtering across multiple text fields via a single "search" param.
"""
from django.db.models import Q
from rest_framework import filters
import django_filters


class CustomSearchFilter(filters.SearchFilter):
    search_param = "search"
    search_title = "Search"
    search_description = "Search query parameter"


class BaseModelFilterSet(django_filters.FilterSet):
    """
    Base for app-level FilterSets. Set Meta.model and Meta.fields (or Meta.exclude).
    Subclass and add extra filters or use SearchFilterMixin for cross-field search.
    """
    class Meta:
        abstract = True


class SearchFilterMixin:
    """
    Mixin for FilterSets that support a single "search" param over multiple fields.
    Require Meta.search_fields = ['field1', 'field2', ...] (icontains).
    """
    search = django_filters.CharFilter(method="filter_search")

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        search_fields = getattr(getattr(self, "Meta", None), "search_fields", None) or []
        if not search_fields:
            return queryset
        pred = Q()
        for field in search_fields:
            pred |= Q(**{f"{field}__icontains": value})
        return queryset.filter(pred)
