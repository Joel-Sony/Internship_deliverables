import cloudinary
import cloudinary.uploader
import cloudinary.api

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from PIL import Image


# ── Constants ──

ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024


# ── Validators ──

def validate_image_file_size(value):
    if value.size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            f"Image file size must be under {MAX_IMAGE_SIZE_MB} MB. "
            f"Uploaded file is {value.size / (1024 * 1024):.2f} MB."
        )

def validate_image_content_type(value):
    try:
        img = Image.open(value)
        img.verify()
        value.seek(0)
    except Exception:
        raise ValidationError(
            f"Uploaded file is not a valid image. "
            f"Allowed types: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}."
        )


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    cloudinary_public_id = models.CharField(max_length=500, blank=True)
    thumbnail_public_id = models.CharField(max_length=500, blank=True)
    image_url = models.URLField(max_length=1000, blank=True)
    thumbnail_url = models.URLField(max_length=1000, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', '-uploaded_at']

    def __str__(self):
        return f"Image for {self.product.name} ({'primary' if self.is_primary else 'secondary'})"

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        for public_id in [self.cloudinary_public_id, self.thumbnail_public_id]:
            if public_id:
                try:
                    cloudinary.api.delete_resources([public_id])
                except Exception:
                    pass
        super().delete(*args, **kwargs)

    @classmethod
    def upload_to_cloudinary(cls, file, product, alt_text='', is_primary=False):
        upload_result = cloudinary.uploader.upload(
            file,
            folder=f"products/{product.pk}/images",
            resource_type="image",
        )
        full_url = upload_result['secure_url']
        full_public_id = upload_result['public_id']

        file.seek(0)
        thumb_result = cloudinary.uploader.upload(
            file,
            folder=f"products/{product.pk}/thumbnails",
            resource_type="image",
            transformation=[
                {'width': 300, 'height': 300, 'crop': 'fill', 'gravity': 'auto'}
            ],
        )
        thumb_url = thumb_result['secure_url']
        thumb_public_id = thumb_result['public_id']

        img = cls(
            product=product,
            cloudinary_public_id=full_public_id,
            thumbnail_public_id=thumb_public_id,
            image_url=full_url,
            thumbnail_url=thumb_url,
            alt_text=alt_text,
            is_primary=is_primary,
        )
        img.save()
        return img


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def subtotal(self):
        return self.product.price * self.quantity