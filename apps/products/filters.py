import django_filters

from apps.core.filters import BaseModelFilterSet, SearchFilterMixin
from .models import Product


class ProductListFilter(SearchFilterMixin, BaseModelFilterSet):
    category__slug = django_filters.CharFilter(field_name="category__slug")
    supplier = django_filters.NumberFilter(field_name="supplier_id")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta(BaseModelFilterSet.Meta):
        model = Product
        fields = ["category__slug", "supplier"]
        search_fields = ["name", "description"]


class SupplierProductFilter(BaseModelFilterSet):
    class Meta(BaseModelFilterSet.Meta):
        model = Product
        fields = ["category", "is_active"]
