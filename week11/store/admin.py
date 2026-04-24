from django.contrib import admin
from .models import Category, Product, ProductImage, Cart, CartItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


class ProductImageInline(admin.TabularInline):
    """Inline display of product images within the Product admin page."""
    model = ProductImage
    extra = 1
    readonly_fields = ['thumbnail', 'uploaded_at']
    fields = ['image', 'thumbnail', 'alt_text', 'is_primary', 'uploaded_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'category', 'image_count', 'created_at']
    list_filter = ['category']
    search_fields = ['name', 'description']
    inlines = [ProductImageInline]

    def image_count(self, obj):
        return obj.images.count()
    image_count.short_description = 'Images'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'is_primary', 'uploaded_at']
    list_filter = ['is_primary', 'product']
    readonly_fields = ['thumbnail', 'uploaded_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity']
