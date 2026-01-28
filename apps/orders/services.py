"""Order service layer for business logic."""
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.db.models import Q
from rest_framework import status

from .models import Deal, Delivery, DeliveryItem, RequestToDriver
from apps.users.models import SupplierProfile, SellerProfile, DriverProfile
from apps.products.models import Product
from apps.core.services import BaseService
from apps.core.exceptions import BusinessLogicError


# ==================== DEAL SERVICE ====================


class DealService(BaseService):
    """Service for deal-related business logic"""
    model = Deal
    
    @classmethod
    def get_user_deals(cls, user) -> List[Deal]:
        """Get deals filtered by user's role"""
        if user.is_supplier:
            return cls.model.objects.filter(
                supplier=user.supplier_profile
            ).select_related('seller', 'supplier', 'driver')
        elif user.is_seller:
            return cls.model.objects.filter(
                seller=user.seller_profile
            ).select_related('seller', 'supplier', 'driver')
        else:
            return cls.model.objects.none()
    
    @classmethod
    def _convert_ids_to_objects(cls, validated_data: Dict[str, Any]) -> None:
        """Convert ID fields to model objects"""
        if 'supplier_id' in validated_data:
            validated_data['supplier'] = SupplierProfile.objects.get(
                id=validated_data.pop('supplier_id')
            )
        
        if 'seller_id' in validated_data:
            validated_data['seller'] = SellerProfile.objects.get(
                id=validated_data.pop('seller_id')
            )
        
        if 'driver_id' in validated_data:
            driver_id = validated_data.pop('driver_id')
            if driver_id:
                validated_data['driver'] = DriverProfile.objects.get(id=driver_id)
    
    @classmethod
    def _validate_delivery_handler(cls, user, delivery_handler: str) -> None:
        """Validate delivery handler based on user role"""
        if user.is_seller and delivery_handler == cls.model.DeliveryHandler.SUPPLIER:
            raise BusinessLogicError(
                'Seller cannot set delivery handler to SUPPLIER',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        if user.is_supplier and delivery_handler == cls.model.DeliveryHandler.SELLER:
            raise BusinessLogicError(
                'Supplier cannot set delivery handler to SELLER',
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @classmethod
    def _prepare_deal_data(cls, user, validated_data: Dict[str, Any]) -> None:
        """Prepare deal data with business logic"""
        delivery_handler = validated_data.get(
            'delivery_handler', 
            cls.model.DeliveryHandler.SYSTEM_DRIVER
        )
        
        cls._validate_delivery_handler(user, delivery_handler)
        
        if delivery_handler != cls.model.DeliveryHandler.SYSTEM_DRIVER:
            validated_data['delivery_cost_split'] = 50
        if delivery_handler == cls.model.DeliveryHandler.SYSTEM_DRIVER:
            driver = validated_data.get('driver')
            validated_data['status'] = (
                cls.model.Status.DEALING if driver 
                else cls.model.Status.LOOKING_FOR_DRIVER
            )
        else:
            validated_data['driver'] = None
            validated_data['status'] = cls.model.Status.DEALING
    
    @classmethod
    def _create_deal_items(cls, deal: Deal, items_data: List[Dict[str, Any]], user) -> None:
        """Create deal items from validated data"""
        from .models import DealItem
        
        for item_data in items_data:
            product_id = item_data.pop('product_id', None) or item_data.pop('product', None)
            if isinstance(product_id, int):
                product = Product.objects.get(id=product_id, supplier=deal.supplier)
                item_data['product'] = product
            
            DealItem.objects.create(
                deal=deal,
                created_by=user,
                **item_data
            )
    
    @classmethod
    @transaction.atomic
    def create_deal(cls, user, validated_data: Dict[str, Any]) -> Deal:
        """Create a new deal with business logic validation"""
        items_data = validated_data.pop('items', [])
        
        cls._convert_ids_to_objects(validated_data)
        cls._prepare_deal_data(user, validated_data)
        
        deal = cls.model.objects.create(created_by=user, **validated_data)
        
        if items_data:
            cls._create_deal_items(deal, items_data, user)
        
        return deal
    
    @classmethod
    def can_user_access_deal(cls, deal: Deal, user) -> bool:
        """Check if user can access this deal"""
        if user.is_supplier:
            return deal.supplier_id == user.supplier_profile.id
        elif user.is_seller:
            return deal.seller_id == user.seller_profile.id
        return False
    
    @classmethod
    def _check_deal_permission(cls, deal: Deal, user) -> None:
        """Check if user has permission to modify deal"""
        if not (user.is_supplier or user.is_seller):
            raise BusinessLogicError(
                'Unauthorized access', 
                status_code=status.HTTP_403_FORBIDDEN
            )
        if not cls.can_user_access_deal(deal, user):
            raise BusinessLogicError(
                'This deal does not belong to you', 
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    @classmethod
    def update_deal_status(cls, deal: Deal, user, new_status: str) -> Deal:
        """Update deal status with permission check"""
        cls._check_deal_permission(deal, user)
        
        deal.status = new_status
        deal.save()
        return deal
    
    @classmethod
    def assign_driver_to_deal(cls, deal: Deal, user, driver_id: int) -> Deal:
        """Assign driver to deal with permission check"""
        cls._check_deal_permission(deal, user)
        
        driver = DriverProfile.objects.get(id=driver_id)
        deal.driver = driver
        
        if deal.status == Deal.Status.LOOKING_FOR_DRIVER:
            deal.status = Deal.Status.DEALING
        
        deal.save()
        return deal
    
    @classmethod
    def _validate_driver_request_prerequisites(cls, deal: Deal, user) -> None:
        """Validate prerequisites for driver request (helper method)"""
        if deal.status != Deal.Status.LOOKING_FOR_DRIVER:
            raise BusinessLogicError(
                'Driver requests can only be made when deal status is LOOKING_FOR_DRIVER',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        cls._check_deal_permission(deal, user)
        
        if deal.delivery_handler != Deal.DeliveryHandler.SYSTEM_DRIVER:
            raise BusinessLogicError(
                'Cannot request driver for 3rd party deliveries',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if deal.driver:
            raise BusinessLogicError(
                'Driver is already assigned to this deal',
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @classmethod
    def request_driver_for_deal(cls, deal: Deal, user, driver_id: int, requested_price: float) -> RequestToDriver:
        """Request driver for deal with validation"""
        cls._validate_driver_request_prerequisites(deal, user)
        
        driver = DriverProfile.objects.get(id=driver_id)
        
        if RequestToDriver.objects.filter(deal=deal, driver=driver).exists():
            raise BusinessLogicError(
                'Request to this driver already exists',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return RequestToDriver.objects.create(
            deal=deal,
            driver=driver,
            requested_price=requested_price,
            status=RequestToDriver.Status.PENDING,
            created_by=user
        )
    
    @classmethod
    def _validate_deal_completion(cls, deal: Deal, user) -> None:
        """Validate deal can be completed (helper method)"""
        if deal.status != Deal.Status.DONE:
            raise BusinessLogicError(
                'Deal can only be completed when status is DONE',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        cls._check_deal_permission(deal, user)
        
        actual_count = deal.deliveries.count()
        if actual_count >= deal.delivery_count:
            raise BusinessLogicError(
                f'All planned deliveries ({deal.delivery_count}) have already been created',
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @classmethod
    def _get_driver_info_for_delivery(cls, deal: Deal) -> Dict[str, Any]:
        """Get driver information for delivery based on deal"""
        if deal.delivery_handler == Deal.DeliveryHandler.SYSTEM_DRIVER and deal.driver:
            return {'driver_profile': deal.driver}
        return {'driver_profile': None}
    
    @classmethod
    def _create_delivery_with_items(cls, deal: Deal, delivery_data: Dict[str, Any], user) -> Delivery:
        """Create a single delivery with items"""
        delivery = Delivery.objects.create(**delivery_data, created_by=user)
        
        for deal_item in deal.items.all():
            DeliveryItem.objects.create(
                delivery=delivery, deal_item=deal_item, quantity=deal_item.quantity, created_by=user
            )
        return delivery
    
    @classmethod
    @transaction.atomic
    def complete_deal(cls, deal: Deal, user, delivery_address: str, 
                     delivery_note: str = '', supplier_share: int = 100) -> List[Delivery]:
        """Complete deal and create remaining deliveries"""
        cls._validate_deal_completion(deal, user)
        
        existing_count = deal.deliveries.count()
        remaining = deal.delivery_count - existing_count
        
        driver_info = cls._get_driver_info_for_delivery(deal)
        
        delivery_data = {
            'deal': deal,
            'supplier_share': supplier_share,
            'delivery_address': delivery_address,
            'delivery_note': delivery_note,
            'status': Delivery.Status.ESTIMATED,
            **driver_info
        }
        
        created_deliveries = []
        for _ in range(remaining):
            delivery = cls._create_delivery_with_items(deal, delivery_data, user)
            created_deliveries.append(delivery)
        
        return created_deliveries


# ==================== DELIVERY SERVICE ====================


class DeliveryService(BaseService):
    """Service for delivery-related business logic"""
    model = Delivery
    
    @classmethod
    def get_user_deliveries(cls, user) -> List[Delivery]:
        """Get deliveries filtered by user's role"""
        if user.is_supplier:
            return cls.model.objects.filter(
                deal__supplier=user.supplier_profile
            ).select_related('deal', 'deal__seller', 'deal__supplier', 'driver_profile')
        elif user.is_seller:
            return cls.model.objects.filter(
                deal__seller=user.seller_profile
            ).select_related('deal', 'deal__seller', 'deal__supplier', 'driver_profile')
        elif user.is_driver:
            return cls.model.objects.filter(
                driver_profile=user.driver_profile
            ).select_related('deal', 'deal__seller', 'deal__supplier', 'driver_profile')
        else:
            return cls.model.objects.none()
    
    @classmethod
    def can_user_access_delivery(cls, delivery: Delivery, user) -> bool:
        """Check if user can access this delivery"""
        if not delivery.deal:
            return False
        
        if user.is_supplier:
            return delivery.deal.supplier_id == user.supplier_profile.id
        elif user.is_seller:
            return delivery.deal.seller_id == user.seller_profile.id
        elif user.is_driver:
            return delivery.driver_profile_id == user.driver_profile.id
        return False
    
    @classmethod
    def _check_delivery_permission(cls, delivery: Delivery, user) -> None:
        """Check if user has permission to modify delivery (helper method)"""
        if not (user.is_supplier or user.is_driver):
            raise BusinessLogicError(
                'Unauthorized access', 
                status_code=status.HTTP_403_FORBIDDEN
            )
        if not cls.can_user_access_delivery(delivery, user):
            raise BusinessLogicError(
                'This delivery does not belong to you', 
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    @classmethod
    def update_delivery_status(cls, delivery: Delivery, user, new_status: str) -> Delivery:
        """Update delivery status with permission check"""
        cls._check_delivery_permission(delivery, user)
        
        delivery.status = new_status
        delivery.save()
        return delivery
    
    @classmethod
    def _clear_manual_driver_fields(cls, delivery: Delivery) -> None:
        """Clear manual driver fields when using system driver"""
        delivery.driver_name = None
        delivery.driver_phone = None
        delivery.driver_vehicle_type = None
        delivery.driver_vehicle_plate = None
        delivery.driver_license_number = None
    
    @classmethod
    def assign_driver_to_delivery(cls, delivery: Delivery, user, driver_id: int) -> Delivery:
        """Assign driver to delivery with permission check"""
        if not delivery.deal or delivery.deal.supplier_id != user.supplier_profile.id:
            raise BusinessLogicError(
                'This delivery does not belong to you', 
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        delivery.driver_profile = DriverProfile.objects.get(id=driver_id)
        cls._clear_manual_driver_fields(delivery)
        delivery.status = Delivery.Status.READY
        delivery.save()
        
        return delivery
    
    @classmethod
    def get_available_deliveries(cls, user) -> List[Delivery]:
        """Get deliveries available for driver acceptance"""
        deliveries = cls.model.objects.filter(
            driver_profile__isnull=True,
            driver_name__isnull=True,
            status=Delivery.Status.READY
        ).select_related('deal', 'deal__seller', 'deal__supplier')
        
        if user.is_driver and user.driver_profile.city:
            driver_city = user.driver_profile.city
            deliveries = deliveries.filter(
                Q(deal__seller__city__icontains=driver_city) | 
                Q(deal__supplier__city__icontains=driver_city)
            )
        
        return deliveries
    
    @classmethod
    def accept_delivery(cls, delivery: Delivery, user) -> Delivery:
        """Driver accepts an available delivery"""
        if not user.is_driver:
            raise BusinessLogicError(
                'Only drivers can accept deliveries', 
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        if delivery.driver_profile_id or delivery.driver_name:
            raise BusinessLogicError(
                'Delivery is already assigned', 
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if delivery.status != Delivery.Status.READY:
            raise BusinessLogicError(
                'Delivery is not ready for acceptance', 
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        delivery.driver_profile = user.driver_profile
        cls._clear_manual_driver_fields(delivery)
        delivery.status = Delivery.Status.PICKED_UP
        delivery.save()
        
        return delivery


# ==================== REQUEST TO DRIVER SERVICE ====================


class RequestToDriverService(BaseService):
    """Service for driver request-related business logic"""
    model = RequestToDriver
    
    @classmethod
    def get_user_requests(cls, user) -> List[RequestToDriver]:
        """Get requests filtered by user's role"""
        if user.is_driver:
            return cls.model.objects.filter(
                driver=user.driver_profile,
                deal__delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER
            ).select_related('deal', 'driver')
        elif user.is_supplier:
            return cls.model.objects.filter(
                deal__supplier=user.supplier_profile,
                deal__delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER
            ).select_related('deal', 'driver')
        elif user.is_seller:
            return cls.model.objects.filter(
                deal__seller=user.seller_profile,
                deal__delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER
            ).select_related('deal', 'driver')
        else:
            return cls.model.objects.none()
    
    @classmethod
    def propose_price(cls, driver_request: RequestToDriver, user, proposed_price: float) -> RequestToDriver:
        """Driver proposes a price (counter offer)"""
        if not user.is_driver or driver_request.driver != user.driver_profile:
            raise BusinessLogicError(
                'Only the requested driver can propose a price',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        if driver_request.status not in [
            RequestToDriver.Status.PENDING, 
            RequestToDriver.Status.COUNTER_OFFERED
        ]:
            raise BusinessLogicError(
                'Can only propose price for pending or counter-offered requests',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        driver_request.driver_proposed_price = proposed_price
        driver_request.status = RequestToDriver.Status.DRIVER_PROPOSED
        driver_request.save()
        
        return driver_request
    
    @classmethod
    def approve_request(cls, driver_request: RequestToDriver, user, final_price: Optional[float] = None) -> RequestToDriver:
        """Approve driver request"""
        driver_request.refresh_from_db()
        
        if not driver_request.can_approve(user):
            raise BusinessLogicError(
                'You are not authorized to approve this request',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        if driver_request.status not in [
            RequestToDriver.Status.PENDING, 
            RequestToDriver.Status.DRIVER_PROPOSED
        ]:
            raise BusinessLogicError(
                'Can only approve pending or driver-proposed requests',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if user.is_supplier:
            driver_request.supplier_approved = True
        elif user.is_seller:
            driver_request.seller_approved = True
        elif user.is_driver:
            driver_request.driver_approved = True
        else:
            raise BusinessLogicError(
                'Invalid user role for approval',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        driver_request.save()
        
        if driver_request.is_fully_approved():
            if not final_price:
                final_price = driver_request.driver_proposed_price or driver_request.requested_price
            driver_request.accept(final_price)
        
        return driver_request
    
    @classmethod
    def _can_user_reject_request(cls, driver_request: RequestToDriver, user) -> bool:
        """Check if user can reject this request"""
        if user.is_driver:
            return driver_request.driver_id == user.driver_profile.id
        elif user.is_supplier:
            return driver_request.deal.supplier_id == user.supplier_profile.id
        elif user.is_seller:
            return driver_request.deal.seller_id == user.seller_profile.id
        return False
    
    @classmethod
    def reject_request(cls, driver_request: RequestToDriver, user) -> RequestToDriver:
        """Reject driver request"""
        if not cls._can_user_reject_request(driver_request, user):
            raise BusinessLogicError(
                'You are not authorized to reject this request',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        driver_request.status = RequestToDriver.Status.REJECTED
        driver_request.save()
        
        return driver_request
    
    @classmethod
    def get_pending_approvals(cls, driver_request: RequestToDriver) -> List[str]:
        """Get list of parties that still need to approve"""
        pending = []
        if not driver_request.supplier_approved:
            pending.append('supplier')
        if not driver_request.seller_approved:
            pending.append('seller')
        if not driver_request.driver_approved:
            pending.append('driver')
        return pending


