from rest_framework import status, viewsets, generics, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from .models import Order
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderStatusUpdateSerializer,
    OrderAssignDriverSerializer,
)
from src.users.models import SupplierProfile, DriverProfile
from apps.core.utils import success_response, error_response
from apps.core.permissions import IsSupplier, IsSeller, IsDriver
from apps.core.pagination import StandardResultsSetPagination


# ==================== ORDER VIEWS ====================

class OrderViewSet(viewsets.ModelViewSet):
    """Order ViewSet - Filtering by role"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_supplier:
            return Order.objects.filter(supplier=user.supplier_profile).select_related('seller', 'supplier', 'driver')
        elif user.is_seller:
            return Order.objects.filter(seller=user.seller_profile).select_related('seller', 'supplier', 'driver')
        elif user.is_driver:
            return Order.objects.filter(driver=user.driver_profile).select_related('seller', 'supplier', 'driver')
        else:
            return Order.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def perform_create(self, serializer):
        # Only Seller can create orders
        if not self.request.user.is_seller:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only sellers can create orders')
        serializer.save(seller=self.request.user.seller_profile)
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Orders listed successfully')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        response_serializer = OrderSerializer(order)
        return success_response(
            data=response_serializer.data,
            message='Order created successfully',
            status_code=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return success_response(data=response.data, message='Order detail')
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        """Update order status - Supplier or Driver"""
        order = self.get_object()
        user = request.user
        
        # Permission check
        if not (user.is_supplier or user.is_driver):
            return error_response(
                message='Unauthorized access',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Supplier check
        if user.is_supplier and order.supplier != user.supplier_profile:
            return error_response(
                message='This order does not belong to you',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Driver check
        if user.is_driver and order.driver != user.driver_profile:
            return error_response(
                message='This order does not belong to you',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = OrderStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            order.status = serializer.validated_data['status']
            order.save()
            return success_response(
                data=OrderSerializer(order).data,
                message='Order status updated successfully'
            )
        return error_response(message='Update failed', errors=serializer.errors)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated, IsSupplier])
    def assign_driver(self, request, pk=None):
        """Assign driver to order - Only supplier can do this"""
        order = self.get_object()
        
        # Supplier check
        if order.supplier != request.user.supplier_profile:
            return error_response(
                message='This order does not belong to you',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = OrderAssignDriverSerializer(data=request.data)
        if serializer.is_valid():
            driver = DriverProfile.objects.get(id=serializer.validated_data['driver_id'])
            order.driver = driver
            order.status = Order.Status.READY
            order.save()
            return success_response(
                data=OrderSerializer(order).data,
                message='Driver assigned successfully'
            )
        return error_response(message='Driver assignment failed', errors=serializer.errors)


# ==================== DISCOVERY VIEWS ====================

class SupplierListView(generics.ListAPIView):
    """List all active suppliers - Sellers can view"""
    queryset = SupplierProfile.objects.filter(is_active=True).select_related('user')
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['city']
    search_fields = ['company_name', 'description']
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            data = [{
                'id': s.id,
                'company_name': s.company_name,
                'city': s.city,
                'description': s.description,
                'product_count': s.products.filter(is_active=True).count()
            } for s in page]
            paginated_response = self.get_paginated_response(data)
            return success_response(
                data=paginated_response.data,
                message='Suppliers listed successfully'
            )
        
        data = [{
            'id': s.id,
            'company_name': s.company_name,
            'city': s.city,
            'description': s.description,
            'product_count': s.products.filter(is_active=True).count()
        } for s in queryset]
        
        return success_response(data=data, message='Suppliers listed successfully')


class DriverListView(generics.ListAPIView):
    """List available drivers - Suppliers can view"""
    queryset = DriverProfile.objects.filter(is_active=True, is_available=True).select_related('user')
    permission_classes = [IsAuthenticated, IsSupplier]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['city', 'vehicle_type']
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            data = [{
                'id': d.id,
                'name': d.user.get_full_name() or d.user.username,
                'phone': d.user.phone_number,
                'city': d.city,
                'vehicle_type': d.vehicle_type,
                'vehicle_type_display': d.get_vehicle_type_display(),
                'vehicle_plate': d.vehicle_plate,
            } for d in page]
            paginated_response = self.get_paginated_response(data)
            return success_response(
                data=paginated_response.data,
                message='Drivers listed successfully'
            )
        
        data = [{
            'id': d.id,
            'name': d.user.get_full_name() or d.user.username,
            'phone': d.user.phone_number,
            'city': d.city,
            'vehicle_type': d.vehicle_type,
            'vehicle_type_display': d.get_vehicle_type_display(),
            'vehicle_plate': d.vehicle_plate,
        } for d in queryset]
        
        return success_response(data=data, message='Drivers listed successfully')


class AvailableOrderListView(generics.ListAPIView):
    """Available orders for drivers"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsDriver]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Orders without driver and ready status
        orders = Order.objects.filter(
            driver__isnull=True,
            status=Order.Status.READY
        ).select_related('seller', 'supplier')
        
        # City filter (based on driver's city)
        driver_city = self.request.user.driver_profile.city
        if driver_city:
            orders = orders.filter(
                Q(seller__city__icontains=driver_city) | Q(supplier__city__icontains=driver_city)
            )
        
        return orders
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Available orders listed successfully')


class AcceptOrderView(generics.UpdateAPIView):
    """Driver accepts order"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsDriver]
    
    def get_queryset(self):
        return Order.objects.filter(
            driver__isnull=True,
            status=Order.Status.READY
        )
    
    def update(self, request, *args, **kwargs):
        order = self.get_object()
        order.driver = request.user.driver_profile
        order.status = Order.Status.PICKED_UP
        order.save()
        
        serializer = self.get_serializer(order)
        return success_response(
            data=serializer.data,
            message='Order accepted successfully'
        )
