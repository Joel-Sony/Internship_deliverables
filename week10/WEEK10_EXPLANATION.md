# Week 10 — Implementation Explanation

> **Focus Topics**: Product Image Uploads · Image Validation · Automatic Thumbnail Generation · File Cleanup · Admin Panel Integration

This document walks through **how** each feature is implemented in the Week 10
E-Commerce Backend API, pointing to the exact files, classes, functions, and
Django/DRF mechanisms involved.

Week 10 builds on top of Week 9 (aggregations, search filters, pagination) by
adding a complete **product image management system**.

---

## 1. Product Image Uploads (Single & Multiple)

### What it does

Each product can have multiple images uploaded via a REST API endpoint. Users
can upload 1–10 images in a single request using `multipart/form-data`, and one
image can be marked as the "primary" display image.

### Where it lives

| File | Location |
|------|----------|
| `store/views.py` | `ProductImageViewSet.upload()` (lines 82–155) |
| `store/serializers.py` | `ProductImageUploadSerializer` (lines 57–96) |
| `store/models.py` | `ProductImage` model (lines 83–185) |
| `store/urls.py` | `products/<id>/images/upload/` (lines 36–39) |

### How it works — step by step

#### a) The upload endpoint

```python
# store/views.py → ProductImageViewSet

@action(detail=False, methods=['post'], url_path='upload')
def upload(self, request, product_pk=None):
    files = request.FILES.getlist('images')  # Multiple files from one key
    serializer = ProductImageUploadSerializer(data={
        'images': files,
        'alt_text': request.data.get('alt_text', ''),
        'is_primary': request.data.get('is_primary', False),
    })
```

- Uses `MultiPartParser` and `FormParser` to handle file uploads.
- `request.FILES.getlist('images')` collects **all files** sent under the `images` key.
- Each file is individually validated, then saved in a loop with `full_clean()` + `save()`.

#### b) The upload serializer validates each file

```python
# store/serializers.py → ProductImageUploadSerializer

images = serializers.ListField(
    child=serializers.ImageField(),
    min_length=1,
    max_length=10,  # Upload 1–10 images at once
)
```

- `ListField` with `ImageField` children enforces that each item is a valid image.
- `min_length=1` prevents empty uploads; `max_length=10` caps batch size.
- A custom `validate_images()` method checks extension and file size per file.

#### c) Per-file error handling

```python
# store/views.py → upload()

for idx, image_file in enumerate(serializer.validated_data['images']):
    try:
        img = ProductImage(product=product, image=image_file, ...)
        img.full_clean()   # run model-level validators
        img.save()         # triggers thumbnail generation
        created_images.append(img)
    except Exception as e:
        errors.append({"file": image_file.name, "error": str(e)})
```

- Each file is processed independently — if one fails validation, the rest still upload.
- Errors are collected and returned alongside successes in the response.

---

## 2. Image Validation (3 Layers)

### What it does

Every uploaded image is validated for file extension, file size, and actual
content (is it really an image?) to prevent malicious or invalid uploads.

### Where it lives

| File | Location |
|------|----------|
| `store/models.py` | `validate_image_file_size()` (lines 24–30) |
| `store/models.py` | `validate_image_content_type()` (lines 33–43) |
| `store/models.py` | `ProductImage.image` field validators (lines 93–99) |
| `store/serializers.py` | `ProductImageUploadSerializer.validate_images()` (lines 77–96) |
| `ecommerce/settings.py` | `DATA_UPLOAD_MAX_MEMORY_SIZE` (line 140) |

### How it works — the 3 validation layers

#### Layer 1: Serializer-level (pre-save)

```python
# store/serializers.py → validate_images()

for f in files:
    ext = f.name.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:     # ['jpg','jpeg','png','gif','webp']
        errors.append(f"File '{f.name}': extension not allowed.")
    if f.size > MAX_IMAGE_SIZE_BYTES:            # 5 MB
        errors.append(f"File '{f.name}': exceeds 5 MB limit.")
```

Quick, cheap checks done before any database interaction.

#### Layer 2: Model field validators (on `full_clean()`)

```python
# store/models.py → ProductImage.image field

image = models.ImageField(
    validators=[
        FileExtensionValidator(allowed_extensions=['jpg','jpeg','png','gif','webp']),
        validate_image_file_size,        # Rejects files > 5 MB
        validate_image_content_type,     # Opens file with Pillow to verify it's a real image
    ],
)
```

