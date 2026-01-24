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
        verbose_name='Driver'
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DEALING,
        verbose_name='Status'
    )
    delivery_address = models.TextField(verbose_name='Delivery Address')
    delivery_note = models.TextField(blank=True, null=True, verbose_name='Delivery Note')
    cost_split = models.BooleanField(
        default=False,
        verbose_name='Cost Split',
        help_text='If True, both supplier and seller can request drivers (costs split)'
    )
    delivery = models.OneToOneField(
        'Delivery',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deal',
        verbose_name='Delivery'
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
    
    seller = models.ForeignKey(
        SellerProfile, 
        on_delete=models.CASCADE, 
        related_name='deliveries',
        verbose_name='Seller'
    )
    supplier = models.ForeignKey(
        SupplierProfile, 
        on_delete=models.CASCADE, 
        related_name='received_deliveries',
        verbose_name='Supplier'
    )
    driver = models.ForeignKey(
        'users.DriverProfile', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='deliveries',
        verbose_name='Driver'
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
        return f"Delivery #{self.id} - {self.seller.business_name}"
    
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
