import django_filters

from apps.core.filters import BaseModelFilterSet, SearchFilterMixin
from .models import User, SupplierProfile, SellerProfile, DriverProfile


class ProfileListSchemaFilter(django_filters.FilterSet):
    """Schema-only: all profile list params for OpenAPI. Used when role is missing."""
    role = django_filters.ChoiceFilter(
        choices=User.Role.choices,
        required=True,
        help_text="List type: SUPPLIER, SELLER or DRIVER. Required.",
    )
    city = django_filters.CharFilter(
        lookup_expr="icontains",
        help_text="Filter by city. For SUPPLIER and SELLER.",
    )
    search = django_filters.CharFilter(
        help_text="Search in company_name/description (SUPPLIER) or business_name/description (SELLER).",
    )
    vehicle_type = django_filters.ChoiceFilter(
        choices=DriverProfile.VehicleType.choices,
        help_text="Driver vehicle type. Only when role=DRIVER.",
    )

    class Meta:
        model = SupplierProfile
        fields = []


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
