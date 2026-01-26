"""
Order management views (Deals, Deliveries, Driver Requests).

All views use DRF generic views and viewsets following best practices:
- ViewSets for CRUD operations
- Generic views for specific read/update operations
- Custom actions for business logic
"""
from rest_framework import status, viewsets, generics, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from .models import Deal, Delivery, DeliveryItem, RequestToDriver
from .serializers import (
    DealSerializer,
    DealCreateSerializer,
    DealStatusUpdateSerializer,
    DealDriverAssignSerializer,
    DealDriverRequestSerializer,
    DealCompleteSerializer,
    RequestToDriverSerializer,
    RequestToDriverProposePriceSerializer,
    RequestToDriverApproveSerializer,
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
    """
    Deal management ViewSet.
    
    Full CRUD operations for deals:
    - GET /api/orders/deals/ - List user's deals (filtered by role)
    - POST /api/orders/deals/ - Create new deal
    - GET /api/orders/deals/{id}/ - Retrieve deal detail
    - PUT /api/orders/deals/{id}/update_status/ - Update deal status
    - PUT /api/orders/deals/{id}/assign_driver/ - Assign driver to deal
    - PUT /api/orders/deals/{id}/request_driver/ - Request driver for deal
    - POST /api/orders/deals/{id}/complete/ - Complete deal and create deliveries
    """
    serializer_class = DealSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return deals filtered by user's role."""
        user = self.request.user
        
        if user.is_supplier:
            return Deal.objects.filter(
                supplier=user.supplier_profile
            ).select_related('seller', 'supplier', 'driver')
        elif user.is_seller:
            return Deal.objects.filter(
                seller=user.seller_profile
            ).select_related('seller', 'supplier', 'driver')
        else:
            return Deal.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return DealCreateSerializer
        return DealSerializer
    
    def list(self, request, *args, **kwargs):
        """List user's deals."""
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Deals listed successfully')
    
    def create(self, request, *args, **kwargs):
        """Create a new deal."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deal = serializer.save(created_by=request.user)
        response_serializer = DealSerializer(deal)
        return success_response(
            data=response_serializer.data,
            message='Deal created successfully',
            status_code=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve deal detail."""
        response = super().retrieve(request, *args, **kwargs)
        return success_response(data=response.data, message='Deal detail')
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        """
        Update deal status.
        
        Only seller or supplier who are part of the deal can update status.
        """
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
        """
        Assign own driver to deal.
        
        Supplier or Seller can assign their own driver directly.
        Changes deal status to DEALING if it was LOOKING_FOR_DRIVER.
        """
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
        """
        Request driver for deal.
        
        Only available when:
        - Deal status is LOOKING_FOR_DRIVER
        - Delivery handler is SYSTEM_DRIVER
        - No driver is already assigned
        
        Creates a RequestToDriver instance that requires approval from all parties.
        """
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
        
        # If delivery_handler is not SYSTEM_DRIVER, cannot request driver (3rd party handles it)
        if deal.delivery_handler != Deal.DeliveryHandler.SYSTEM_DRIVER:
            return error_response(
                message='Cannot request driver for 3rd party deliveries',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # If driver is already assigned, cannot request another
        if deal.driver:
            return error_response(
                message='Driver is already assigned to this deal',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = DealDriverRequestSerializer(data=request.data)
        if serializer.is_valid():
            driver = DriverProfile.objects.get(id=serializer.validated_data['driver_id'])
            requested_price = serializer.validated_data['requested_price']
            
            # Check if request already exists
            if RequestToDriver.objects.filter(deal=deal, driver=driver).exists():
                return error_response(
                    message='Request to this driver already exists',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Create request to driver
            # created_by is the user who created the request (supplier or seller)
            driver_request = RequestToDriver.objects.create(
                deal=deal,
                driver=driver,
                requested_price=requested_price,
                status=RequestToDriver.Status.PENDING,
                created_by=request.user
            )
            
            return success_response(
                data=RequestToDriverSerializer(driver_request).data,
                message='Driver request sent successfully',
                status_code=status.HTTP_201_CREATED
            )
        return error_response(message='Driver request failed', errors=serializer.errors)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        """
        Complete deal and create deliveries.
        
        Only available when:
        - Deal status is DONE
        - Not all planned deliveries have been created yet
        
        Creates the remaining deliveries (delivery_count - existing deliveries)
        with ESTIMATED status. Each delivery includes all deal items.
        """
        deal = self.get_object()
        user = request.user
        
        # Status check
        if deal.status != Deal.Status.DONE:
            return error_response(
                message='Deal can only be completed when status is DONE',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if all planned deliveries have been created
        # delivery_count is the planned number of deliveries for this deal
        # If actual deliveries >= planned deliveries, all deliveries have been created
        actual_delivery_count = deal.deliveries.count()
        if actual_delivery_count >= deal.delivery_count:
            return error_response(
                message=f'All planned deliveries ({deal.delivery_count}) have already been created for this deal',
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
        
        # Validate serializer to get delivery_address and delivery_note
        serializer = DealCompleteSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='Invalid data',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Get validated data
        delivery_address = serializer.validated_data['delivery_address']
        delivery_note = serializer.validated_data.get('delivery_note', '')
        supplier_share = serializer.validated_data.get('supplier_share', 100)
        
        # Get driver information based on delivery_handler
        driver_profile = None
        driver_name = None
        driver_phone = None
        driver_vehicle_type = None
        driver_vehicle_plate = None
        driver_license_number = None
        
        if deal.delivery_handler == Deal.DeliveryHandler.SYSTEM_DRIVER:
            # Use system driver from deal - only set driver_profile, not manual fields
            if deal.driver:
                driver_profile = deal.driver
                # Manual driver fields should be None when using system driver
                driver_name = None
                driver_phone = None
                driver_vehicle_type = None
                driver_vehicle_plate = None
                driver_license_number = None
        # For SUPPLIER or SELLER (3rd party), all driver fields remain None
        # The supplier/seller will handle delivery themselves or provide driver info later
        
        # Calculate how many deliveries still need to be created
        # delivery_count is the planned number of deliveries for this deal
        existing_deliveries_count = deal.deliveries.count()
        remaining_deliveries = deal.delivery_count - existing_deliveries_count
        
        if remaining_deliveries <= 0:
            return error_response(
                message=f'All planned deliveries ({deal.delivery_count}) have already been created for this deal',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create all remaining deliveries (delivery_count - existing_deliveries_count)
        # Each delivery will be created with ESTIMATED status
        created_deliveries = []
        for i in range(remaining_deliveries):
            delivery = Delivery.objects.create(
                deal=deal,
                supplier_share=supplier_share,
                driver_profile=driver_profile,
                driver_name=driver_name,
                driver_phone=driver_phone,
                driver_vehicle_type=driver_vehicle_type,
                driver_vehicle_plate=driver_vehicle_plate,
                driver_license_number=driver_license_number,
                delivery_address=delivery_address,
                delivery_note=delivery_note,
                status=Delivery.Status.ESTIMATED,  # Created as ESTIMATED status
                created_by=request.user
            )
            
            # Create delivery items from deal items
            # For now, each delivery gets all items (can be customized later to split items across deliveries)
            for deal_item in deal.items.all():
                DeliveryItem.objects.create(
                    delivery=delivery,
                    product=deal_item.product,
                    quantity=deal_item.quantity,
                    unit_price=deal_item.unit_price,
                    created_by=request.user
                )
            
            # Calculate total
            delivery.calculate_total()
            created_deliveries.append(delivery)
        
        return success_response(
            data={
                'deal': DealSerializer(deal).data,
                'deliveries': [DeliverySerializer(d).data for d in created_deliveries],
                'created_count': len(created_deliveries),
                'total_planned': deal.delivery_count
            },
            message=f'Deal completed and {len(created_deliveries)} delivery(ies) created successfully',
            status_code=status.HTTP_201_CREATED
        )


# ==================== DELIVERY VIEWS ====================


class DeliveryViewSet(viewsets.ModelViewSet):
    """
    Delivery management ViewSet.
    
    Full CRUD operations for deliveries (filtered by role):
    - GET /api/orders/deliveries/ - List user's deliveries
    - GET /api/orders/deliveries/{id}/ - Retrieve delivery detail
    - PUT /api/orders/deliveries/{id}/update_status/ - Update delivery status
    - PUT /api/orders/deliveries/{id}/assign_driver/ - Assign driver to delivery
    
    Note: Deliveries cannot be created directly - they must be created from deals.
    """
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return deliveries filtered by user's role."""
        user = self.request.user
        
        if user.is_supplier:
            return Delivery.objects.filter(
                deal__supplier=user.supplier_profile
            ).select_related('deal', 'deal__seller', 'deal__supplier', 'driver_profile')
        elif user.is_seller:
            return Delivery.objects.filter(
                deal__seller=user.seller_profile
            ).select_related('deal', 'deal__seller', 'deal__supplier', 'driver_profile')
        elif user.is_driver:
            return Delivery.objects.filter(
                driver_profile=user.driver_profile
            ).select_related('deal', 'deal__seller', 'deal__supplier', 'driver_profile')
        else:
            return Delivery.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return DeliveryCreateSerializer
        return DeliverySerializer
    
    def perform_create(self, serializer):
        """
        Prevent direct delivery creation.
        
        Deliveries should be created from deals, not directly.
        This method should not be called as create is overridden.
        """
        pass
    
    def list(self, request, *args, **kwargs):
        """List user's deliveries."""
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Deliveries listed successfully')
    
    def create(self, request, *args, **kwargs):
        """
        Prevent direct delivery creation.
        
        Deliveries must be created from deals. Please complete a deal first.
        """
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('Deliveries must be created from deals. Please complete a deal first.')
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve delivery detail."""
        response = super().retrieve(request, *args, **kwargs)
        return success_response(data=response.data, message='Delivery detail')
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        """
        Update delivery status.
        
        Only supplier or driver who are part of the delivery can update status.
        """
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
        """
        Assign driver to delivery.
        
        Only supplier who owns the delivery can assign a driver.
        Sets delivery status to READY after assignment.
        """
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
            # Manual fields should be None when using system driver
            delivery.driver_name = None
            delivery.driver_phone = None
            delivery.driver_vehicle_type = None
            delivery.driver_vehicle_plate = None
            delivery.driver_license_number = None
            delivery.status = Delivery.Status.READY
            delivery.save()
            return success_response(
                data=DeliverySerializer(delivery).data,
                message='Driver assigned successfully'
            )
        return error_response(message='Driver assignment failed', errors=serializer.errors)


# ==================== DISCOVERY VIEWS ====================


class SupplierListView(generics.ListAPIView):
    """
    Supplier discovery endpoint.
    
    GET /api/orders/suppliers/ - List all active suppliers with product counts
    Accessible by authenticated users (typically sellers looking for suppliers).
    """
    queryset = SupplierProfile.objects.filter(is_active=True).select_related('user')
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['city']
    search_fields = ['company_name', 'description']
    
    def list(self, request, *args, **kwargs):
        """List suppliers with product counts."""
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
    """
    Driver discovery endpoint.
    
    GET /api/orders/drivers/ - List all available drivers
    Accessible by suppliers looking for drivers.
    """
    queryset = DriverProfile.objects.filter(
        is_active=True, 
        is_available=True
    ).select_related('user')
    permission_classes = [IsAuthenticated, IsSupplier]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['city', 'vehicle_type']
    
    def list(self, request, *args, **kwargs):
        """List available drivers with their details."""
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
    """
    Available deliveries for drivers.
    
    GET /api/orders/available-orders/ - List deliveries ready for driver acceptance
    Shows deliveries without assigned driver and READY status.
    Filtered by driver's city if available.
    """
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated, IsDriver]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return deliveries available for driver acceptance."""
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
                Q(deal__seller__city__icontains=driver_city) | 
                Q(deal__supplier__city__icontains=driver_city)
            )
        
        return deliveries
    
    def list(self, request, *args, **kwargs):
        """List available deliveries for driver acceptance."""
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Available deliveries listed successfully')


class AcceptDeliveryView(generics.UpdateAPIView):
    """
    Driver delivery acceptance endpoint.
    
    PUT /api/orders/accept-order/{id}/ - Driver accepts an available delivery
    Sets delivery status to PICKED_UP and assigns driver to delivery.
    """
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated, IsDriver]
    
    def get_queryset(self):
        """Return deliveries available for acceptance."""
        return Delivery.objects.filter(
            driver_profile__isnull=True,
            driver_name__isnull=True,
            status=Delivery.Status.READY
        )
    
    def update(self, request, *args, **kwargs):
        """Accept delivery and assign driver."""
        delivery = self.get_object()
        delivery.driver_profile = request.user.driver_profile
        # Manual fields should be None when using system driver
        delivery.driver_name = None
        delivery.driver_phone = None
        delivery.driver_vehicle_type = None
        delivery.driver_vehicle_plate = None
        delivery.driver_license_number = None
        delivery.status = Delivery.Status.PICKED_UP
        delivery.save()
        
        serializer = self.get_serializer(delivery)
        return success_response(
            data=serializer.data,
            message='Delivery accepted successfully'
        )


# ==================== REQUEST TO DRIVER VIEWS ====================


class RequestToDriverViewSet(viewsets.ModelViewSet):
    """
    Driver request management ViewSet.
    
    Manages driver requests for deals with LOOKING_FOR_DRIVER status:
    - GET /api/orders/driver-requests/ - List driver requests (filtered by role)
    - GET /api/orders/driver-requests/{id}/ - Retrieve request detail
    - PUT /api/orders/driver-requests/{id}/propose_price/ - Driver proposes price
    - PUT /api/orders/driver-requests/{id}/approve/ - Approve request (supplier/seller/driver)
    - PUT /api/orders/driver-requests/{id}/reject/ - Reject request
    
    All 3 parties (supplier, seller, driver) must approve for request to be accepted.
    """
    serializer_class = RequestToDriverSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'deal', 'driver']
    ordering_fields = ['created_at', 'requested_price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return requests filtered by user's role."""
        user = self.request.user
        
        # Drivers can see requests sent to them
        if user.is_driver:
            return RequestToDriver.objects.filter(
                driver=user.driver_profile,
                deal__delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER
            ).select_related('deal', 'driver')
        
        # Suppliers can see requests for their deals
        if user.is_supplier:
            return RequestToDriver.objects.filter(
                deal__supplier=user.supplier_profile,
                deal__delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER
            ).select_related('deal', 'driver')
        
        # Sellers can see requests for their deals
        if user.is_seller:
            return RequestToDriver.objects.filter(
                deal__seller=user.seller_profile,
                deal__delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER
            ).select_related('deal', 'driver')
        
        return RequestToDriver.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'propose_price':
            return RequestToDriverProposePriceSerializer
        elif self.action in ['approve', 'reject']:
            return RequestToDriverApproveSerializer
        return RequestToDriverSerializer
    
    def list(self, request, *args, **kwargs):
        """List driver requests."""
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Driver requests listed successfully')
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve driver request detail."""
        response = super().retrieve(request, *args, **kwargs)
        return success_response(data=response.data, message='Driver request detail')
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def propose_price(self, request, pk=None):
        """
        Driver proposes a price (counter offer).
        
        Only the requested driver can propose a price.
        Available when request status is PENDING or COUNTER_OFFERED.
        """
        driver_request = self.get_object()
        user = request.user
        
        # Only driver can propose price
        if not user.is_driver or driver_request.driver != user.driver_profile:
            return error_response(
                message='Only the requested driver can propose a price',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check status
        if driver_request.status not in [
            RequestToDriver.Status.PENDING, 
            RequestToDriver.Status.COUNTER_OFFERED
        ]:
            return error_response(
                message='Can only propose price for pending or counter-offered requests',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RequestToDriverProposePriceSerializer(data=request.data)
        if serializer.is_valid():
            driver_request.driver_proposed_price = serializer.validated_data['proposed_price']
            driver_request.status = RequestToDriver.Status.DRIVER_PROPOSED
            driver_request.save()
            
            return success_response(
                data=RequestToDriverSerializer(driver_request).data,
                message='Price proposed successfully'
            )
        return error_response(message='Price proposal failed', errors=serializer.errors)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """
        Approve driver request.
        
        All 3 parties (supplier, seller, driver) must approve for request to be accepted.
        When fully approved, driver is automatically assigned to the deal.
        """
        driver_request = self.get_object()
        user = request.user
        
        # Refresh request from DB to ensure we have latest data (especially deal relationship)
        driver_request.refresh_from_db()
        
        # Check if user can approve
        if not driver_request.can_approve(user):
            return error_response(
                message='You are not authorized to approve this request',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check status
        if driver_request.status not in [
            RequestToDriver.Status.PENDING, 
            RequestToDriver.Status.DRIVER_PROPOSED
        ]:
            return error_response(
                message='Can only approve pending or driver-proposed requests',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RequestToDriverApproveSerializer(data=request.data)
        if serializer.is_valid():
            final_price = serializer.validated_data.get('final_price')
            
            # Set approval based on user role
            # Note: can_approve() already verified user has permission, so we can safely set the flag
            if user.is_supplier:
                driver_request.supplier_approved = True
            elif user.is_seller:
                driver_request.seller_approved = True
            elif user.is_driver:
                driver_request.driver_approved = True
            else:
                # This shouldn't happen if can_approve() is working correctly
                return error_response(
                    message='Invalid user role for approval',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Save the approval - save all fields to ensure approval flags are persisted
            driver_request.save()
            
            # Check if fully approved (all 3 parties), then accept
            # Note: is_fully_approved() will get fresh deal from DB, so no need to refresh here
            if driver_request.is_fully_approved():
                try:
                    # Use final_price if provided, otherwise use driver_proposed_price or requested_price
                    if not final_price:
                        final_price = driver_request.driver_proposed_price or driver_request.requested_price
                    driver_request.accept(final_price)
                    return success_response(
                        data=RequestToDriverSerializer(driver_request).data,
                        message='Request approved by all parties and driver assigned to deal successfully'
                    )
                except ValueError as e:
                    return error_response(
                        message=str(e),
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
            else:
                # Check who still needs to approve
                pending_approvals = []
                if not driver_request.supplier_approved:
                    pending_approvals.append('supplier')
                if not driver_request.seller_approved:
                    pending_approvals.append('seller')
                if not driver_request.driver_approved:
                    pending_approvals.append('driver')
                
                return success_response(
                    data=RequestToDriverSerializer(driver_request).data,
                    message=f'Request approved. Waiting for approval from: {", ".join(pending_approvals)}.'
                )
        return error_response(message='Approval failed', errors=serializer.errors)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """
        Reject driver request.
        
        Driver, Supplier, or Seller who are part of the request can reject it.
        """
        driver_request = self.get_object()
        user = request.user
        
        # Check if user can reject
        can_reject = False
        if user.is_driver and driver_request.driver == user.driver_profile:
            can_reject = True
        elif user.is_supplier and driver_request.deal.supplier == user.supplier_profile:
            can_reject = True
        elif user.is_seller and driver_request.deal.seller == user.seller_profile:
            can_reject = True
        
        if not can_reject:
            return error_response(
                message='You are not authorized to reject this request',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        driver_request.status = RequestToDriver.Status.REJECTED
        driver_request.save()
        
        return success_response(
            data=RequestToDriverSerializer(driver_request).data,
            message='Request rejected successfully'
        )
