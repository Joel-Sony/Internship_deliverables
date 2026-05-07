# Week 9 — Implementation Explanation

> **Focus Topics**: Aggregations · Advanced Search Filters · Pagination

This document walks through **how** each of these three features is implemented in
the Week 9 E-Commerce Backend API, pointing to the exact files, classes, functions,
and Django/DRF mechanisms involved.

---

## 1. Aggregations

### What it does

The `/api/stats/` endpoint returns computed statistics across all products and a
per-category breakdown — without loading every row into Python. All the math is
done **inside the database** using Django ORM aggregation functions.

### Where it lives

| File | Location |
|------|----------|
| `store/views.py` | `product_stats()` function (lines 140–163) |
| `store/urls.py` | `path('stats/', views.product_stats)` (line 13) |

### How it works — step by step

#### a) Overall stats — `aggregate()`

```python
# store/views.py  →  product_stats()

stats = Product.objects.aggregate(
    total_products=Count('id'),
    average_price=Avg('price'),
    min_price=Min('price'),
    max_price=Max('price'),
    total_stock=Sum('stock'),
)
```

- **`aggregate()`** collapses the entire `Product` table into a single dictionary.
- Each keyword argument maps a label to an aggregation function imported from
  `django.db.models` (`Count`, `Avg`, `Min`, `Max`, `Sum`).
- Under the hood Django generates SQL like:

  ```sql
  SELECT COUNT(id)       AS total_products,
         AVG(price)      AS average_price,
         MIN(price)      AS min_price,
         MAX(price)      AS max_price,
         SUM(stock)      AS total_stock
  FROM store_product;
  ```

- The result is a **flat dict**, e.g.
  `{"total_products": 25, "average_price": 149.99, ...}` — no queryset, just data.

#### b) Per-category stats — `annotate()`

```python
# store/views.py  →  product_stats()

category_stats = list(
    Category.objects.annotate(
        product_count=Count('products'),
        avg_price=Avg('products__price'),
        total_stock=Sum('products__stock'),
    ).values('id', 'name', 'product_count', 'avg_price', 'total_stock')
)
```

- **`annotate()`** is different from `aggregate()` — it calculates a value **for
  each row** in the queryset (here, each Category) instead of collapsing to one result.
- `'products'` is the `related_name` defined on the `Product.category` ForeignKey,
  so Django knows how to reverse-join from `Category → Product`.
- `.values(...)` turns each annotated Category object into a plain dict, which is
  perfect for direct JSON serialization.
- The SQL equivalent is a `GROUP BY category.id` with the same aggregation functions.

#### c) `annotate()` is also used in the Category list endpoint

```python
# store/views.py → CategoryViewSet.get_queryset()

def get_queryset(self):
    return Category.objects.annotate(product_count=Count('products'))
``` 

This adds a `product_count` field to every category returned by `GET /api/categories/`,
showing how many products belong to each category — another use of annotation.

#### d) Summary

| ORM Method | Purpose | Returns |
|------------|---------|---------|
| `aggregate()` | Compute a **single** summary across all rows | A flat `dict` |
| `annotate()` | Attach a computed value to **each** row in the queryset | A queryset with extra fields |

---

## 2. Advanced Search Filters

### What it does

The `GET /api/products/` endpoint supports searching, filtering by price/category/stock,
and ordering — all via query parameters.

### Where it lives

| File | Purpose |
|------|---------|
| `store/filters.py` | `ProductFilter` class — custom filter definitions |
| `store/views.py` | `ProductViewSet` — wires the filter + search + ordering into the view |
| `ecommerce/settings.py` | `REST_FRAMEWORK` config — registers the filter backends globally |

### How it works — step by step

#### a) Global filter backends (settings.py)

```python
# ecommerce/settings.py

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',   # ← field filters
        'rest_framework.filters.SearchFilter',                 # ← ?search=
        'rest_framework.filters.OrderingFilter',               # ← ?ordering=
    ],
    ...
}
```

These three backends are applied **to every ViewSet automatically**:

