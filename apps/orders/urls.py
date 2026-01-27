from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DealViewSet,
    RequestToDriverViewSet,
    DeliveryViewSet,
    AvailableDeliveryListView,
    AcceptDeliveryView,
)

app_name = 'orders'

router = DefaultRouter()
router.register(r'deals', DealViewSet, basename='deal')
router.register(r'driver-requests', RequestToDriverViewSet, basename='driver-request')
router.register(r'deliveries', DeliveryViewSet, basename='delivery')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # Delivery discovery (suppliers/drivers/sellers moved to api/users/)
    path('available-deliveries/', AvailableDeliveryListView.as_view(), name='available-deliveries'),
    path('accept-delivery/<int:pk>/', AcceptDeliveryView.as_view(), name='accept-delivery'),
]
