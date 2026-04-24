from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Count, Avg, Min, Max, Sum

from .models import Category, Product, Cart, CartItem
from .serializers import (
    CategorySerializer, ProductSerializer,
    UserSerializer, CartSerializer, CartItemSerializer
)
from .filters import ProductFilter


# ── Category CRUD ──

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.annotate(product_count=Count('products'))

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        if category.products.exists():
            return Response(
                {"error": "Cannot delete category that has products. Remove products first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


# ── Product CRUD + Search + Filters + Pagination ──

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    search_fields = ['name', 'description']  # ?search=keyword
    ordering_fields = ['price', 'name', 'created_at', 'stock']  # ?ordering=price
    ordering = ['-created_at']  # default ordering


# ── User Registration ──

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post']  # only list, create, retrieve


# ── Cart ──

class CartViewSet(viewsets.ViewSet):
    """
    Cart operations using user_id as a path param.
    GET  /carts/{user_id}/       → view cart
    POST /carts/{user_id}/add/   → add item
    POST /carts/{user_id}/remove/→ remove item
    DELETE /carts/{user_id}/clear/→ clear cart
    """

    def retrieve(self, request, pk=None):
        """View a user's cart."""
        cart = self._get_or_create_cart(pk)
        if cart is None:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add(self, request, pk=None):
        """Add a product to cart. Body: {product: id, quantity: int}"""
        cart = self._get_or_create_cart(pk)
        if cart is None:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product = serializer.validated_data['product']
        quantity = serializer.validated_data.get('quantity', 1)

        # If item already in cart, update quantity
        try:
            item = CartItem.objects.get(cart=cart, product=product)
            new_qty = item.quantity + quantity
            if new_qty > product.stock:
                return Response(
                    {"error": f"Only {product.stock} items available. You already have {item.quantity} in cart."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            item.quantity = new_qty
            item.save()
        except CartItem.DoesNotExist:
            CartItem.objects.create(cart=cart, product=product, quantity=quantity)

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def remove(self, request, pk=None):
        """Remove a product from cart. Body: {product: id}"""
        cart = self._get_or_create_cart(pk)
        if cart is None:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        product_id = request.data.get('product')
        if not product_id:
            return Response({"error": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = CartItem.objects.get(cart=cart, product_id=product_id)
            item.delete()
        except CartItem.DoesNotExist:
            return Response({"error": "Product not in cart."}, status=status.HTTP_404_NOT_FOUND)

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'])
    def clear(self, request, pk=None):
        """Clear all items from cart."""
        cart = self._get_or_create_cart(pk)
        if cart is None:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        cart.items.all().delete()
        return Response({"message": "Cart cleared."}, status=status.HTTP_200_OK)

    def _get_or_create_cart(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart


# ── Aggregation Stats Endpoint ──

@api_view(['GET'])
def product_stats(request):
    """Aggregated product statistics — shows ORM aggregation skills."""
    stats = Product.objects.aggregate(
        total_products=Count('id'),
        average_price=Avg('price'),
        min_price=Min('price'),
        max_price=Max('price'),
        total_stock=Sum('stock'),
    )

    # Per-category stats
    category_stats = list(
        Category.objects.annotate(
            product_count=Count('products'),
            avg_price=Avg('products__price'),
            total_stock=Sum('products__stock'),
        ).values('id', 'name', 'product_count', 'avg_price', 'total_stock')
    )

    return Response({
        "overall": stats,
        "by_category": category_stats
    })