| Validator | What it checks |
|-----------|----------------|
| `FileExtensionValidator` | File extension is in the allowed list |
| `validate_image_file_size` | File size ≤ 5 MB |
| `validate_image_content_type` | Uses `Pillow` to open & `img.verify()` — catches renamed `.exe` → `.jpg` files |

#### Layer 3: Django settings (global limit)

```python
# ecommerce/settings.py

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
```

Django itself rejects any request body larger than 10 MB before it even reaches the view.

#### Summary

```
Request → Django (10 MB body limit)
       → Serializer (extension + size per file)
       → Model full_clean() (extension + size + Pillow content verify)
       → Save to disk
```

---

## 3. Automatic Thumbnail Generation

### What it does

Every time an image is saved, a 300×300 thumbnail is automatically generated
using Pillow and stored alongside the original — no manual step required.

### Where it lives

| File | Location |
|------|----------|
| `store/models.py` | `ProductImage.save()` (lines 125–137) |
| `store/models.py` | `ProductImage._generate_thumbnail()` (lines 157–185) |

### How it works — step by step

#### a) Triggered on `save()`

```python
# store/models.py → ProductImage.save()

def save(self, *args, **kwargs):
    if self.is_primary:
        # Un-mark any other primary images for this product
        ProductImage.objects.filter(
            product=self.product, is_primary=True
        ).exclude(pk=self.pk).update(is_primary=False)

    super().save(*args, **kwargs)   # save original image to disk first

    # Generate thumbnail after image is on disk
    if self.image and (not self.thumbnail or self._thumbnail_needs_update()):
        self._generate_thumbnail()
```

- The original image is saved first via `super().save()`.
- Then `_generate_thumbnail()` runs only if a thumbnail doesn't exist or is outdated.

#### b) The thumbnail generation logic

```python
# store/models.py → _generate_thumbnail()

img = Image.open(self.image.path)            # Open with Pillow
if img.mode in ('RGBA', 'P'):
    img = img.convert('RGB')                  # Convert for JPEG compatibility
img.thumbnail(THUMBNAIL_MAX_SIZE, Image.LANCZOS)  # Resize to 300×300

thumb_io = BytesIO()
img.save(thumb_io, format=img_format, quality=85)
self.thumbnail.save(thumb_filename, ContentFile(thumb_io.read()), save=True)
```

