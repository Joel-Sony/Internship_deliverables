import os
from io import BytesIO
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from PIL import Image


# ── Soft Delete Manager ──

class SoftDeleteManager(models.Manager):
    """Default manager: only returns non-deleted records."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """Bypass soft-delete filter — use with Model.all_objects."""
    pass


# ── Soft Delete Mixin ──

class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()  # includes deleted records

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft-delete: mark as deleted instead of removing the row."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """Un-delete a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def hard_delete(self):
        """Permanently remove the row from the database."""
        super().delete()


# ── Constants ──

ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024  # 5 MB
THUMBNAIL_MAX_SIZE = (300, 300)


# ── Validators ──

def validate_image_file_size(value):
    """Reject files larger than MAX_IMAGE_SIZE_MB."""
    if value.size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            f"Image file size must be under {MAX_IMAGE_SIZE_MB} MB. "
            f"Uploaded file is {value.size / (1024 * 1024):.2f} MB."
        )


def validate_image_content_type(value):
    """Verify that the uploaded file is a genuine image by reading its header."""
    try:
        img = Image.open(value)
        img.verify()  # verify it's a real image
        value.seek(0)  # reset pointer after verify
    except Exception:
        raise ValidationError(
            "Uploaded file is not a valid image. "
            f"Allowed types: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}."
        )


class Category(SoftDeleteMixin):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(SoftDeleteMixin):
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
    """
    Stores product images with automatic thumbnail generation.
    Each product can have multiple images; one can be marked as primary.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='products/images/%Y/%m/',
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS),
            validate_image_file_size,
            validate_image_content_type,
        ],
        help_text=f"Allowed types: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}. Max size: {MAX_IMAGE_SIZE_MB} MB."
    )
    thumbnail = models.ImageField(
        upload_to='products/thumbnails/%Y/%m/',
        blank=True,
        editable=False,
        help_text="Auto-generated 300×300 thumbnail."
    )
    alt_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="Alt text for accessibility."
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Mark as the main display image for the product."
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', '-uploaded_at']

    def __str__(self):
        return f"Image for {self.product.name} ({'primary' if self.is_primary else 'secondary'})"

    def save(self, *args, **kwargs):
        """Generate thumbnail before saving."""
        # If this is marked primary, un-mark any other primary images
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)

        # Generate thumbnail after the image has been saved to disk
        if self.image and (not self.thumbnail or self._thumbnail_needs_update()):
            self._generate_thumbnail()

    def delete(self, *args, **kwargs):
        """Clean up files from disk when the record is deleted."""
        image_path = self.image.path if self.image else None
        thumb_path = self.thumbnail.path if self.thumbnail else None
        super().delete(*args, **kwargs)
        for path in [image_path, thumb_path]:
            if path and os.path.isfile(path):
                os.remove(path)

    def _thumbnail_needs_update(self):
        """Check if thumbnail is missing or outdated."""
        if not self.thumbnail:
            return True
        try:
            return not os.path.isfile(self.thumbnail.path)
        except Exception:
            return True

    def _generate_thumbnail(self):
        """Create a 300×300 thumbnail from the original image."""
        try:
            img = Image.open(self.image.path)

            # Convert RGBA/P to RGB for JPEG compatibility
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            img.thumbnail(THUMBNAIL_MAX_SIZE, Image.LANCZOS)

            thumb_io = BytesIO()
            img_format = 'JPEG'
            ext = os.path.splitext(self.image.name)[1].lower()
            if ext == '.png':
                img_format = 'PNG'
            elif ext == '.webp':
                img_format = 'WEBP'
            elif ext == '.gif':
                img_format = 'GIF'

            img.save(thumb_io, format=img_format, quality=85)
            thumb_io.seek(0)

            thumb_filename = f"thumb_{os.path.basename(self.image.name)}"
            self.thumbnail.save(thumb_filename, ContentFile(thumb_io.read()), save=True)
        except Exception:
            # If thumbnail generation fails, continue without it
            pass


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
