from django.db import models
from apps.core.models import TimeStampedModel
from apps.users.models import SupplierProfile, SellerProfile
from apps.products.models import Product


class Deal(TimeStampedModel):
    """Deal Model - Created before Delivery, manages driver assignment and negotiation"""
    
    class Status(models.TextChoices):
        DEALING = 'DEALING', 'Dealing'
        LOOKING_FOR_DRIVER = 'LOOKING_FOR_DRIVER', 'Looking for Driver'
        DONE = 'DONE', 'Done'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    class DeliveryHandler(models.TextChoices):
        SYSTEM_DRIVER = 'SYSTEM_DRIVER', 'System Driver'
        SUPPLIER = 'SUPPLIER', 'Supplier (3rd Party)'
        SELLER = 'SELLER', 'Seller (3rd Party)'
    
    seller = models.ForeignKey(
        SellerProfile,
        on_delete=models.CASCADE,
        related_name='deals',
        verbose_name='Seller'
    )
    supplier = models.ForeignKey(
        SupplierProfile,
        on_delete=models.CASCADE,
        related_name='deals',
        verbose_name='Supplier'
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DEALING,
        verbose_name='Status'
    )
    delivery_handler = models.CharField(
        max_length=20,
        choices=DeliveryHandler.choices,
        default=DeliveryHandler.SYSTEM_DRIVER,
        verbose_name='Delivery Handler',
        help_text='Who will handle the delivery: System driver, Supplier (3rd party), or Seller (3rd party)'
    )
    # Delivery cost split - only used when delivery_handler is SYSTEM_DRIVER
    # Indicates how delivery cost is split between supplier and seller (0-100)
    # 0 = seller pays all, 100 = supplier pays all, 50 = split equally
    delivery_cost_split = models.PositiveIntegerField(
        default=50,
        verbose_name='Delivery Cost Split (%)',
        help_text='Percentage of delivery cost paid by supplier when using system driver (0-100). 0=seller pays all, 100=supplier pays all, 50=split equally. Only used when delivery_handler is SYSTEM_DRIVER.'
    )
    delivery_count = models.PositiveIntegerField(
        default=1,
        verbose_name='Delivery Count',
        help_text='Number of deliveries planned for this deal. For example, 200kg of onions can be delivered in 3 separate deliveries. This is the planned count, not the actual count.'
    )
    # Both parties must approve before transitioning to LOOKING_FOR_DRIVER or DONE.
    # When seller/supplier changes deal (delivery_handler, delivery_cost_split, delivery_count) or any DealItem, the other party’s approval is cleared.
    seller_approved = models.BooleanField(
        default=False,
        verbose_name='Seller Approved',
        help_text='Seller has approved the current deal/items. Cleared when supplier edits deal or items.'
    )
    supplier_approved = models.BooleanField(
        default=False,
        verbose_name='Supplier Approved',
        help_text='Supplier has approved the current deal/items. Cleared when seller edits deal or items.'
    )

    class Meta:
        db_table = 'deals'
        verbose_name = 'Deal'
        verbose_name_plural = 'Deals'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Deal #{self.id} - {self.seller.business_name} & {self.supplier.company_name}"
    
    def calculate_total(self):
        """Price 1: total goods value from deal items."""
        return sum(item.total_price for item in self.items.all())

    def get_delivery_fee_split(self):
        """
        Price 2: delivery fee (RequestToDriver.final_price) split by delivery_cost_split.
        Returns (delivery_fee, supplier_amount, seller_amount) or (None, None, None).
        delivery_cost_split = % paid by supplier (0=seller all, 100=supplier all, 50=split).
        """
        if self.delivery_handler != self.DeliveryHandler.SYSTEM_DRIVER:
            return None, None, None
        accepted = self.driver_requests.filter(status='ACCEPTED').first()
        if not accepted or not accepted.final_price:
            return None, None, None
        from decimal import Decimal
        fee = accepted.final_price
        pct = Decimal(self.delivery_cost_split) / 100
        supplier_amount = (fee * pct).quantize(Decimal('0.01'))
        seller_amount = (fee * (1 - pct)).quantize(Decimal('0.01'))
        return fee, supplier_amount, seller_amount

    def get_actual_delivery_count(self):
        """Get the actual number of deliveries created from this deal"""
        return self.deliveries.count()
    
    def can_create_more_deliveries(self):
        """Check if more deliveries can be created for this deal"""
        return self.get_actual_delivery_count() < self.delivery_count

    @property
    def both_parties_approved(self):
        """True if both seller and supplier have approved; required for LOOKING_FOR_DRIVER / DONE."""
        return bool(self.seller_approved and self.supplier_approved)


class DealItem(TimeStampedModel):
    """Deal Item Model"""
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='deal_items')
    quantity = models.PositiveIntegerField(verbose_name='Quantity')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Unit Price')
    
    class Meta:
        db_table = 'deal_items'
        verbose_name = 'Deal Item'
        verbose_name_plural = 'Deal Items'
        ordering = ['id']  # Ensure consistent ordering for pagination
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price
    
    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)


