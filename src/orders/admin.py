from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'seller', 'supplier', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['seller__business_name', 'supplier__company_name']
    readonly_fields = ['total_amount', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    ordering = ['-created_at']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity', 'unit_price', 'total_price']
    list_filter = ['order__status']
    search_fields = ['order__id', 'product__name']
    readonly_fields = ['total_price', 'created_at', 'updated_at']
