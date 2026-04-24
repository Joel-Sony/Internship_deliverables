from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Category, Product, ProductImage, Cart, CartItem,
    ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_SIZE_MB, MAX_IMAGE_SIZE_BYTES,
)


# ── Category ──

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'product_count', 'created_at']

    def validate_name(self, value):
        # Case-insensitive uniqueness check
        qs = Category.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value


# ── Product Image ──

class ProductImageSerializer(serializers.ModelSerializer):
    """Read-only serializer for returning product image data."""
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = [
            'id', 'product', 'image', 'image_url',
            'thumbnail', 'thumbnail_url', 'alt_text',
            'is_primary', 'uploaded_at',
        ]
        read_only_fields = ['id', 'thumbnail', 'uploaded_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None


class ProductImageUploadSerializer(serializers.Serializer):
    """
    Handles single or multiple image uploads with validation.
    Accepts: images (multiple files), alt_text, is_primary.
    """
    images = serializers.ListField(
        child=serializers.ImageField(),
        min_length=1,
        max_length=10,
        help_text="Upload 1–10 images at once.",
    )
    alt_text = serializers.CharField(
        max_length=200, required=False, default='', allow_blank=True,
        help_text="Alt text applied to all uploaded images.",
    )
    is_primary = serializers.BooleanField(
        required=False, default=False,
        help_text="If true, the FIRST uploaded image becomes the primary image.",
    )

    def validate_images(self, files):
        """Validate every file in the batch for type and size."""
        errors = []
        for i, f in enumerate(files):
            # Check extension
            ext = f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                errors.append(
                    f"File '{f.name}': extension '.{ext}' is not allowed. "
                    f"Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}."
                )
            # Check size
            if f.size > MAX_IMAGE_SIZE_BYTES:
                errors.append(
                    f"File '{f.name}': size {f.size / (1024 * 1024):.2f} MB "
                    f"exceeds the {MAX_IMAGE_SIZE_MB} MB limit."
                )
        if errors:
            raise serializers.ValidationError(errors)
        return files


# ── Product ──

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    image_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'stock',
            'category', 'category_name',
            'images', 'image_count',
            'created_at', 'updated_at',
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value

    def get_image_count(self, obj):
        return obj.images.count()


# ── User ──

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'date_joined']
        read_only_fields = ['date_joined']

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required.")
        qs = User.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user


# ── Cart ──

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(
        source='product.price', read_only=True,
        max_digits=10, decimal_places=2
    )
    subtotal = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'subtotal']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def validate_product(self, value):
        if value.stock < 1:
            raise serializers.ValidationError("This product is out of stock.")
        return value

    def validate(self, data):
        product = data.get('product')
        quantity = data.get('quantity', 1)
        if product and quantity > product.stock:
            raise serializers.ValidationError(
                {"quantity": f"Only {product.stock} items available in stock."}
            )
        return data


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'item_count', 'total', 'created_at', 'updated_at']
        read_only_fields = ['user']

    def get_total(self, obj):
        return sum(item.subtotal for item in obj.items.all())

    def get_item_count(self, obj):
        return obj.items.count()