class RequestToDriver(TimeStampedModel):
    """Request to Driver Model - For LOOKING_FOR_DRIVER status deals with SYSTEM_DRIVER handler"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'  # Request sent, waiting for driver response
        DRIVER_PROPOSED = 'DRIVER_PROPOSED', 'Driver Proposed'  # Driver proposed a price
        ACCEPTED = 'ACCEPTED', 'Accepted'  # Price accepted, driver assigned to deal
        REJECTED = 'REJECTED', 'Rejected'  # Request rejected by driver or supplier/seller
        COUNTER_OFFERED = 'COUNTER_OFFERED', 'Counter Offered'  # Counter offer made
    
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='driver_requests',
        verbose_name='Deal',
        help_text='The deal this request is for. Only valid for SYSTEM_DRIVER delivery_handler.'
    )
    driver = models.ForeignKey(
        'users.DriverProfile',
        on_delete=models.CASCADE,
        related_name='driver_requests',
        verbose_name='Driver',
        help_text='Driver who received this request'
    )
    requested_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Requested Price',
        help_text='Price offered by supplier/seller to driver'
    )
    driver_proposed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Driver Proposed Price',
        help_text='Price proposed by driver (counter offer)'
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Final Price',
        help_text='Final agreed price when request is accepted'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Status'
    )
    # Approval flags - all 3 parties (supplier, seller, driver) must approve
    supplier_approved = models.BooleanField(
        default=False,
        verbose_name='Supplier Approved',
        help_text='Supplier has approved the price'
    )
    seller_approved = models.BooleanField(
        default=False,
        verbose_name='Seller Approved',
        help_text='Seller has approved the price'
    )
    driver_approved = models.BooleanField(
        default=False,
        verbose_name='Driver Approved',
        help_text='Driver has approved the price'
    )
    
    class Meta:
        db_table = 'requests_to_driver'
        verbose_name = 'Request to Driver'
        verbose_name_plural = 'Requests to Driver'
        ordering = ['-created_at']
        unique_together = [['deal', 'driver']]  # One request per driver per deal
    
    def __str__(self):
        return f"Request #{self.id} - Deal #{self.deal.id} to Driver {self.driver.user.username}"
    
    def can_approve(self, user):
        """Check if user can approve this request - All 3 parties (supplier, seller, driver) can approve"""
        # Get fresh deal from database to ensure delivery_handler and supplier/seller are current
        deal = Deal.objects.get(pk=self.deal_id)
        if deal.delivery_handler != Deal.DeliveryHandler.SYSTEM_DRIVER:
            return False
        
        # Driver can always approve (if they are the requested driver)
        # Use ID comparison to avoid issues with cached objects
        if user.is_driver:
            return self.driver_id == user.driver_profile.id if user.driver_profile else False
        
        # Supplier can approve if they are part of the deal
        # Use ID comparison to avoid issues with cached objects
        if user.is_supplier:
            supplier_profile_id = user.supplier_profile.id if user.supplier_profile else None
            return deal.supplier_id == supplier_profile_id if supplier_profile_id else False
        
        # Seller can approve if they are part of the deal
        # Use ID comparison to avoid issues with cached objects
        if user.is_seller:
            seller_profile_id = user.seller_profile.id if user.seller_profile else None
            return deal.seller_id == seller_profile_id if seller_profile_id else False
        
        return False
    
    def is_fully_approved(self):
        """Check if request is fully approved - All 3 parties (supplier, seller, driver) must approve"""
        # Get fresh deal from database to ensure delivery_handler is current
        # This avoids issues with cached deal relationships
        deal = Deal.objects.get(pk=self.deal_id)
        if deal.delivery_handler != Deal.DeliveryHandler.SYSTEM_DRIVER:
            return False
        
        # All 3 parties must approve: supplier, seller, and driver
        return self.supplier_approved and self.seller_approved and self.driver_approved
    
    def accept(self, final_price):
        """Accept the request"""
        if not self.is_fully_approved():
            raise ValueError("Request must be fully approved before acceptance")
        
        self.status = self.Status.ACCEPTED
        self.final_price = final_price
        self.save()
        
        # Update deal status to DEALING (driver info is now in RequestToDriver, not Deal)
        self.deal.status = Deal.Status.DEALING
        self.deal.save()
        
        return self


class Delivery(TimeStampedModel):
    """Delivery Model - Created from Deal, tracks delivery progress"""
    
    class Status(models.TextChoices):
        ESTIMATED = 'ESTIMATED', 'Estimated'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        PREPARING = 'PREPARING', 'Preparing'
        READY = 'READY', 'Ready'
        PICKED_UP = 'PICKED_UP', 'Picked Up'
        IN_TRANSIT = 'IN_TRANSIT', 'In Transit'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='deliveries',
        verbose_name='Deal',
        help_text='The deal this delivery was created from. Delivery is always linked to a deal.'
    )
    # Supplier share indicates percentage owned by supplier (0-100)
    # Remaining percentage (100 - supplier_share) belongs to seller
    supplier_share = models.PositiveIntegerField(
        default=100,
        verbose_name='Supplier Share (%)',
        help_text='Percentage of delivery owned by supplier (0-100). Remaining percentage belongs to seller.'
    )
    # Driver information - can be from system (DriverProfile) or external (3rd party manual entry)
    # If driver is handled by supplier or seller as 3rd party, driver_profile is null but manual fields are filled
    driver_profile = models.ForeignKey(
        'users.DriverProfile', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='deliveries',
        verbose_name='Driver Profile',
        help_text='System driver profile if driver is registered in system. If null, use manual driver fields for 3rd party drivers.'
    )
    # External/3rd party driver information (when driver_profile is null and supplier/seller handles delivery)
    driver_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Driver Name',
        help_text='Driver name for 3rd party drivers (when driver_profile is null)'
    )
    driver_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Driver Phone',
        help_text='Driver phone number'
    )
    driver_vehicle_type = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Driver Vehicle Type',
        help_text='Driver vehicle type'
    )
    driver_vehicle_plate = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Driver Vehicle Plate',
        help_text='Driver vehicle plate number'
    )
    driver_license_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Driver License Number',
        help_text='Driver license number'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ESTIMATED, verbose_name='Status')
    delivery_address = models.TextField(verbose_name='Delivery Address')
    delivery_note = models.TextField(blank=True, null=True, verbose_name='Delivery Note')
    
    class Meta:
        db_table = 'deliveries'
        verbose_name = 'Delivery'
        verbose_name_plural = 'Deliveries'
        ordering = ['-created_at']
    
    def __str__(self):
        seller_name = self.deal.seller.business_name
        return f"Delivery #{self.id} - {seller_name}"
    
    @property
    def seller_profile(self):
        """Get seller profile from deal"""
        return self.deal.seller
    
    @property
    def supplier_profile(self):
        """Get supplier profile from deal"""
        return self.deal.supplier
    
    @property
    def is_3rd_party_delivery(self):
        """Check if this delivery is handled by 3rd party (supplier or seller handles delivery, not system driver)"""
        # If driver_profile is null but driver_name is set, it's a 3rd party delivery
        # Or if both are null, supplier/seller handles it themselves
        return self.driver_profile is None
    
    def clean(self):
        """Validate delivery model"""
        from django.core.exceptions import ValidationError
        
        # Deal is always required
        if not hasattr(self, 'deal_id') or self.deal_id is None:
            raise ValidationError("Delivery must be linked to a deal.")
        
        # Validate supplier_share
        if self.supplier_share > 100:
            raise ValidationError("Supplier share cannot exceed 100%.")
        
        # Delivery address is required
        if not self.delivery_address:
            raise ValidationError("Delivery address is required.")
        
        # If driver_profile is set, manual driver fields should be empty (use system driver)
        if self.driver_profile:
            if self.driver_name or self.driver_phone or self.driver_vehicle_type or self.driver_vehicle_plate or self.driver_license_number:
                raise ValidationError("Cannot use both system driver (driver_profile) and manual driver fields. Use one or the other.")
    
    def save(self, *args, **kwargs):
        """Override save to validate and update deal delivery count"""
        self.clean()
        is_new = self.pk is None
        old_deal_id = None
        
        if not is_new:
            old_delivery = Delivery.objects.get(pk=self.pk)
            old_deal_id = old_delivery.deal_id if old_delivery.deal else None
        
        super().save(*args, **kwargs)
        
        # Note: delivery_count is the planned count, not the actual count
        # Actual count is tracked via deal.deliveries.count()
        # No need to increment/decrement delivery_count anymore
    
    def get_driver_info(self):
        """Get driver information - from system or manual entry"""
        if self.driver_profile:
            return {
                'name': self.driver_profile.user.get_full_name() or self.driver_profile.user.username,
                'phone': self.driver_profile.user.phone_number,
                'vehicle_plate': self.driver_profile.vehicle_plate,
                'vehicle_type': self.driver_profile.get_vehicle_type_display(),
                'license_number': self.driver_profile.license_number,
                'is_system_driver': True
            }
        elif self.driver_name:
            return {
                'name': self.driver_name,
                'phone': self.driver_phone,
                'vehicle_plate': self.driver_vehicle_plate,
                'vehicle_type': self.driver_vehicle_type,
                'license_number': self.driver_license_number,
                'is_system_driver': False
            }
        return None


class DeliveryItem(TimeStampedModel):
    """Delivery line item - links to DealItem for price (no price stored on Delivery/DeliveryItem)."""
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='items')
    deal_item = models.ForeignKey(
        'DealItem',
        on_delete=models.CASCADE,
        related_name='delivery_items',
        verbose_name='Deal Item',
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField(verbose_name='Quantity')

    class Meta:
        db_table = 'delivery_items'
        verbose_name = 'Delivery Item'
        verbose_name_plural = 'Delivery Items'

    def __str__(self):
        if self.deal_item:
            return f"{self.deal_item.product.name} x {self.quantity}"
        return f"DeliveryItem #{self.pk}"

    @property
    def product(self):
        return self.deal_item.product if self.deal_item else None

    @property
    def unit_price(self):
        return self.deal_item.unit_price if self.deal_item else None

    @property
    def total_price(self):
        if self.deal_item and self.unit_price is not None:
            return self.quantity * self.unit_price
        return None