| Backend | Query Param | What it does |
|---------|-------------|--------------|
| `DjangoFilterBackend` | `?min_price=`, `?category=`, etc. | Applies exact / range / custom filters |
| `SearchFilter` | `?search=laptop` | Partial text search across specified fields |
| `OrderingFilter` | `?ordering=price` or `?ordering=-price` | Sorts the result set |

#### b) Search — `SearchFilter` + `search_fields`

```python
# store/views.py → ProductViewSet

class ProductViewSet(viewsets.ModelViewSet):
    search_fields = ['name', 'description']   # ← which fields to search in
```

- When a user hits `GET /api/products/?search=laptop`, DRF's `SearchFilter`
  backend reads `search_fields` and builds an ORM query:

  ```python
  Q(name__icontains='laptop') | Q(description__icontains='laptop')
  ```

- This is a **case-insensitive partial match** — it finds any product where
  "laptop" appears anywhere in the name or description.
- No extra code needed; just declaring `search_fields` is enough because the
  backend is already registered globally.

#### c) Field filters — `django-filter` + `ProductFilter`

```python
# store/filters.py

class ProductFilter(django_filters.FilterSet):
    min_price     = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price     = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category      = django_filters.NumberFilter(field_name='category__id')
    category_name = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    in_stock      = django_filters.BooleanFilter(method='filter_in_stock')

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'category', 'category_name', 'in_stock']

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)
```

How each filter maps to the ORM:

| Query Param | Filter Type | ORM Lookup Generated |
|-------------|-------------|----------------------|
| `?min_price=50` | `NumberFilter` with `gte` | `Product.objects.filter(price__gte=50)` |
| `?max_price=200` | `NumberFilter` with `lte` | `Product.objects.filter(price__lte=200)` |
| `?category=3` | `NumberFilter` (exact) | `Product.objects.filter(category__id=3)` |
| `?category_name=electronics` | `CharFilter` with `icontains` | `Product.objects.filter(category__name__icontains='electronics')` |
| `?in_stock=true` | `BooleanFilter` (custom) | `Product.objects.filter(stock__gt=0)` |
| `?in_stock=false` | `BooleanFilter` (custom) | `Product.objects.filter(stock=0)` |

Key points:
- **`lookup_expr`** controls the SQL operator: `gte` → `>=`, `lte` → `<=`,
  `icontains` → `LIKE '%...%'` (case-insensitive).
- **`method='filter_in_stock'`** is a custom filter method. Instead of a
  one-to-one field mapping, it runs custom logic to decide which ORM call to
  make based on the boolean value.
- The `category__name` double-underscore syntax follows the ForeignKey relationship
  (`Product → Category`) to filter on a field in the related table.

The filter class is wired into the view with one line:

```python
# store/views.py → ProductViewSet

filterset_class = ProductFilter
```

#### d) Ordering — `OrderingFilter` + `ordering_fields`

```python
# store/views.py → ProductViewSet

ordering_fields = ['price', 'name', 'created_at', 'stock']
ordering = ['-created_at']   # default sort
```

- `ordering_fields` is a **whitelist** — users can only sort by these fields.
- `?ordering=price` → ascending by price; `?ordering=-price` → descending.
- `ordering` sets the default when no `?ordering=` param is provided.

#### e) Combining filters

All filters **stack**. A request like:

```
GET /api/products/?search=phone&min_price=100&max_price=500&category_name=electronics&in_stock=true&ordering=price
```

produces a queryset equivalent to:

```python
Product.objects.filter(
    Q(name__icontains='phone') | Q(description__icontains='phone'),
    price__gte=100,
    price__lte=500,
    category__name__icontains='electronics',
    stock__gt=0,
).order_by('price')
```

Each backend processes the queryset in sequence, so they compose naturally.

---

## 3. Pagination

### What it does

All list endpoints (products, categories, users) return results in pages of 10
items, with navigation metadata included in the JSON response.

### Where it lives

| File | Purpose |
|------|---------|
| `ecommerce/settings.py` | Global pagination config |

