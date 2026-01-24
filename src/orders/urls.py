from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderViewSet,
    SupplierListView,
    DriverListView,
    AvailableOrderListView,
    AcceptOrderView,
)

app_name = 'orders'

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Discovery URLs
    path('suppliers/', SupplierListView.as_view(), name='supplier-list'),
    path('drivers/', DriverListView.as_view(), name='driver-list'),
    path('available-orders/', AvailableOrderListView.as_view(), name='available-orders'),
    path('accept-order/<int:pk>/', AcceptOrderView.as_view(), name='accept-order'),
]
