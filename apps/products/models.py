from django.db import models
from apps.core.models import TimeStampedModel
from apps.users.models import SupplierProfile


class Category(TimeStampedModel):
    """Product Category Model"""
    name = models.CharField(max_length=100, verbose_name='Category name')
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True, 
        related_name='children',
        verbose_name='Parent category'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    """Product Model - Created by supplier"""
    
    class Unit(models.TextChoices):
        KG = 'KG', 'Kilogram'
        GRAM = 'GRAM', 'Gram'
        PIECE = 'PIECE', 'Piece'
        LITER = 'LITER', 'Liter'
        BOX = 'BOX', 'Box'
        PACKAGE = 'PACKAGE', 'Package'
    
    supplier = models.ForeignKey(
        SupplierProfile, 
        on_delete=models.CASCADE, 
        related_name='products',
        verbose_name='Supplier'
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='products',
        verbose_name='Category'
    )
    name = models.CharField(max_length=255, verbose_name='Product name')
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Price')
    unit = models.CharField(max_length=20, choices=Unit.choices, default=Unit.KG, verbose_name='Unit')
    min_order_quantity = models.PositiveIntegerField(default=1, verbose_name='Min order quantity')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Product image')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.supplier.company_name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
