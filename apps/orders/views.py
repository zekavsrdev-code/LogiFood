"""Order management views (Deals, Deliveries, Driver Requests)"""
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
from .services import (
    DealService,
    DeliveryService,
    RequestToDriverService,
)
from apps.core.utils import success_response, error_response
from apps.core.permissions import IsSupplier, IsSeller, IsDriver
from apps.core.pagination import StandardResultsSetPagination
from apps.core.exceptions import BusinessLogicError


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
        return DealService.get_user_deals(self.request.user)
    
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
        try:
            deal = DealService.create_deal(request.user, serializer.validated_data)
            response_serializer = DealSerializer(deal)
            return success_response(
                data=response_serializer.data,
                message='Deal created successfully',
                status_code=status.HTTP_201_CREATED
            )
        except BusinessLogicError as e:
            return error_response(
                message=str(e.detail),
                status_code=e.status_code
            )
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return success_response(data=response.data, message='Deal detail')
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        deal = self.get_object()
        serializer = DealStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                updated_deal = DealService.update_deal_status(
                    deal, 
                    request.user, 
                    serializer.validated_data['status']
                )
                return success_response(
                    data=DealSerializer(updated_deal).data,
                    message='Deal status updated successfully'
                )
            except BusinessLogicError as e:
                return error_response(
                    message=str(e.detail),
                    status_code=e.status_code
                )
        return error_response(message='Update failed', errors=serializer.errors)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def assign_driver(self, request, pk=None):
        deal = self.get_object()
        serializer = DealDriverAssignSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                updated_deal = DealService.assign_driver_to_deal(
                    deal,
                    request.user,
                    serializer.validated_data['driver_id']
                )
                return success_response(
                    data=DealSerializer(updated_deal).data,
                    message='Driver assigned successfully'
                )
            except BusinessLogicError as e:
                return error_response(
                    message=str(e.detail),
                    status_code=e.status_code
                )
        return error_response(message='Driver assignment failed', errors=serializer.errors)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def request_driver(self, request, pk=None):
        deal = self.get_object()
        serializer = DealDriverRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                driver_request = DealService.request_driver_for_deal(
                    deal,
                    request.user,
                    serializer.validated_data['driver_id'],
                    serializer.validated_data['requested_price']
                )
                return success_response(
                    data=RequestToDriverSerializer(driver_request).data,
                    message='Driver request sent successfully',
                    status_code=status.HTTP_201_CREATED
                )
            except BusinessLogicError as e:
                return error_response(
                    message=str(e.detail),
                    status_code=e.status_code
                )
        return error_response(message='Driver request failed', errors=serializer.errors)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        deal = self.get_object()
        serializer = DealCompleteSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(
                message='Invalid data',
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            created_deliveries = DealService.complete_deal(
                deal,
                request.user,
                serializer.validated_data['delivery_address'],
                serializer.validated_data.get('delivery_note', ''),
                serializer.validated_data.get('supplier_share', 100)
            )
            
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
        except BusinessLogicError as e:
            return error_response(
                message=str(e.detail),
                status_code=e.status_code
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
        return DeliveryService.get_user_deliveries(self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DeliveryCreateSerializer
        return DeliverySerializer
    
    def perform_create(self, serializer):
        pass
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Deliveries listed successfully')
    
    def create(self, request, *args, **kwargs):
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('Deliveries must be created from deals. Please complete a deal first.')
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return success_response(data=response.data, message='Delivery detail')
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        delivery = self.get_object()
        serializer = DeliveryStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                updated_delivery = DeliveryService.update_delivery_status(
                    delivery,
                    request.user,
                    serializer.validated_data['status']
                )
                return success_response(
                    data=DeliverySerializer(updated_delivery).data,
                    message='Delivery status updated successfully'
                )
            except BusinessLogicError as e:
                return error_response(
                    message=str(e.detail),
                    status_code=e.status_code
                )
        return error_response(message='Update failed', errors=serializer.errors)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated, IsSupplier])
    def assign_driver(self, request, pk=None):
        delivery = self.get_object()
        serializer = DeliveryAssignDriverSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                updated_delivery = DeliveryService.assign_driver_to_delivery(
                    delivery,
                    request.user,
                    serializer.validated_data['driver_id']
                )
                return success_response(
                    data=DeliverySerializer(updated_delivery).data,
                    message='Driver assigned successfully'
                )
            except BusinessLogicError as e:
                return error_response(
                    message=str(e.detail),
                    status_code=e.status_code
                )
        return error_response(message='Driver assignment failed', errors=serializer.errors)


# ==================== DELIVERY DISCOVERY VIEWS ====================


class AvailableDeliveryListView(generics.ListAPIView):
    """Available deliveries for drivers"""
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated, IsDriver]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return DeliveryService.get_available_deliveries(self.request.user)
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Available deliveries listed successfully')


