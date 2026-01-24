from django.db import models
from apps.core.models import TimeStampedModel
from src.users.models import SupplierProfile


class Category(TimeStampedModel):
    """Product Category Model"""
    name = models.CharField(max_length=100, verbose_name='Kategori Adı')
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True, verbose_name='Açıklama')
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True, 
        related_name='children',
        verbose_name='Üst Kategori'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Kategori'
        verbose_name_plural = 'Kategoriler'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    """Product Model - Created by supplier"""
    
    class Unit(models.TextChoices):
        KG = 'KG', 'Kilogram'
        GRAM = 'GRAM', 'Gram'
        PIECE = 'PIECE', 'Adet'
        LITER = 'LITER', 'Litre'
        BOX = 'BOX', 'Koli'
        PACKAGE = 'PACKAGE', 'Paket'
    
    supplier = models.ForeignKey(
        SupplierProfile, 
        on_delete=models.CASCADE, 
        related_name='products',
        verbose_name='Tedarikçi'
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='products',
        verbose_name='Kategori'
    )
    name = models.CharField(max_length=255, verbose_name='Ürün Adı')
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True, null=True, verbose_name='Açıklama')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Fiyat')
    unit = models.CharField(max_length=20, choices=Unit.choices, default=Unit.KG, verbose_name='Birim')
    stock = models.PositiveIntegerField(default=0, verbose_name='Stok')
    min_order_quantity = models.PositiveIntegerField(default=1, verbose_name='Minimum Sipariş Miktarı')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Ürün Resmi')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Ürün'
        verbose_name_plural = 'Ürünler'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.supplier.company_name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