### How it works — step by step

#### a) Configuration

```python
# ecommerce/settings.py

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    ...
}
```

- **`PageNumberPagination`** is DRF's built-in page-number style paginator.
- **`PAGE_SIZE: 10`** means every paginated response contains at most 10 items.
- This is set **globally** — every `ModelViewSet` inherits it automatically.

#### b) How the user navigates pages

| Request | Page |
|---------|------|
| `GET /api/products/` | Page 1 (default) |
| `GET /api/products/?page=2` | Page 2 |
| `GET /api/products/?page=3` | Page 3 |

#### c) What the paginated response looks like

Instead of returning a bare JSON array, DRF wraps the results:

```json
{
    "count": 25,
    "next": "http://localhost:8000/api/products/?page=2",
    "previous": null,
    "results": [
        { "id": 1, "name": "Laptop", ... },
        { "id": 2, "name": "Phone", ... },
        ...
    ]
}
```

| Field | Meaning |
|-------|---------|
| `count` | Total number of objects across all pages |
| `next` | URL to the next page (`null` if on last page) |
| `previous` | URL to the previous page (`null` if on first page) |
| `results` | The actual items for the current page (up to 10) |

#### d) Pagination + Filters work together

Pagination is applied **after** filtering. So a request like:

```
GET /api/products/?category=1&page=2
```

first filters down to only category 1 products, then returns page 2 of those
filtered results. The `count` field reflects the filtered total — not the total
of all products.

#### e) Why pagination matters

- **Performance**: Without pagination, a database with thousands of products
  would serialize and transfer everything in one request — slow and memory-heavy.
- **Usability**: Front-end clients can load data incrementally and display
  page navigation controls.
- **Bandwidth**: Small payloads per request keep the API snappy.

---

## How Everything Connects — The Full Request Flow

Here's what happens when a client sends:

```
GET /api/products/?search=laptop&min_price=100&in_stock=true&page=2
```

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Request hits urls.py                                        │
│     → routed to ProductViewSet (registered via DefaultRouter)   │
├─────────────────────────────────────────────────────────────────┤
│  2. DRF reads DEFAULT_FILTER_BACKENDS from settings.py          │
│     → applies each backend in order:                            │
│                                                                 │
│     a) DjangoFilterBackend reads ProductFilter (filters.py)     │
│        → applies: price__gte=100, stock__gt=0                   │
│                                                                 │
│     b) SearchFilter reads search_fields                         │
│        → applies: name__icontains='laptop' OR                   │
│                   description__icontains='laptop'               │
│                                                                 │
│     c) OrderingFilter reads ordering_fields                     │
│        → no ?ordering= param, so uses default: -created_at       │
├─────────────────────────────────────────────────────────────────┤
│  3. PageNumberPagination slices the filtered queryset           │
│     → page=2, PAGE_SIZE=10 → rows 11–20                         │
├─────────────────────────────────────────────────────────────────┤
│  4. ProductSerializer serializes each Product in the page       │
│     → includes category_name via select_related('category')     │
├─────────────────────────────────────────────────────────────────┤
│  5. DRF wraps it in the paginated response envelope             │
│     → { "count": ..., "next": ..., "previous": ...,            │
│          "results": [...] }                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Quick Reference

| File | Key Contents |
|------|-------------|
| `store/models.py` | `Product`, `Category`, `Cart`, `CartItem` models with validators & relationships |
| `store/views.py` | `ProductViewSet` (search + filters), `CategoryViewSet` (annotated queryset), `product_stats()` (aggregations) |
| `store/filters.py` | `ProductFilter` — price range, category, and stock availability filters |
| `store/serializers.py` | Serializers with custom validation (price > 0, stock ≥ 0, unique emails, etc.) |
| `store/urls.py` | Router registration + stats endpoint |
| `store/exceptions.py` | Custom exception handler — catches `IntegrityError` and other unhandled exceptions |
| `ecommerce/settings.py` | DRF config — pagination class, page size, filter backends, exception handler |
