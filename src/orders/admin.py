from django.contrib import admin
from .models import Deal, DealItem, Delivery, DeliveryItem


class DealItemInline(admin.TabularInline):
    model = DealItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ['id', 'seller', 'supplier', 'driver', 'status', 'cost_split', 'delivery', 'created_at']
    list_filter = ['status', 'cost_split', 'created_at']
    search_fields = ['seller__business_name', 'supplier__company_name']
    inlines = [DealItemInline]
    ordering = ['-created_at']


@admin.register(DealItem)
class DealItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'deal', 'product', 'quantity', 'unit_price', 'total_price']
    list_filter = ['deal__status']
    search_fields = ['deal__id', 'product__name']
    readonly_fields = ['total_price', 'created_at', 'updated_at']


class DeliveryItemInline(admin.TabularInline):
    model = DeliveryItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['id', 'seller', 'supplier', 'driver', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['seller__business_name', 'supplier__company_name']
    readonly_fields = ['total_amount', 'created_at', 'updated_at']
    inlines = [DeliveryItemInline]
    ordering = ['-created_at']


@admin.register(DeliveryItem)
class DeliveryItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'delivery', 'product', 'quantity', 'unit_price', 'total_price']
    list_filter = ['delivery__status']
    search_fields = ['delivery__id', 'product__name']
    readonly_fields = ['total_price', 'created_at', 'updated_at']
