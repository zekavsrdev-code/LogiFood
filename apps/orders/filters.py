from apps.core.filters import BaseModelFilterSet
from .models import Deal, Delivery, RequestToDriver


class DealFilter(BaseModelFilterSet):
    class Meta(BaseModelFilterSet.Meta):
        model = Deal
        fields = ["status"]


class DeliveryFilter(BaseModelFilterSet):
    class Meta(BaseModelFilterSet.Meta):
        model = Delivery
        fields = ["status"]


class RequestToDriverFilter(BaseModelFilterSet):
    class Meta(BaseModelFilterSet.Meta):
        model = RequestToDriver
        fields = ["status", "deal", "driver"]