class AcceptDeliveryView(generics.UpdateAPIView):
    """Driver delivery acceptance endpoint"""
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated, IsDriver]
    
    def get_queryset(self):
        return DeliveryService.get_available_deliveries(self.request.user)
    
    def update(self, request, *args, **kwargs):
        delivery = self.get_object()
        
        try:
            updated_delivery = DeliveryService.accept_delivery(delivery, request.user)
            serializer = self.get_serializer(updated_delivery)
            return success_response(
                data=serializer.data,
                message='Delivery accepted successfully'
            )
        except BusinessLogicError as e:
            return error_response(
                message=str(e.detail),
                status_code=e.status_code
            )


# ==================== REQUEST TO DRIVER VIEWS ====================


class RequestToDriverViewSet(viewsets.ModelViewSet):
    """Driver request management ViewSet"""
    serializer_class = RequestToDriverSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'deal', 'driver']
    ordering_fields = ['created_at', 'requested_price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return RequestToDriverService.get_user_requests(self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'propose_price':
            return RequestToDriverProposePriceSerializer
        elif self.action in ['approve', 'reject']:
            return RequestToDriverApproveSerializer
        return RequestToDriverSerializer
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message='Driver requests listed successfully')
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return success_response(data=response.data, message='Driver request detail')
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def propose_price(self, request, pk=None):
        driver_request = self.get_object()
        serializer = RequestToDriverProposePriceSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                updated_request = RequestToDriverService.propose_price(
                    driver_request,
                    request.user,
                    serializer.validated_data['proposed_price']
                )
                return success_response(
                    data=RequestToDriverSerializer(updated_request).data,
                    message='Price proposed successfully'
                )
            except BusinessLogicError as e:
                return error_response(
                    message=str(e.detail),
                    status_code=e.status_code
                )
        return error_response(message='Price proposal failed', errors=serializer.errors)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        driver_request = self.get_object()
        serializer = RequestToDriverApproveSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                updated_request = RequestToDriverService.approve_request(
                    driver_request,
                    request.user,
                    serializer.validated_data.get('final_price')
                )
                
                if updated_request.is_fully_approved():
                    message = 'Request approved by all parties and driver assigned to deal successfully'
                else:
                    pending = RequestToDriverService.get_pending_approvals(updated_request)
                    message = f'Request approved. Waiting for approval from: {", ".join(pending)}.'
                
                return success_response(
                    data=RequestToDriverSerializer(updated_request).data,
                    message=message
                )
            except BusinessLogicError as e:
                return error_response(
                    message=str(e.detail),
                    status_code=e.status_code
                )
        return error_response(message='Approval failed', errors=serializer.errors)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        driver_request = self.get_object()
        
        try:
            updated_request = RequestToDriverService.reject_request(
                driver_request,
                request.user
            )
            return success_response(
                data=RequestToDriverSerializer(updated_request).data,
                message='Request rejected successfully'
            )
        except BusinessLogicError as e:
            return error_response(
                message=str(e.detail),
                status_code=e.status_code
            )
