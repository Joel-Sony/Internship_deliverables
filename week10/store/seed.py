"""
Seed script — run with: python manage.py shell < store/seed.py
"""
from django.contrib.auth.models import User
from store.models import Category, Product

# Create categories
categories_data = [
    {"name": "Electronics", "description": "Gadgets and electronic devices"},
    {"name": "Clothing", "description": "Apparel and fashion items"},
    {"name": "Books", "description": "Physical and digital books"},
    {"name": "Home & Kitchen", "description": "Home appliances and kitchen tools"},
]

categories = {}
for data in categories_data:
    cat, created = Category.objects.get_or_create(name=data["name"], defaults=data)
    categories[data["name"]] = cat
    print(f"{'Created' if created else 'Exists'}: {cat.name}")

# Create products
products_data = [
    {"name": "Smartphone", "description": "Latest 5G smartphone", "price": 699.99, "stock": 50, "category": "Electronics"},
    {"name": "Laptop", "description": "15-inch business laptop", "price": 1299.99, "stock": 25, "category": "Electronics"},
    {"name": "Wireless Earbuds", "description": "Noise cancelling earbuds", "price": 149.99, "stock": 100, "category": "Electronics"},
    {"name": "T-Shirt", "description": "Cotton crew neck t-shirt", "price": 19.99, "stock": 200, "category": "Clothing"},
    {"name": "Jeans", "description": "Slim fit denim jeans", "price": 49.99, "stock": 80, "category": "Clothing"},
    {"name": "Jacket", "description": "Waterproof winter jacket", "price": 89.99, "stock": 40, "category": "Clothing"},
    {"name": "Python Crash Course", "description": "Beginner-friendly Python book", "price": 29.99, "stock": 60, "category": "Books"},
    {"name": "Clean Code", "description": "A handbook of agile software craftsmanship", "price": 34.99, "stock": 45, "category": "Books"},
    {"name": "Blender", "description": "High-speed kitchen blender", "price": 59.99, "stock": 35, "category": "Home & Kitchen"},
    {"name": "Coffee Maker", "description": "Automatic drip coffee maker", "price": 79.99, "stock": 20, "category": "Home & Kitchen"},
    {"name": "Toaster", "description": "4-slice stainless steel toaster", "price": 39.99, "stock": 55, "category": "Home & Kitchen"},
    {"name": "Desk Lamp", "description": "LED adjustable desk lamp", "price": 24.99, "stock": 70, "category": "Home & Kitchen"},
]

for data in products_data:
    cat = categories[data.pop("category")]
    product, created = Product.objects.get_or_create(name=data["name"], defaults={**data, "category": cat})
    print(f"{'Created' if created else 'Exists'}: {product.name} (${product.price})")

# Create a test user
user, created = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})
if created:
    user.set_password("test1234")
    user.save()
    print("Created test user: testuser / test1234")
else:
    print("Test user already exists")

print("\nSeeding complete!")
