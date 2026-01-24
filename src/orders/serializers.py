from rest_framework import serializers
from .models import Deal, DealItem, Delivery, DeliveryItem
from src.users.models import SupplierProfile, DriverProfile, SellerProfile
from src.users.serializers import SupplierProfileSerializer, SellerProfileSerializer, DriverProfileSerializer
from src.products.models import Product


# ==================== DEAL SERIALIZERS ====================

class DealItemSerializer(serializers.ModelSerializer):
    """Deal Item Serializer"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = DealItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['id', 'unit_price']


class DealSerializer(serializers.ModelSerializer):
    """Deal Serializer"""
    items = DealItemSerializer(many=True, read_only=True)
    seller_name = serializers.CharField(source='seller.business_name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    driver_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_amount = serializers.SerializerMethodField()
    seller_detail = SellerProfileSerializer(source='seller', read_only=True)
    supplier_detail = SupplierProfileSerializer(source='supplier', read_only=True)
    driver_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = Deal
        fields = [
            'id', 'seller', 'seller_name', 'seller_detail',
            'supplier', 'supplier_name', 'supplier_detail',
            'driver', 'driver_name', 'driver_detail',
            'status', 'status_display',
            'delivery_address', 'delivery_note', 'cost_split',
            'items', 'total_amount', 'delivery', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'seller', 'supplier', 'delivery', 'created_at', 'updated_at']
    
    def get_driver_name(self, obj):
        if obj.driver:
            return obj.driver.user.username
        return None
    
    def get_driver_detail(self, obj):
        if obj.driver:
            return DriverProfileSerializer(obj.driver).data
        return None
    
    def get_total_amount(self, obj):
        return obj.calculate_total()


class DealCreateSerializer(serializers.Serializer):
    """Deal Creation Serializer - For sellers or suppliers"""
    supplier_id = serializers.IntegerField(required=False)
    seller_id = serializers.IntegerField(required=False)
    delivery_address = serializers.CharField()
    delivery_note = serializers.CharField(required=False, allow_blank=True)
    driver_id = serializers.IntegerField(required=False, allow_null=True)
    cost_split = serializers.BooleanField(default=False)
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        ),
        min_length=1
    )
    
    def validate(self, attrs):
        supplier_id = attrs.get('supplier_id')
        seller_id = attrs.get('seller_id')
        user = self.context['request'].user
        
        # If user is seller, supplier_id is required
        if user.is_seller:
            if not supplier_id:
                raise serializers.ValidationError({"supplier_id": "Supplier ID is required for sellers."})
            attrs['seller_id'] = user.seller_profile.id
        # If user is supplier, seller_id is required
        elif user.is_supplier:
            if not seller_id:
                raise serializers.ValidationError({"seller_id": "Seller ID is required for suppliers."})
            attrs['supplier_id'] = user.supplier_profile.id
        else:
            raise serializers.ValidationError("Only sellers or suppliers can create deals.")
        
        return attrs
    
    def validate_supplier_id(self, value):
        if value:
            try:
                SupplierProfile.objects.get(id=value, is_active=True)
            except SupplierProfile.DoesNotExist:
                raise serializers.ValidationError("Supplier not found.")
        return value
    
    def validate_seller_id(self, value):
        if value:
            try:
                SellerProfile.objects.get(id=value, is_active=True)
            except SellerProfile.DoesNotExist:
                raise serializers.ValidationError("Seller not found.")
        return value
    
    def validate_driver_id(self, value):
        if value:
            try:
                DriverProfile.objects.get(id=value, is_active=True)
            except DriverProfile.DoesNotExist:
                raise serializers.ValidationError("Driver not found.")
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
        
        if user.is_seller:
            seller_profile = user.seller_profile
            supplier = SupplierProfile.objects.get(id=validated_data['supplier_id'])
        else:  # user.is_supplier
            supplier = user.supplier_profile
            seller_profile = SellerProfile.objects.get(id=validated_data['seller_id'])
        
        # Create deal
        driver_id = validated_data.get('driver_id')
        deal = Deal.objects.create(
            seller=seller_profile,
            supplier=supplier,
            delivery_address=validated_data['delivery_address'],
            delivery_note=validated_data.get('delivery_note', ''),
            driver_id=driver_id if driver_id else None,
            cost_split=validated_data.get('cost_split', False),
            status=Deal.Status.DEALING if driver_id else Deal.Status.LOOKING_FOR_DRIVER
        )
        
        # Create deal items
        for item_data in validated_data['items']:
            product = Product.objects.get(id=item_data['product_id'], supplier=supplier)
            DealItem.objects.create(
                deal=deal,
                product=product,
                quantity=item_data['quantity'],
                unit_price=product.price
            )
        
        return deal


class DealStatusUpdateSerializer(serializers.Serializer):
    """Deal Status Update Serializer"""
    status = serializers.ChoiceField(choices=Deal.Status.choices)


class DealDriverAssignSerializer(serializers.Serializer):
    """Deal Driver Assignment Serializer - For supplier or seller to assign their own driver"""
    driver_id = serializers.IntegerField()
    
    def validate_driver_id(self, value):
        try:
            DriverProfile.objects.get(id=value, is_active=True)
        except DriverProfile.DoesNotExist:
            raise serializers.ValidationError("Driver not found.")
        return value


class DealDriverRequestSerializer(serializers.Serializer):
    """Deal Driver Request Serializer - For requesting drivers when status is LOOKING_FOR_DRIVER"""
    driver_id = serializers.IntegerField()
    
    def validate_driver_id(self, value):
        try:
            DriverProfile.objects.get(id=value, is_active=True, is_available=True)
        except DriverProfile.DoesNotExist:
            raise serializers.ValidationError("Available driver not found.")
        return value


class DealCompleteSerializer(serializers.Serializer):
    """Deal Completion Serializer - Creates Delivery from Deal when status is DONE"""
    pass


# ==================== DELIVERY SERIALIZERS ====================

class DeliveryItemSerializer(serializers.ModelSerializer):
    """Delivery Item Serializer"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = DeliveryItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['id', 'unit_price']


