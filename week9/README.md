# Week 9 — E-Commerce Backend API

Advanced ORM & Pagination assignment using Django REST Framework.

## Features

- **Models**: Products, Categories, Users, Carts (with CartItems)
- **Search**: Search products by name/description (`?search=laptop`)
- **Filters**: Filter by price range, category, stock availability
- **Pagination**: 10 items per page with page navigation
- **Aggregations**: Product stats endpoint with per-category breakdowns
- **Validation**: Clean JSON error messages — no DB errors exposed to users

## Setup

- ### Create and activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```
- ### Install dependencies
```
pip install -r requirements.txt
```
- ### Run migrations
```
python manage.py migrate
```
- ### Seed sample data
```
python manage.py shell < store/seed.py
```
- ### Run server
```
python manage.py runserver
```

## API Endpoints

Base URL: `http://localhost:8000/api/`

### Categories
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/categories/` | List all categories (with product count) |
| POST | `/api/categories/` | Create a category |
| GET | `/api/categories/{id}/` | Get category detail |
| PUT | `/api/categories/{id}/` | Update category |
| DELETE | `/api/categories/{id}/` | Delete category (fails if products exist) |

### Products
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/products/` | List products (paginated) |
| POST | `/api/products/` | Create a product |
| GET | `/api/products/{id}/` | Get product detail |
| PUT/PATCH | `/api/products/{id}/` | Update product |
| DELETE | `/api/products/{id}/` | Delete product |

### Query Parameters for Products:
| Param | Example | Description |
|-------|---------|-------------|
| `search` | `?search=laptop` | Search by name or description |
| `min_price` | `?min_price=50` | Minimum price filter |
| `max_price` | `?max_price=200` | Maximum price filter |
| `category` | `?category=1` | Filter by category ID |
| `category_name` | `?category_name=electronics` | Filter by category name |
| `in_stock` | `?in_stock=true` | Only in-stock products |
| `ordering` | `?ordering=price` | Sort by field (prefix `-` for desc) |
| `page` | `?page=2` | Pagination |

### Users
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/users/` | List users |
| POST | `/api/users/` | Register user |
| GET | `/api/users/{id}/` | Get user detail |

### Cart
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/carts/{user_id}/` | View user's cart |
| POST | `/api/carts/{user_id}/add/` | Add item (`{product, quantity}`) |
| POST | `/api/carts/{user_id}/remove/` | Remove item (`{product}`) |
| DELETE | `/api/carts/{user_id}/clear/` | Clear all items |

### Aggregations
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/stats/` | Product stats (avg/min/max price, per-category) |

## DB Schema

```
Category: id, name (unique), description, created_at
Product:  id, name, description, price, stock, category_id (FK), created_at, updated_at
Cart:     id, user_id (OneToOne FK to auth_user), created_at, updated_at
CartItem: id, cart_id (FK), product_id (FK), quantity  [unique_together: cart+product]
User:     Django's built-in auth_user table
```

