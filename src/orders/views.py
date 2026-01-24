from rest_framework import status, viewsets, generics, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from .models import Deal, Delivery, DeliveryItem
from .serializers import (
    DealSerializer,
    DealCreateSerializer,
    DealStatusUpdateSerializer,
    DealDriverAssignSerializer,
    DealDriverRequestSerializer,
    DealCompleteSerializer,
    DeliverySerializer,
    DeliveryCreateSerializer,
    DeliveryStatusUpdateSerializer,
    DeliveryAssignDriverSerializer,
)
from src.users.models import SupplierProfile, DriverProfile
from apps.core.utils import success_response, error_response
from apps.core.permissions import IsSupplier, IsSeller, IsDriver
from apps.core.pagination import StandardResultsSetPagination


# ==================== DEAL VIEWS ====================

class DealViewSet(viewsets.ModelViewSet):
    """Deal ViewSet - Manages deals before deliveries"""
    serializer_class = DealSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_supplier:
            return Deal.objects.filter(supplier=user.supplier_profile).select_related('seller', 'supplier', 'driver')
        elif user.is_seller:
            return Deal.objects.filter(seller=user.seller_profile).select_related('seller', 'supplier', 'driver')
        else:
            return Deal.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DealCreateSerializer
        return DealSerializer
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Deals listed successfully')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deal = serializer.save()
        response_serializer = DealSerializer(deal)
        return success_response(
            data=response_serializer.data,
            message='Deal created successfully',
            status_code=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return success_response(data=response.data, message='Deal detail')
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        """Update deal status"""
        deal = self.get_object()
        user = request.user
        
        # Permission check - only seller or supplier can update
        if not (user.is_supplier or user.is_seller):
            return error_response(
                message='Unauthorized access',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user is part of this deal
        if user.is_supplier and deal.supplier != user.supplier_profile:
            return error_response(
                message='This deal does not belong to you',
                status_code=status.HTTP_403_FORBIDDEN
            )
        if user.is_seller and deal.seller != user.seller_profile:
            return error_response(
                message='This deal does not belong to you',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DealStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            deal.status = serializer.validated_data['status']
            deal.save()
            return success_response(
                data=DealSerializer(deal).data,
                message='Deal status updated successfully'
            )
        return error_response(message='Update failed', errors=serializer.errors)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def assign_driver(self, request, pk=None):
        """Assign own driver to deal - Supplier or Seller can assign their own driver"""
        deal = self.get_object()
        user = request.user
        
        # Permission check
        if not (user.is_supplier or user.is_seller):
            return error_response(
                message='Unauthorized access',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user is part of this deal
        if user.is_supplier and deal.supplier != user.supplier_profile:
            return error_response(
                message='This deal does not belong to you',
                status_code=status.HTTP_403_FORBIDDEN
            )
        if user.is_seller and deal.seller != user.seller_profile:
            return error_response(
                message='This deal does not belong to you',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DealDriverAssignSerializer(data=request.data)
        if serializer.is_valid():
            driver = DriverProfile.objects.get(id=serializer.validated_data['driver_id'])
            deal.driver = driver
            # If driver is assigned, status changes to DEALING
            if deal.status == Deal.Status.LOOKING_FOR_DRIVER:
                deal.status = Deal.Status.DEALING
            deal.save()
            return success_response(
                data=DealSerializer(deal).data,
                message='Driver assigned successfully'
            )
        return error_response(message='Driver assignment failed', errors=serializer.errors)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def request_driver(self, request, pk=None):
        """Request driver for deal - Only when status is LOOKING_FOR_DRIVER"""
        deal = self.get_object()
        user = request.user
        
        # Status check
        if deal.status != Deal.Status.LOOKING_FOR_DRIVER:
            return error_response(
                message='Driver requests can only be made when deal status is LOOKING_FOR_DRIVER',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Permission check
        if not (user.is_supplier or user.is_seller):
            return error_response(
                message='Unauthorized access',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user is part of this deal
        if user.is_supplier and deal.supplier != user.supplier_profile:
            return error_response(
                message='This deal does not belong to you',
                status_code=status.HTTP_403_FORBIDDEN
            )
        if user.is_seller and deal.seller != user.seller_profile:
            return error_response(
                message='This deal does not belong to you',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # If cost_split is False, only one party can request
        if not deal.cost_split:
            # If driver is already assigned, cannot request another
            if deal.driver:
                return error_response(
                    message='Driver is already assigned to this deal',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = DealDriverRequestSerializer(data=request.data)
        if serializer.is_valid():
            driver = DriverProfile.objects.get(id=serializer.validated_data['driver_id'])
            deal.driver = driver
            deal.status = Deal.Status.DEALING
            deal.save()
            return success_response(
                data=DealSerializer(deal).data,
                message='Driver request sent successfully'
            )
        return error_response(message='Driver request failed', errors=serializer.errors)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        """Complete deal and create order - Only when status is DONE"""
        deal = self.get_object()
        user = request.user
        
        # Status check
        if deal.status != Deal.Status.DONE:
            return error_response(
                message='Deal can only be completed when status is DONE',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if delivery already exists
        if deal.delivery:
            return error_response(
                message='Delivery already created for this deal',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Permission check - only seller or supplier can complete
        if not (user.is_supplier or user.is_seller):
            return error_response(
                message='Unauthorized access',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user is part of this deal
        if user.is_supplier and deal.supplier != user.supplier_profile:
            return error_response(
                message='This deal does not belong to you',
                status_code=status.HTTP_403_FORBIDDEN
            )
        if user.is_seller and deal.seller != user.seller_profile:
            return error_response(
                message='This deal does not belong to you',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Create delivery from deal
        # Get driver information from deal
        driver_profile = None
        driver_name = None
        driver_phone = None
        driver_vehicle_type = None
        driver_vehicle_plate = None
        driver_license_number = None
        
        if deal.driver:
            driver_profile = deal.driver
            driver_name = deal.driver.user.get_full_name() or deal.driver.user.username
            driver_phone = deal.driver.user.phone_number
            driver_vehicle_type = deal.driver.vehicle_type
            driver_vehicle_plate = deal.driver.vehicle_plate
            driver_license_number = deal.driver.license_number
        
        # Default supplier_share is 100 (all to supplier), can be adjusted later
        delivery = Delivery.objects.create(
            deal=deal,
            supplier_share=100,  # Default: all to supplier, can be adjusted
            driver_profile=driver_profile,
            driver_name=driver_name,
            driver_phone=driver_phone,
            driver_vehicle_type=driver_vehicle_type,
            driver_vehicle_plate=driver_vehicle_plate,
            driver_license_number=driver_license_number,
            delivery_address=deal.delivery_address,
            delivery_note=deal.delivery_note,
            status=Delivery.Status.CONFIRMED
        )
        
        # Create delivery items from deal items
        for deal_item in deal.items.all():
            DeliveryItem.objects.create(
                delivery=delivery,
                product=deal_item.product,
                quantity=deal_item.quantity,
                unit_price=deal_item.unit_price
            )
        
        # Calculate total (this will also increment deal.delivery_count via save method)
        delivery.calculate_total()
        
        return success_response(
            data={
                'deal': DealSerializer(deal).data,
                'delivery': DeliverySerializer(delivery).data
            },
            message='Deal completed and delivery created successfully',
            status_code=status.HTTP_201_CREATED
        )


# ==================== DELIVERY VIEWS ====================

class DeliveryViewSet(viewsets.ModelViewSet):
    """Delivery ViewSet - Filtering by role"""
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_supplier:
            return Delivery.objects.filter(deal__supplier=user.supplier_profile).select_related('deal', 'deal__seller', 'deal__supplier', 'driver_profile')
        elif user.is_seller:
            return Delivery.objects.filter(deal__seller=user.seller_profile).select_related('deal', 'deal__seller', 'deal__supplier', 'driver_profile')
        elif user.is_driver:
            return Delivery.objects.filter(driver_profile=user.driver_profile).select_related('deal', 'deal__seller', 'deal__supplier', 'driver_profile')
        else:
            return Delivery.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DeliveryCreateSerializer
        return DeliverySerializer
    
    def perform_create(self, serializer):
        # Deliveries should be created from deals, not directly
        # This method should not be called as create is overridden
        pass
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Deliveries listed successfully')
    
    def create(self, request, *args, **kwargs):
        # Deliveries should be created from deals, not directly
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('Deliveries must be created from deals. Please complete a deal first.')
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return success_response(data=response.data, message='Delivery detail')
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        """Update delivery status - Supplier or Driver"""
        delivery = self.get_object()
        user = request.user
        
        # Permission check
        if not (user.is_supplier or user.is_driver):
            return error_response(
                message='Unauthorized access',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Supplier check
        if user.is_supplier and (not delivery.deal or delivery.deal.supplier != user.supplier_profile):
            return error_response(
                message='This delivery does not belong to you',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Driver check
        if user.is_driver and delivery.driver_profile != user.driver_profile:
            return error_response(
                message='This delivery does not belong to you',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DeliveryStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            delivery.status = serializer.validated_data['status']
            delivery.save()
            return success_response(
                data=DeliverySerializer(delivery).data,
                message='Delivery status updated successfully'
            )
        return error_response(message='Update failed', errors=serializer.errors)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated, IsSupplier])
    def assign_driver(self, request, pk=None):
        """Assign driver to delivery - Only supplier can do this"""
        delivery = self.get_object()
        
        # Supplier check
        if not delivery.deal or delivery.deal.supplier != request.user.supplier_profile:
            return error_response(
                message='This delivery does not belong to you',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DeliveryAssignDriverSerializer(data=request.data)
        if serializer.is_valid():
            driver_profile = DriverProfile.objects.get(id=serializer.validated_data['driver_id'])
            delivery.driver_profile = driver_profile
            # Populate driver info from profile
            delivery.driver_name = driver_profile.user.get_full_name() or driver_profile.user.username
            delivery.driver_phone = driver_profile.user.phone_number
            delivery.driver_vehicle_type = driver_profile.vehicle_type
            delivery.driver_vehicle_plate = driver_profile.vehicle_plate
            delivery.driver_license_number = driver_profile.license_number
            delivery.status = Delivery.Status.READY
            delivery.save()
            return success_response(
                data=DeliverySerializer(delivery).data,
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


class AvailableDeliveryListView(generics.ListAPIView):
    """Available deliveries for drivers"""
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated, IsDriver]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Deliveries without driver and ready status
        deliveries = Delivery.objects.filter(
            driver_profile__isnull=True,
            driver_name__isnull=True,
            status=Delivery.Status.READY
        ).select_related('deal', 'deal__seller', 'deal__supplier')
        
        # City filter (based on driver's city)
        driver_city = self.request.user.driver_profile.city
        if driver_city:
            deliveries = deliveries.filter(
                Q(deal__seller__city__icontains=driver_city) | Q(deal__supplier__city__icontains=driver_city)
            )
        
        return deliveries
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Available deliveries listed successfully')


class AcceptDeliveryView(generics.UpdateAPIView):
    """Driver accepts delivery"""
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated, IsDriver]
    
    def get_queryset(self):
        return Delivery.objects.filter(
            driver_profile__isnull=True,
            driver_name__isnull=True,
            status=Delivery.Status.READY
        )
    
    def update(self, request, *args, **kwargs):
        delivery = self.get_object()
        driver_profile = request.user.driver_profile
        delivery.driver_profile = driver_profile
        # Populate driver info from profile
        delivery.driver_name = driver_profile.user.get_full_name() or driver_profile.user.username
        delivery.driver_phone = driver_profile.user.phone_number
        delivery.driver_vehicle_type = driver_profile.vehicle_type
        delivery.driver_vehicle_plate = driver_profile.vehicle_plate
        delivery.driver_license_number = driver_profile.license_number
        delivery.status = Delivery.Status.PICKED_UP
        delivery.save()
        
        serializer = self.get_serializer(delivery)
        return success_response(
            data=serializer.data,
            message='Delivery accepted successfully'
        )