class DeliverySerializer(serializers.ModelSerializer):
    """Delivery Serializer"""
    items = DeliveryItemSerializer(many=True, read_only=True)
    seller_name = serializers.CharField(source='seller.business_name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    driver_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    seller_detail = SellerProfileSerializer(source='seller', read_only=True)
    supplier_detail = SupplierProfileSerializer(source='supplier', read_only=True)
    driver_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = Delivery
        fields = [
            'id', 'seller', 'seller_name', 'seller_detail',
            'supplier', 'supplier_name', 'supplier_detail',
            'driver', 'driver_name', 'driver_detail',
            'status', 'status_display',
            'total_amount', 'delivery_address', 'delivery_note',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'seller', 'total_amount', 'created_at', 'updated_at']
    
    def get_driver_name(self, obj):
        if obj.driver:
            return obj.driver.user.username
        return None
    
    def get_driver_detail(self, obj):
        if obj.driver:
            return DriverProfileSerializer(obj.driver).data
        return None


class DeliveryCreateSerializer(serializers.Serializer):
    """Delivery Creation Serializer - For sellers"""
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
            raise PermissionDenied('Only sellers can create deliveries')
        seller_profile = user.seller_profile
        supplier = SupplierProfile.objects.get(id=validated_data['supplier_id'])
        
        # Create delivery
        delivery = Delivery.objects.create(
            seller=seller_profile,
            supplier=supplier,
            delivery_address=validated_data['delivery_address'],
            delivery_note=validated_data.get('delivery_note', '')
        )
        
        # Create delivery items
        for item_data in validated_data['items']:
            product = Product.objects.get(id=item_data['product_id'], supplier=supplier)
            DeliveryItem.objects.create(
                delivery=delivery,
                product=product,
                quantity=item_data['quantity'],
                unit_price=product.price
            )
        
        # Calculate total amount
        delivery.calculate_total()
        
        return delivery


class DeliveryStatusUpdateSerializer(serializers.Serializer):
    """Delivery Status Update Serializer"""
    status = serializers.ChoiceField(choices=Delivery.Status.choices)


class DeliveryAssignDriverSerializer(serializers.Serializer):
    """Delivery Driver Assignment Serializer"""
    driver_id = serializers.IntegerField()
    
    def validate_driver_id(self, value):
        try:
            DriverProfile.objects.get(id=value, is_active=True, is_available=True)
        except DriverProfile.DoesNotExist:
            raise serializers.ValidationError("Available driver not found.")
        return value