| Step | What happens |
|------|-------------|
| Open | Pillow reads the saved image from disk |
| Convert | RGBA/P mode images → RGB (JPEG doesn't support transparency) |
| Resize | `img.thumbnail()` scales down preserving aspect ratio, max 300×300 |
| Save | Written to `products/thumbnails/YYYY/MM/` via Django's storage |

#### c) File organization on disk

```
media/
├── products/
│   ├── images/2026/04/       ← original uploads
│   │   ├── laptop_front.jpg
│   │   └── laptop_back.jpg
│   └── thumbnails/2026/04/   ← auto-generated thumbnails
│       ├── thumb_laptop_front.jpg
│       └── thumb_laptop_back.jpg
```

---

## 4. File Cleanup on Delete

### What it does

When a product image record is deleted, both the original image **and** the
thumbnail are removed from disk — preventing orphaned files.

### Where it lives

| File | Location |
|------|----------|
| `store/models.py` | `ProductImage.delete()` (lines 139–146) |
| `store/views.py` | `ProductImageViewSet.destroy()` (lines 208–235) |

### How it works

```python
# store/models.py → ProductImage.delete()

def delete(self, *args, **kwargs):
    image_path = self.image.path if self.image else None
    thumb_path = self.thumbnail.path if self.thumbnail else None
    super().delete(*args, **kwargs)       # delete DB record first
    for path in [image_path, thumb_path]:
        if path and os.path.isfile(path):
            os.remove(path)               # then remove files from disk
```

- Paths are captured **before** the DB delete (since the object won't have them after).
- `os.remove()` cleans up both files.
- The view's `destroy()` method catches any exceptions and returns clean JSON errors.

---

## 5. Primary Image Management

### What it does

Each product can have one image marked as "primary" (the main display image).
Setting a new primary automatically un-marks the old one.

### Where it lives

| File | Location |
|------|----------|
| `store/views.py` | `ProductImageViewSet.set_primary()` (lines 239–273) |
| `store/models.py` | `ProductImage.save()` (lines 125–131) |

### How it works

```python
# store/views.py → set_primary()

ProductImage.objects.filter(
    product=product, is_primary=True
).update(is_primary=False)           # un-mark all
image.is_primary = True
image.save(update_fields=['is_primary'])  # mark the new one
```

This is also enforced in the model's `save()` method, so even if an image is
created with `is_primary=True` via the upload endpoint, any existing primary
is automatically demoted.

---

## 6. Nested REST API Design

### What it does

Image endpoints are nested under products, creating intuitive, resource-oriented URLs.

### Where it lives

| File | Location |
|------|----------|
| `store/urls.py` | Nested URL patterns (lines 11–51) |

### The endpoint structure

| Endpoint | Method | Action |
|----------|--------|--------|
| `/api/products/{id}/images/` | `GET` | List all images for a product |
| `/api/products/{id}/images/upload/` | `POST` | Upload 1–10 images |
| `/api/products/{id}/images/{img_id}/` | `GET` | Get single image details |
| `/api/products/{id}/images/{img_id}/` | `DELETE` | Delete an image + files |
| `/api/products/{id}/images/{img_id}/set-primary/` | `POST` | Mark as primary |

### How the nesting works

```python
# store/urls.py

image_list = views.ProductImageViewSet.as_view({'get': 'list'})
image_upload = views.ProductImageViewSet.as_view({'post': 'upload'})

urlpatterns = [
    path('products/<int:product_pk>/images/', image_list),
    path('products/<int:product_pk>/images/upload/', image_upload),
    ...
]
```

- `product_pk` is passed from the URL to the view, which uses `_get_product(product_pk)` to fetch the product.
- The product listing endpoint (`GET /api/products/`) includes images inline via `prefetch_related('images')`.

---

## 7. Admin Panel Integration

### What it does

Product images are manageable through Django's admin interface, with inline
image editing directly on the product page.

### Where it lives

| File | Location |
|------|----------|
| `store/admin.py` | `ProductImageInline`, `ProductImageAdmin` (lines 11–35) |

### How it works

```python
# store/admin.py

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1                                    # show 1 empty upload slot
    readonly_fields = ['thumbnail', 'uploaded_at']
    fields = ['image', 'thumbnail', 'alt_text', 'is_primary', 'uploaded_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]               # images shown inside product page
    def image_count(self, obj):
        return obj.images.count()                # custom column showing image count
```

- `TabularInline` embeds the images table directly inside the product edit page.
- Thumbnails and upload timestamps are shown as read-only fields.
- A separate `ProductImageAdmin` also allows managing images independently.

---

## How Everything Connects — Image Upload Flow

Here's what happens when a client sends:

```
POST /api/products/5/images/upload/
Content-Type: multipart/form-data
images: [file1.jpg, file2.png]
alt_text: "Product shot"
is_primary: true
```

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Django checks body size ≤ 10 MB (settings.py)               │
├─────────────────────────────────────────────────────────────────┤
│  2. urls.py routes to ProductImageViewSet.upload()              │
│     → MultiPartParser extracts files from request               │
├─────────────────────────────────────────────────────────────────┤
│  3. ProductImageUploadSerializer validates:                     │
│     → 1–10 files? ✓                                            │
│     → Each file: extension allowed? ✓  Size ≤ 5 MB? ✓          │
├─────────────────────────────────────────────────────────────────┤
│  4. For each validated file:                                    │
│     a) Create ProductImage instance                             │
│     b) full_clean() → model validators run:                     │
│        → FileExtensionValidator ✓                               │
│        → validate_image_file_size ✓                             │
│        → validate_image_content_type (Pillow verify) ✓          │
│     c) save() →                                                 │
│        → If is_primary: un-mark other primaries                 │
│        → Save original to media/products/images/YYYY/MM/        │
│        → _generate_thumbnail() → Pillow resize → save thumb    │
├─────────────────────────────────────────────────────────────────┤
│  5. Response: 201 Created                                       │
│     → { uploaded: [{id, image_url, thumbnail_url, ...}],       │
│          errors: [...] }                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Quick Reference

| File | Key Contents |
|------|-------------|
| `store/models.py` | `ProductImage` model with validators, auto-thumbnail in `save()`, file cleanup in `delete()` |
| `store/views.py` | `ProductImageViewSet` — upload, list, retrieve, delete, set-primary endpoints |
| `store/serializers.py` | `ProductImageUploadSerializer` (batch validation), `ProductImageSerializer` (read-only output with URLs) |
| `store/admin.py` | `ProductImageInline` for managing images inside the product admin page |
| `store/urls.py` | Nested URL patterns under `/products/{id}/images/` |
| `ecommerce/settings.py` | `MEDIA_URL`, `MEDIA_ROOT`, `DATA_UPLOAD_MAX_MEMORY_SIZE` configuration |
