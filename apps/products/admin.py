from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'supplier', 'category', 'price', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'unit', 'created_at']
    search_fields = ['name', 'description', 'supplier__company_name']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    ordering = ['-created_at']
