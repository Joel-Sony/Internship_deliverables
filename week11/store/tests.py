import json
import pytest
import responses
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase

from .models import Category, Product, ProductImage, Cart, CartItem

class ECommerceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password123')
        
        self.category1 = Category.objects.create(name='Electronics', description='Gadgets')
        self.category2 = Category.objects.create(name='Clothing')

        self.product1 = Product.objects.create(
            name='Laptop',
            description='A good laptop',
            price=Decimal('999.99'),
            stock=10,
            category=self.category1
        )
        self.product2 = Product.objects.create(
            name='T-Shirt',
            description='A nice t-shirt',
            price=Decimal('15.50'),
            stock=50,
            category=self.category2
        )

        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(cart=self.cart, product=self.product1, quantity=2)

    # --- MODEL TESTS ---
    def test_category_creation(self):
        self.assertEqual(self.category1.name, 'Electronics')
        self.assertEqual(str(self.category1), 'Electronics')

    def test_product_creation(self):
        self.assertEqual(self.product1.name, 'Laptop')
        self.assertEqual(self.product1.price, Decimal('999.99'))
        self.assertEqual(str(self.product1), 'Laptop')

    def test_cart_and_items(self):
        self.assertEqual(str(self.cart), f"Cart of {self.user.username}")
        self.assertEqual(str(self.cart_item), f"2x Laptop")
        self.assertEqual(self.cart_item.subtotal, Decimal('1999.98'))

    # --- API TESTS ---
    def test_category_list(self):
        url = reverse('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'count' in response.data:
            self.assertEqual(response.data['count'], 2)
        else:
            self.assertEqual(len(response.data), 2)

    def test_product_list_and_search(self):
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assuming pagination or returning directly
        self.assertIn('count', response.data) if 'count' in response.data else self.assertEqual(len(response.data), 2)

        # test search
        response = self.client.get(url, {'search': 'Laptop'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_stats(self):
        url = reverse('product-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['overall']['total_products'], 2)

    # --- CART TESTS ---
    def test_get_cart(self):
        url = reverse('cart-detail', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_to_cart(self):
        url = reverse('cart-add', kwargs={'pk': self.user.id})
        response = self.client.post(url, {'product': self.product2.id, 'quantity': 3}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        cart_item = CartItem.objects.get(cart=self.cart, product=self.product2)
        self.assertEqual(cart_item.quantity, 3)

    def test_add_to_cart_exceeds_stock(self):
        url = reverse('cart-add', kwargs={'pk': self.user.id})
        response = self.client.post(url, {'product': self.product1.id, 'quantity': 20}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_from_cart(self):
        url = reverse('cart-remove', kwargs={'pk': self.user.id})
        response = self.client.post(url, {'product': self.product1.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 0)

    def test_clear_cart(self):
        url = reverse('cart-clear', kwargs={'pk': self.user.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 0)

    # --- EXTERNAL API MOCKING TEST ---
    @responses.activate
    def test_external_exchange_rate(self):
        # Mock the external API
        url = 'https://api.exchangerate-api.com/v4/latest/USD'
        responses.add(
            responses.GET,
            url,
            json={'base': 'USD', 'rates': {'EUR': 0.85, 'GBP': 0.75}},
            status=200
        )

        api_url = reverse('external-rates')
        response = self.client.get(api_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['base'], 'USD')
        self.assertEqual(response.data['rates']['EUR'], 0.85)

    @responses.activate
    def test_external_exchange_rate_failure(self):
        url = 'https://api.exchangerate-api.com/v4/latest/USD'
        responses.add(
            responses.GET,
            url,
            json={'error': 'Not found'},
            status=500
        )

        api_url = reverse('external-rates')
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)

