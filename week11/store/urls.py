from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'users', views.UserViewSet, basename='user')

# Cart uses /api/cart/ (always scoped to the authenticated user)
cart_list = views.CartViewSet.as_view({'get': 'list'})
cart_add = views.CartViewSet.as_view({'post': 'add'})
cart_remove = views.CartViewSet.as_view({'post': 'remove'})
cart_clear = views.CartViewSet.as_view({'delete': 'clear'})

# Nested image routes under /products/{product_id}/images/
image_list = views.ProductImageViewSet.as_view({'get': 'list'})
image_detail = views.ProductImageViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})
image_upload = views.ProductImageViewSet.as_view({'post': 'upload'})
image_set_primary = views.ProductImageViewSet.as_view({'post': 'set_primary'})

urlpatterns = [
    path('', include(router.urls)),

    # ── Auth endpoints ──
    path('auth/login/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # ── Cart (authenticated user's own cart) ──
    path('cart/', cart_list, name='cart-detail'),
    path('cart/add/', cart_add, name='cart-add'),
    path('cart/remove/', cart_remove, name='cart-remove'),
    path('cart/clear/', cart_clear, name='cart-clear'),

    # ── Stats & external ──
    path('stats/', views.product_stats, name='product-stats'),
    path('external-rates/', views.external_exchange_rate, name='external-rates'),

    # ── Product Image endpoints ──
    path(
        'products/<int:product_pk>/images/',
        image_list,
        name='product-image-list',
    ),
    path(
        'products/<int:product_pk>/images/upload/',
        image_upload,
        name='product-image-upload',
    ),
    path(
        'products/<int:product_pk>/images/<int:pk>/',
        image_detail,
        name='product-image-detail',
    ),
    path(
        'products/<int:product_pk>/images/<int:pk>/set-primary/',
        image_set_primary,
        name='product-image-set-primary',
    ),
]
