# Week 10 — File Uploads & Media Handling

Product image upload API with automatic thumbnail generation.

## Features

- Multiple image upload per product (1–10 at once)
- File validation: type (jpg/png/gif/webp), size (5 MB max), content (Pillow verify)
- Auto 300×300 thumbnail generation
- Set primary image, list, retrieve, delete
- DB errors shielded from user via try/except

## Setup

```bash
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/products/{id}/images/upload/` | Upload images (multipart/form-data) |
| GET | `/api/products/{id}/images/` | List product images |
| GET | `/api/products/{id}/images/{img_id}/` | Get image detail |
| DELETE | `/api/products/{id}/images/{img_id}/` | Delete image |
| POST | `/api/products/{id}/images/{img_id}/set-primary/` | Set primary image |

## Tech Stack

- Python 3 / Django 5.2 / DRF
- Pillow (thumbnail generation)
- SQLite

## Screenshots

See the [`screenshots/`](screenshots/) folder:

| Screenshot | Description |
|------------|-------------|
| [01_upload_endpoint.png](screenshots/01_upload_endpoint.png) | Upload endpoint with POST form |
| [02_image_list.png](screenshots/02_image_list.png) | List all images for a product |
| [03_product_detail_with_images.png](screenshots/03_product_detail_with_images.png) | Product detail with nested images |
| [04_set_primary.png](screenshots/04_set_primary.png) | Set primary image response |
| [05_image_detail.png](screenshots/05_image_detail.png) | Single image detail |
| [06_validation_error_404.png](screenshots/06_validation_error_404.png) | 404 error for non-existent product |
