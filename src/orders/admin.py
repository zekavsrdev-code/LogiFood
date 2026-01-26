from django.contrib import admin
from .models import Deal, DealItem, Delivery, DeliveryItem, RequestToDriver


class DealItemInline(admin.TabularInline):
    model = DealItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ['id', 'seller', 'supplier', 'driver', 'delivery_handler', 'delivery_cost_split', 'status', 'delivery_count', 'get_actual_delivery_count', 'created_at']
    list_filter = ['status', 'delivery_handler', 'created_at']
    search_fields = ['seller__business_name', 'supplier__company_name']
    inlines = [DealItemInline]
    ordering = ['-created_at']
    
    def get_actual_delivery_count(self, obj):
        """Get actual number of deliveries created"""
        return obj.get_actual_delivery_count()
    get_actual_delivery_count.short_description = 'Actual Deliveries'


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
    list_display = ['id', 'deal', 'get_seller', 'get_supplier', 'get_supplier_share', 'get_is_3rd_party', 'driver_profile', 'driver_name', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['deal__seller__business_name', 'deal__supplier__company_name', 'seller__business_name', 'supplier__company_name', 'driver_name']
    readonly_fields = ['total_amount', 'created_at', 'updated_at']
    inlines = [DeliveryItemInline]
    ordering = ['-created_at']
    
    def get_seller(self, obj):
        seller = obj.seller_profile
        return seller.business_name if seller else None
    get_seller.short_description = 'Seller'
    
    def get_supplier(self, obj):
        supplier = obj.supplier_profile
        return supplier.company_name if supplier else None
    get_supplier.short_description = 'Supplier'
    
    def get_supplier_share(self, obj):
        return f"{obj.supplier_share}%"
    get_supplier_share.short_description = 'Supplier Share'
    
    def get_is_3rd_party(self, obj):
        return obj.is_3rd_party_delivery
    get_is_3rd_party.boolean = True
    get_is_3rd_party.short_description = '3rd Party Delivery'


@admin.register(DeliveryItem)
class DeliveryItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'delivery', 'product', 'quantity', 'unit_price', 'total_price']
    list_filter = ['delivery__status']
    search_fields = ['delivery__id', 'product__name']
    readonly_fields = ['total_price', 'created_at', 'updated_at']


@admin.register(RequestToDriver)
class RequestToDriverAdmin(admin.ModelAdmin):
    list_display = ['id', 'deal', 'driver', 'requested_price', 'driver_proposed_price', 'final_price', 'status', 'supplier_approved', 'seller_approved', 'driver_approved', 'created_by', 'created_at']
    list_filter = ['status', 'supplier_approved', 'seller_approved', 'driver_approved', 'created_at']
    search_fields = ['deal__id', 'driver__user__username', 'created_by__username']
    ordering = ['-created_at']
