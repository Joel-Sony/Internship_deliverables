from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'carts', views.CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', views.product_stats, name='product-stats'),
]
