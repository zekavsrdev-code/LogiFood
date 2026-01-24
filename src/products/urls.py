from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    ProductListView,
    ProductDetailView,
    SupplierProductViewSet,
)

app_name = 'products'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'my-products', SupplierProductViewSet, basename='supplier-product')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Product URLs
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
]
