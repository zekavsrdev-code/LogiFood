from django.db import models
from apps.core.models import TimeStampedModel
from src.users.models import SupplierProfile, SellerProfile
from src.products.models import Product


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
    driver = models.ForeignKey(
        'users.DriverProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals',
        verbose_name='Driver',
        help_text='System driver assigned to this deal (only used when delivery_handler is SYSTEM_DRIVER)'
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
    cost_split = models.BooleanField(
        default=False,
        verbose_name='Cost Split',
        help_text='If True, both supplier and seller can request drivers (costs split)'
    )
    delivery_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Delivery Count',
        help_text='Number of deliveries created from this deal'
    )
    
    class Meta:
        db_table = 'deals'
        verbose_name = 'Deal'
        verbose_name_plural = 'Deals'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Deal #{self.id} - {self.seller.business_name} & {self.supplier.company_name}"
    
    def calculate_total(self):
        """Calculate total amount from deal items"""
        total = sum(item.total_price for item in self.items.all())
        return total
    
    def increment_delivery_count(self):
        """Increment delivery count when a delivery is created from this deal"""
        self.delivery_count += 1
        self.save(update_fields=['delivery_count'])


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
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price
    
    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)


class Delivery(TimeStampedModel):
    """Delivery Model - Created from Deal, tracks delivery progress"""
    
    class Status(models.TextChoices):
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
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED, verbose_name='Status')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total Amount')
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
        
        # Update deal delivery count
        if self.deal:
            if is_new or old_deal_id != self.deal_id:
                self.deal.increment_delivery_count()
        elif old_deal_id:
            # Delivery was removed from deal, decrement count
            try:
                old_deal = Deal.objects.get(pk=old_deal_id)
                old_deal.delivery_count = max(0, old_deal.delivery_count - 1)
                old_deal.save(update_fields=['delivery_count'])
            except Deal.DoesNotExist:
                pass
    
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
    
    def calculate_total(self):
        """Calculate delivery total amount"""
        total = sum(item.total_price for item in self.items.all())
        self.total_amount = total
        self.save()
        return total


class DeliveryItem(TimeStampedModel):
    """Delivery Item Model"""
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='delivery_items')
    quantity = models.PositiveIntegerField(verbose_name='Quantity')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Unit Price')
    
    class Meta:
        db_table = 'delivery_items'
        verbose_name = 'Delivery Item'
        verbose_name_plural = 'Delivery Items'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price
    
    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)
