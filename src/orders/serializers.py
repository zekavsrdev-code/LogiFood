from rest_framework import serializers
from .models import Order, OrderItem
from src.users.models import SupplierProfile, DriverProfile
from src.products.models import Product


class OrderItemSerializer(serializers.ModelSerializer):
    """Order Item Serializer"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['id', 'unit_price']


class OrderSerializer(serializers.ModelSerializer):
    """Order Serializer"""
    items = OrderItemSerializer(many=True, read_only=True)
    seller_name = serializers.CharField(source='seller.business_name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    driver_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'seller', 'seller_name', 'supplier', 'supplier_name',
            'driver', 'driver_name', 'status', 'status_display',
            'total_amount', 'delivery_address', 'delivery_note',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'seller', 'total_amount', 'created_at', 'updated_at']
    
    def get_driver_name(self, obj):
        if obj.driver:
            return obj.driver.user.username
        return None


class OrderCreateSerializer(serializers.Serializer):
    """Order Creation Serializer - For sellers"""
    supplier_id = serializers.IntegerField()
    delivery_address = serializers.CharField()
    delivery_note = serializers.CharField(required=False, allow_blank=True)
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        ),
        min_length=1
    )
    
    def validate_supplier_id(self, value):
        try:
            SupplierProfile.objects.get(id=value, is_active=True)
        except SupplierProfile.DoesNotExist:
            raise serializers.ValidationError("Supplier not found.")
        return value
    
    def validate_items(self, value):
        for item in value:
            if 'product_id' not in item or 'quantity' not in item:
                raise serializers.ValidationError("Each item must contain 'product_id' and 'quantity'.")
            if item['quantity'] < 1:
                raise serializers.ValidationError("Quantity must be at least 1.")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        if not user.is_seller:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only sellers can create orders')
        seller_profile = user.seller_profile
        supplier = SupplierProfile.objects.get(id=validated_data['supplier_id'])
        
        # Create order
        order = Order.objects.create(
            seller=seller_profile,
            supplier=supplier,
            delivery_address=validated_data['delivery_address'],
            delivery_note=validated_data.get('delivery_note', '')
        )
        
        # Create order items
        for item_data in validated_data['items']:
            product = Product.objects.get(id=item_data['product_id'], supplier=supplier)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                unit_price=product.price
            )
        
        # Calculate total amount
        order.calculate_total()
        
        return order


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Order Status Update Serializer"""
    status = serializers.ChoiceField(choices=Order.Status.choices)


class OrderAssignDriverSerializer(serializers.Serializer):
    """Order Driver Assignment Serializer"""
    driver_id = serializers.IntegerField()
    
    def validate_driver_id(self, value):
        try:
            DriverProfile.objects.get(id=value, is_active=True, is_available=True)
        except DriverProfile.DoesNotExist:
            raise serializers.ValidationError("Available driver not found.")
        return value
