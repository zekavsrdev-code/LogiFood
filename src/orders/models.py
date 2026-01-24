from django.db import models
from apps.core.models import TimeStampedModel
from src.users.models import SupplierProfile, SellerProfile
from src.products.models import Product


class Order(TimeStampedModel):
    """Order Model - Created by seller"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
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
        related_name='orders',
        verbose_name='Seller'
    )
    supplier = models.ForeignKey(
        SupplierProfile, 
        on_delete=models.CASCADE, 
        related_name='received_orders',
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
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name='Status')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total Amount')
    delivery_address = models.TextField(verbose_name='Delivery Address')
    delivery_note = models.TextField(blank=True, null=True, verbose_name='Delivery Note')
    
    class Meta:
        db_table = 'orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.seller.business_name}"
    
    def calculate_total(self):
        """Calculate order total amount"""
        total = sum(item.total_price for item in self.items.all())
        self.total_amount = total
        self.save()
        return total


class OrderItem(TimeStampedModel):
    """Order Item Model"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(verbose_name='Quantity')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Unit Price')
    
    class Meta:
        db_table = 'order_items'
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price
    
    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)
