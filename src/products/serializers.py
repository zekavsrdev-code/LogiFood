from rest_framework import serializers
from .models import Category, Product
from src.users.models import SupplierProfile


class CategorySerializer(serializers.ModelSerializer):
    """Category Serializer"""
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent', 'children', 'is_active']
        read_only_fields = ['id']
    
    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data if children.exists() else []


class ProductSerializer(serializers.ModelSerializer):
    """Product Serializer"""
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'unit', 'unit_display',
            'stock', 'min_order_quantity', 'image', 'is_active',
            'supplier', 'supplier_name', 'category', 'category_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'supplier', 'created_at', 'updated_at']


class ProductCreateSerializer(serializers.ModelSerializer):
    """Product Creation Serializer - For suppliers"""
    image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'unit', 'stock', 
            'min_order_quantity', 'image', 'category', 'is_active'
        ]
    
    def create(self, validated_data):
        # Get supplier from request
        user = self.context['request'].user
        supplier_profile = user.supplier_profile
        validated_data['supplier'] = supplier_profile
        return super().create(validated_data)
