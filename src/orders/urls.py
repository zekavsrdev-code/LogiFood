from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DealViewSet,
    DeliveryViewSet,
    SupplierListView,
    DriverListView,
    AvailableDeliveryListView,
    AcceptDeliveryView,
)

app_name = 'orders'

router = DefaultRouter()
router.register(r'deals', DealViewSet, basename='deal')
router.register(r'deliveries', DeliveryViewSet, basename='delivery')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # Discovery URLs
    path('suppliers/', SupplierListView.as_view(), name='supplier-list'),
    path('drivers/', DriverListView.as_view(), name='driver-list'),
    path('available-deliveries/', AvailableDeliveryListView.as_view(), name='available-deliveries'),
    path('accept-delivery/<int:pk>/', AcceptDeliveryView.as_view(), name='accept-delivery'),
]
