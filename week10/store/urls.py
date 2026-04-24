from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'carts', views.CartViewSet, basename='cart')

# Nested image routes under /products/{product_id}/images/
image_list = views.ProductImageViewSet.as_view({
    'get': 'list',
})
image_detail = views.ProductImageViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy',
})
image_upload = views.ProductImageViewSet.as_view({
    'post': 'upload',
})
image_set_primary = views.ProductImageViewSet.as_view({
    'post': 'set_primary',
})

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', views.product_stats, name='product-stats'),

    # Product Image endpoints
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
