import django_filters

from apps.core.filters import BaseModelFilterSet, SearchFilterMixin
from .models import SupplierProfile, SellerProfile, DriverProfile


class SupplierProfileListFilter(SearchFilterMixin, BaseModelFilterSet):
    city = django_filters.CharFilter(lookup_expr="icontains")

    class Meta(BaseModelFilterSet.Meta):
        model = SupplierProfile
        fields = ["city"]
        search_fields = ["company_name", "description"]


class DriverProfileListFilter(BaseModelFilterSet):
    city = django_filters.CharFilter(lookup_expr="icontains")
    vehicle_type = django_filters.ChoiceFilter(choices=DriverProfile.VehicleType.choices)

    class Meta(BaseModelFilterSet.Meta):
        model = DriverProfile
        fields = ["city", "vehicle_type"]


class SellerProfileListFilter(SearchFilterMixin, BaseModelFilterSet):
    city = django_filters.CharFilter(lookup_expr="icontains")

    class Meta(BaseModelFilterSet.Meta):
        model = SellerProfile
        fields = ["city"]
        search_fields = ["business_name", "description"]
