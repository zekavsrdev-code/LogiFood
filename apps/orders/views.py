"""Order management views (Deals, Deliveries, Driver Requests)"""
from rest_framework import status, viewsets, generics, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from apps.core.schema import openapi_parameters_from_filterset
from apps.core.mixins import ActionValidationMixin, SuccessResponseListRetrieveMixin
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
DELIVERY_ORDERING_FIELDS = ['created_at', 'total_amount']
REQUEST_ORDERING_FIELDS = ['created_at', 'requested_price']


# ==================== DEAL VIEWS ====================


class DealViewSet(ActionValidationMixin, SuccessResponseListRetrieveMixin, viewsets.ModelViewSet):
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
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        deal = self.get_object()
        return self._run_action_validated(request, lambda d: success_response(
            data=DealSerializer(DealService.update_deal_status(deal, request.user, d['status'])).data,
            message='Deal status updated successfully',
        ))
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def assign_driver(self, request, pk=None):
        deal = self.get_object()
        return self._run_action_validated(request, lambda d: success_response(
            data=DealSerializer(DealService.assign_driver_to_deal(deal, request.user, d['driver_id'])).data,
            message='Driver assigned successfully',
        ))
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def request_driver(self, request, pk=None):
        deal = self.get_object()
        def run(d):
            r = DealService.request_driver_for_deal(deal, request.user, d['driver_id'], d['requested_price'])
            return success_response(
                data=RequestToDriverSerializer(r).data,
                message='Driver request sent successfully',
                status_code=status.HTTP_201_CREATED,
            )
        return self._run_action_validated(request, run)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        deal = self.get_object()
        def run(d):
            created = DealService.complete_deal(
                deal, request.user,
                d['delivery_address'],
                d.get('delivery_note', ''),
                d.get('supplier_share', 100),
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
        return self._run_action_validated(request, run)


# ==================== DELIVERY VIEWS ====================


class DeliveryViewSet(ActionValidationMixin, SuccessResponseListRetrieveMixin, viewsets.ModelViewSet):
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
        return self._run_action_validated(
            request,
            lambda d: success_response(
                data=DeliverySerializer(
                    DeliveryService.update_delivery_status(delivery, request.user, d['status'])
                ).data,
                message='Delivery status updated successfully',
            ),
            validation_message='Update failed',
        )
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated, IsSupplier])
    def assign_driver(self, request, pk=None):
        delivery = self.get_object()
        return self._run_action_validated(
            request,
            lambda d: success_response(
                data=DeliverySerializer(
                    DeliveryService.assign_driver_to_delivery(delivery, request.user, d['driver_id'])
                ).data,
                message='Driver assigned successfully',
            ),
            validation_message='Driver assignment failed',
        )


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


class RequestToDriverViewSet(ActionValidationMixin, SuccessResponseListRetrieveMixin, viewsets.ModelViewSet):
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
        return self._run_action_validated(
            request,
            lambda d: success_response(
                data=RequestToDriverSerializer(
                    RequestToDriverService.propose_price(
                        driver_request, request.user, d['proposed_price']
                    )
                ).data,
                message='Price proposed successfully',
            ),
            validation_message='Price proposal failed',
        )
    
    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        driver_request = self.get_object()
        def run(d):
            updated = RequestToDriverService.approve_request(
                driver_request, request.user, d.get('final_price')
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
        return self._run_action_validated(request, run, validation_message='Approval failed')
    
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
