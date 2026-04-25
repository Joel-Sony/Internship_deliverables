from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from django.db.models import Count, Avg, Min, Max, Sum

from .models import Category, Product, ProductImage, Cart, CartItem
from .serializers import (
    CategorySerializer, ProductSerializer,
    ProductImageSerializer, ProductImageUploadSerializer,
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
    queryset = Product.objects.select_related('category').prefetch_related('images').all()
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    search_fields = ['name', 'description']  # ?search=keyword
    ordering_fields = ['price', 'name', 'created_at', 'stock']  # ?ordering=price
    ordering = ['-created_at']  # default ordering


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

        # Collect files — DRF's request.FILES is a MultiValueDict
        files = request.FILES.getlist('images')
        if not files:
            return Response(
                {"error": "No image files provided. Use the 'images' field."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Run through serializer validation
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
                img = ProductImage.upload_to_cloudinary(
                    file=image_file,
                    product=product,
                    alt_text=alt_text,
                    is_primary=(is_primary and idx == 0),
                )
                created_images.append(img)
            except Exception as e:
                errors.append({
                    "file": image_file.name,
                    "error": str(e),
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
            image.delete()  # model's delete() cleans up files
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
            # Un-mark all others and set this one
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
    try:
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
    except Exception:
        return Response(
            {"error": "An unexpected error occurred while fetching stats."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
