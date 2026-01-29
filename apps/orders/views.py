"""Order management views (Deals, Deliveries, Driver Requests)"""
from rest_framework import status, viewsets, generics, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from apps.core.schema import openapi_parameters_from_filterset
from apps.core.mixins import SuccessResponseListRetrieveMixin
from .models import Deal, DealItem, Delivery, DeliveryItem, RequestToDriver
from .serializers import (
    DealSerializer,
    DealCreateSerializer,
    DealUpdateSerializer,
    DealStatusUpdateSerializer,
    DealDriverAssignSerializer,
    DealDriverRequestSerializer,
    DealCompleteSerializer,
    DealItemSerializer,
    DealItemCreateUpdateSerializer,
    RequestToDriverSerializer,
    RequestToDriverProposePriceSerializer,
    RequestToDriverApproveSerializer,
    DeliverySerializer,
    DeliveryCreateSerializer,
    DeliveryStatusUpdateSerializer,
    DeliveryAssignDriverSerializer,
)
from .filters import DealFilter, DeliveryFilter, RequestToDriverFilter
from .services import (
    DealService,
    DeliveryService,
    RequestToDriverService,
)
from apps.core.utils import success_response, error_response
from apps.core.permissions import IsSupplier, IsSeller, IsDriver
from apps.core.pagination import StandardResultsSetPagination
from apps.core.exceptions import BusinessLogicError


# Ordering fields: single source for both OrderingFilter and OpenAPI
DEAL_ORDERING_FIELDS = ['created_at']
DELIVERY_ORDERING_FIELDS = ['created_at']
REQUEST_ORDERING_FIELDS = ['created_at', 'requested_price']


# ==================== DEAL VIEWS ====================


