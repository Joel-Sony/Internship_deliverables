import requests

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import action
from django.contrib.auth.models import User
from django.db.models import Count, Avg, Min, Max, Sum

from .models import Category, Product, ProductImage, Cart, CartItem
from .serializers import (
    CategorySerializer, ProductSerializer,
    ProductImageSerializer, ProductImageUploadSerializer,
    UserSerializer, CartSerializer, CartItemSerializer
)
from .filters import ProductFilter


# ── Category CRUD (admin only for write; read is public) ──

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAdminUser()]

    def get_queryset(self):
        # Admins can see deleted categories too via ?include_deleted=true
        qs = Category.objects.annotate(product_count=Count('products'))
        if self.request.user.is_staff and self.request.query_params.get('include_deleted') == 'true':
            qs = Category.all_objects.annotate(product_count=Count('products'))
        return qs

    def perform_destroy(self, instance):
        """Soft-delete instead of hard-delete."""
        instance.delete()   # calls SoftDeleteMixin.delete()

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        if category.products.exists():
            return Response(
                {"error": "Cannot delete category that has products. Remove products first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_destroy(category)
        return Response(
            {"message": f"Category '{category.name}' soft-deleted."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def restore(self, request, pk=None):
        """Restore a soft-deleted category."""
        try:
            category = Category.all_objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
        if not category.is_deleted:
            return Response({"error": "Category is not deleted."}, status=status.HTTP_400_BAD_REQUEST)
        category.restore()
        return Response(
            {"message": f"Category '{category.name}' restored.", "category": CategorySerializer(category).data}
        )


# ── Product CRUD + Search + Filters + Pagination ──

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'name', 'created_at', 'stock']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'product_stats'):
            return [AllowAny()]
        return [IsAdminUser()]

    def get_queryset(self):
        qs = Product.objects.select_related('category').prefetch_related('images')
        # Admins can see soft-deleted products with ?include_deleted=true
        if self.request.user.is_staff and self.request.query_params.get('include_deleted') == 'true':
            qs = Product.all_objects.select_related('category').prefetch_related('images')
        return qs

    def perform_destroy(self, instance):
        """Soft-delete instead of hard-delete."""
        instance.delete()   # calls SoftDeleteMixin.delete()

    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        self.perform_destroy(product)
        return Response(
            {"message": f"Product '{product.name}' soft-deleted."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def restore(self, request, pk=None):
        """Restore a soft-deleted product."""
        try:
            product = Product.all_objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        if not product.is_deleted:
            return Response({"error": "Product is not deleted."}, status=status.HTTP_400_BAD_REQUEST)
        product.restore()
        return Response(
            {"message": f"Product '{product.name}' restored.", "product": ProductSerializer(product).data}
        )


# ── Product Image Upload & Management ──

class ProductImageViewSet(viewsets.ViewSet):
    """
    Product Image management endpoints.

    POST   /products/{product_id}/images/upload/   → upload one or more images
    GET    /products/{product_id}/images/           → list all images for a product
    GET    /products/{product_id}/images/{image_id}/→ retrieve a single image
    DELETE /products/{product_id}/images/{image_id}/→ delete a single image
    POST   /products/{product_id}/images/{image_id}/set-primary/ → mark as primary
    """
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        # Uploading, deleting, and setting primary require admin
        if self.action in ('upload', 'destroy', 'set_primary'):
            return [IsAdminUser()]
        return [AllowAny()]

    # ── Helpers ──

    def _get_product(self, product_id):
        """Fetch product or return None."""
        try:
            return Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return None
        except Exception:
            return None

    def _get_image(self, product, image_id):
        """Fetch a specific image belonging to a product, or return None."""
        try:
            return ProductImage.objects.get(pk=image_id, product=product)
        except ProductImage.DoesNotExist:
            return None
        except Exception:
            return None

    # ── Upload (single or multiple) ──

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request, product_pk=None):
        """
        Upload one or more images for a product.

        Send as multipart/form-data:
          - images: one or more image files (key can be repeated)
          - alt_text: optional string
          - is_primary: optional boolean (applies to first image only)
        """
        product = self._get_product(product_pk)
        if product is None:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        files = request.FILES.getlist('images')
        if not files:
            return Response(
                {"error": "No image files provided. Use the 'images' field."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ProductImageUploadSerializer(data={
            'images': files,
            'alt_text': request.data.get('alt_text', ''),
            'is_primary': request.data.get('is_primary', False),
        })

        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed.", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        alt_text = serializer.validated_data['alt_text']
        is_primary = serializer.validated_data['is_primary']

        created_images = []
        errors = []

        for idx, image_file in enumerate(serializer.validated_data['images']):
            try:
                img = ProductImage(
                    product=product,
                    image=image_file,
                    alt_text=alt_text,
                    is_primary=(is_primary and idx == 0),
                )
                img.full_clean()
                img.save()
                created_images.append(img)
            except Exception as e:
                errors.append({
                    "file": image_file.name,
                    "error": str(e) if not hasattr(e, 'message_dict') else e.message_dict,
                })

        response_data = {
            "message": f"{len(created_images)} image(s) uploaded successfully.",
            "uploaded": ProductImageSerializer(
                created_images, many=True, context={'request': request}
            ).data,
        }
        if errors:
            response_data["errors"] = errors

        return Response(
            response_data,
            status=status.HTTP_201_CREATED if created_images else status.HTTP_400_BAD_REQUEST
        )

    # ── List all images for a product ──

    def list(self, request, product_pk=None):
        """List all images for a product, ordered by primary first."""
        product = self._get_product(product_pk)
        if product is None:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            images = ProductImage.objects.filter(product=product)
            serializer = ProductImageSerializer(
                images, many=True, context={'request': request}
            )
            return Response({
                "product_id": product.id,
                "product_name": product.name,
                "image_count": images.count(),
                "images": serializer.data,
            })
        except Exception:
            return Response(
                {"error": "An unexpected error occurred while fetching images."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ── Retrieve a single image ──

    def retrieve(self, request, product_pk=None, pk=None):
        """Get details of a single product image."""
        product = self._get_product(product_pk)
        if product is None:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        image = self._get_image(product, pk)
        if image is None:
            return Response(
                {"error": "Image not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductImageSerializer(image, context={'request': request})
        return Response(serializer.data)

    # ── Delete a single image ──

    def destroy(self, request, product_pk=None, pk=None):
        """Delete a product image and its files from disk."""
        product = self._get_product(product_pk)
        if product is None:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        image = self._get_image(product, pk)
        if image is None:
            return Response(
                {"error": "Image not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            image_id = image.id
            image.delete()
            return Response(
                {"message": f"Image {image_id} deleted successfully."},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"error": "An unexpected error occurred while deleting the image."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ── Set primary image ──

    @action(detail=True, methods=['post'], url_path='set-primary')
    def set_primary(self, request, product_pk=None, pk=None):
        """Mark a specific image as the primary image for the product."""
        product = self._get_product(product_pk)
        if product is None:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        image = self._get_image(product, pk)
        if image is None:
            return Response(
                {"error": "Image not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            ProductImage.objects.filter(
                product=product, is_primary=True
            ).update(is_primary=False)
            image.is_primary = True
            image.save(update_fields=['is_primary'])
            return Response(
                {
                    "message": f"Image {image.id} is now the primary image.",
                    "image": ProductImageSerializer(image, context={'request': request}).data,
                }
            )
        except Exception:
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ── User Registration (public) ──

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post']

    def get_permissions(self):
        # Anyone can register; listing users requires admin
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]


# ── Cart (authenticated users manage their own cart) ──

class CartViewSet(viewsets.ViewSet):
    """
    Cart operations — always scoped to the authenticated user's own cart.

    GET    /cart/        → view my cart
    POST   /cart/add/    → add item
    POST   /cart/remove/ → remove item
    DELETE /cart/clear/  → clear cart
    """
    permission_classes = [IsAuthenticated]

    def _get_or_create_cart(self, user):
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    def list(self, request):
        """View the authenticated user's cart."""
        cart = self._get_or_create_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        """Add a product to cart. Body: {product: id, quantity: int}"""
        cart = self._get_or_create_cart(request.user)

        serializer = CartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product = serializer.validated_data['product']
        quantity = serializer.validated_data.get('quantity', 1)

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

    @action(detail=False, methods=['post'])
    def remove(self, request):
        """Remove a product from cart. Body: {product: id}"""
        cart = self._get_or_create_cart(request.user)

        product_id = request.data.get('product')
        if not product_id:
            return Response({"error": "Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = CartItem.objects.get(cart=cart, product_id=product_id)
            item.delete()
        except CartItem.DoesNotExist:
            return Response({"error": "Product not in cart."}, status=status.HTTP_404_NOT_FOUND)

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all items from the authenticated user's cart."""
        cart = self._get_or_create_cart(request.user)
        cart.items.all().delete()
        return Response({"message": "Cart cleared."}, status=status.HTTP_200_OK)


# ── Aggregation Stats Endpoint (public) ──

@api_view(['GET'])
@permission_classes([AllowAny])
def product_stats(request):
    """Aggregated product statistics — shows ORM aggregation skills."""
    try:
        stats = Product.objects.aggregate(
            total_products=Count('id'),
            average_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price'),
            total_stock=Sum('stock'),
        )

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
    except Exception:
        return Response(
            {"error": "An unexpected error occurred while fetching stats."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ── External API Integration (public) ──

@api_view(['GET'])
@permission_classes([AllowAny])
def external_exchange_rate(request):
    """Fetches exchange rates from an external API, to be mocked in tests."""
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
        response.raise_for_status()
        data = response.json()
        return Response({"base": data.get("base"), "rates": data.get("rates")})
    except requests.RequestException:
        return Response({"error": "Failed to fetch external data."}, status=status.HTTP_502_BAD_GATEWAY)