class DealViewSet(SuccessResponseListRetrieveMixin, viewsets.ModelViewSet):
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
    filterset_class = DealFilter
    ordering_fields = DEAL_ORDERING_FIELDS
    ordering = ['-created_at']
    list_success_message = 'Deals listed successfully'
    retrieve_success_message = 'Deal detail'

    def get_queryset(self):
        return DealService.get_user_deals(self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DealCreateSerializer
        if self.action in ('update', 'partial_update'):
            return DealUpdateSerializer
        if self.action == 'update_status':
            return DealStatusUpdateSerializer
        if self.action == 'assign_driver':
            return DealDriverAssignSerializer
        if self.action == 'request_driver':
            return DealDriverRequestSerializer
        if self.action == 'complete':
            return DealCompleteSerializer
        return DealSerializer

    @extend_schema(
        parameters=openapi_parameters_from_filterset(DealFilter, ordering_fields=DEAL_ORDERING_FIELDS)
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

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
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        deal = self.get_object()
        ser = self.get_serializer(deal, data=request.data, partial=False)
        ser.is_valid(raise_exception=True)
        try:
            updated = DealService.update_deal(deal, request.user, **ser.validated_data)
            return success_response(data=DealSerializer(updated).data, message='Deal updated successfully')
        except BusinessLogicError as e:
            return error_response(message=str(e.detail), status_code=e.status_code)

    def partial_update(self, request, *args, **kwargs):
        deal = self.get_object()
        ser = self.get_serializer(deal, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        try:
            updated = DealService.update_deal(deal, request.user, **ser.validated_data)
            return success_response(data=DealSerializer(updated).data, message='Deal updated successfully')
        except BusinessLogicError as e:
            return error_response(message=str(e.detail), status_code=e.status_code)

    @action(detail=True, methods=['put', 'post'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """Seller or supplier approves the current deal/items. Required before LOOKING_FOR_DRIVER or DONE."""
        deal = self.get_object()
        try:
            updated = DealService.approve_deal(deal, request.user)
            return success_response(data=DealSerializer(updated).data, message='Deal approved')
        except BusinessLogicError as e:
            return error_response(message=str(e.detail), status_code=e.status_code)

    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        deal = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = DealService.update_deal_status(deal, request.user, serializer.validated_data['status'])
            return success_response(
                data=DealSerializer(updated).data,
                message='Deal status updated successfully',
            )
        except BusinessLogicError as e:
            return error_response(message=str(e.detail), status_code=e.status_code)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def assign_driver(self, request, pk=None):
        deal = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = DealService.assign_driver_to_deal(deal, request.user, serializer.validated_data['driver_id'])
            return success_response(
                data=DealSerializer(updated).data,
                message='Driver assigned successfully',
            )
        except BusinessLogicError as e:
            return error_response(message=str(e.detail), status_code=e.status_code)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def request_driver(self, request, pk=None):
        deal = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
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
                status_code=status.HTTP_201_CREATED,
            )
        except BusinessLogicError as e:
            return error_response(message=str(e.detail), status_code=e.status_code)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        deal = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            created = DealService.complete_deal(
                deal, 
                request.user,
                serializer.validated_data['delivery_address'],
                serializer.validated_data.get('delivery_note', ''),
                serializer.validated_data.get('supplier_share', 100),
            )
            return success_response(
                data={
                    'deal': DealSerializer(deal).data,
                    'deliveries': [DeliverySerializer(x).data for x in created],
                    'created_count': len(created),
                    'total_planned': deal.delivery_count,
                },
                message=f'Deal completed and {len(created)} delivery(ies) created successfully',
                status_code=status.HTTP_201_CREATED,
            )
        except BusinessLogicError as e:
            return error_response(message=str(e.detail), status_code=e.status_code)


# ==================== DEAL ITEM VIEWS ====================


class DealItemViewSet(viewsets.ModelViewSet):
    """Deal items: both seller and supplier can create/update/delete. Clears the other party’s deal approval."""
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_seller:
            return DealItem.objects.filter(deal__seller=user.seller_profile).select_related('deal', 'product')
        if user.is_supplier:
            return DealItem.objects.filter(deal__supplier=user.supplier_profile).select_related('deal', 'product')
        return DealItem.objects.none()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return DealItemCreateUpdateSerializer
        return DealItemSerializer

    def _ensure_deal_editable(self, deal):
        if deal.status != Deal.Status.DEALING:
            raise BusinessLogicError(
                'Deal items can only be changed while deal status is Dealing',
                status_code=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        deal = serializer.validated_data.get('deal')
        self._ensure_deal_editable(deal)
        instance = serializer.save(created_by=self.request.user)
        DealService.clear_other_approval(instance.deal, self.request.user)
        instance.deal.save()

    def perform_update(self, serializer):
        self._ensure_deal_editable(serializer.instance.deal)
        super().perform_update(serializer)
        DealService.clear_other_approval(serializer.instance.deal, self.request.user)
        serializer.instance.deal.save()

    def perform_destroy(self, instance):
        self._ensure_deal_editable(instance.deal)
        deal = instance.deal
        super().perform_destroy(instance)
        DealService.clear_other_approval(deal, self.request.user)
        deal.save()


# ==================== DELIVERY VIEWS ====================


class DeliveryViewSet(SuccessResponseListRetrieveMixin, viewsets.ModelViewSet):
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
    filterset_class = DeliveryFilter
    ordering_fields = DELIVERY_ORDERING_FIELDS
    ordering = ['-created_at']
    list_success_message = 'Deliveries listed successfully'
    retrieve_success_message = 'Delivery detail'

    def get_queryset(self):
        return DeliveryService.get_user_deliveries(self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DeliveryCreateSerializer
        if self.action == 'update_status':
            return DeliveryStatusUpdateSerializer
        if self.action == 'assign_driver':
            return DeliveryAssignDriverSerializer
        return DeliverySerializer
    
    def perform_create(self, serializer):
        pass

    @extend_schema(
        parameters=openapi_parameters_from_filterset(
            DeliveryFilter, ordering_fields=DELIVERY_ORDERING_FIELDS
        )
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('Deliveries must be created from deals. Please complete a deal first.')
    
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        delivery = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = DeliveryService.update_delivery_status(
                delivery, 
                request.user, 
                serializer.validated_data['status']
            )
            return success_response(
                data=DeliverySerializer(updated).data,
                message='Delivery status updated successfully',
            )
        except BusinessLogicError as e:
            return error_response(message=str(e.detail), status_code=e.status_code)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated, IsSupplier])
    def assign_driver(self, request, pk=None):
        delivery = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = DeliveryService.assign_driver_to_delivery(
                delivery, 
                request.user, 
                serializer.validated_data['driver_id']
            )
            return success_response(
                data=DeliverySerializer(updated).data,
                message='Driver assigned successfully',
            )
        except BusinessLogicError as e:
            return error_response(message=str(e.detail), status_code=e.status_code)


# ==================== DELIVERY DISCOVERY VIEWS ====================


class AvailableDeliveryListView(SuccessResponseListRetrieveMixin, generics.ListAPIView):
    """Available deliveries for drivers. Uses DELIVERY_ORDERING_FIELDS as single source for ordering."""
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated, IsDriver]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = DELIVERY_ORDERING_FIELDS
    ordering = ['-created_at']
    list_success_message = 'Available deliveries listed successfully'

    def get_queryset(self):
        return DeliveryService.get_available_deliveries(self.request.user)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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


class RequestToDriverViewSet(SuccessResponseListRetrieveMixin, viewsets.ModelViewSet):
    """Driver request management ViewSet"""
    serializer_class = RequestToDriverSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RequestToDriverFilter
    ordering_fields = REQUEST_ORDERING_FIELDS
    ordering = ['-created_at']
    list_success_message = 'Driver requests listed successfully'
    retrieve_success_message = 'Driver request detail'

    def get_queryset(self):
        return RequestToDriverService.get_user_requests(self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'propose_price':
            return RequestToDriverProposePriceSerializer
        if self.action in ['approve', 'reject']:
            return RequestToDriverApproveSerializer
        return RequestToDriverSerializer

    @extend_schema(
        parameters=openapi_parameters_from_filterset(
            RequestToDriverFilter, ordering_fields=REQUEST_ORDERING_FIELDS
        )
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def propose_price(self, request, pk=None):
        driver_request = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = RequestToDriverService.propose_price(
                driver_request, 
                request.user, 
                serializer.validated_data['proposed_price']
            )
            return success_response(
                data=RequestToDriverSerializer(updated).data,
                message='Price proposed successfully',
            )
        except BusinessLogicError as e:
            return error_response(message=str(e.detail), status_code=e.status_code)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        driver_request = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = RequestToDriverService.approve_request(
                driver_request, 
                request.user, 
                serializer.validated_data.get('final_price')
            )
            if updated.is_fully_approved():
                msg = 'Request approved by all parties and driver assigned to deal successfully'
            else:
                pending = RequestToDriverService.get_pending_approvals(updated)
                msg = f'Request approved. Waiting for approval from: {", ".join(pending)}.'
            return success_response(
                data=RequestToDriverSerializer(updated).data,
                message=msg,
            )
        except BusinessLogicError as e:
            return error_response(message=str(e.detail), status_code=e.status_code)
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        driver_request = self.get_object()
        try:
            updated = RequestToDriverService.reject_request(driver_request, request.user)
            return success_response(
                data=RequestToDriverSerializer(updated).data,
                message='Request rejected successfully',
            )
        except BusinessLogicError as e:
            return error_response(message=str(e.detail), status_code=e.status_code)
