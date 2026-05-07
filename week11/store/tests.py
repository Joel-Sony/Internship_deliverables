import responses
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Product, Cart, CartItem


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_user(username='user', password='pass1234', is_staff=False):
    return User.objects.create_user(username=username, password=password, is_staff=is_staff)


# ── Model Tests ───────────────────────────────────────────────────────────────

class ModelTests(APITestCase):
    def setUp(self):
        self.user = make_user()
        self.cat = Category.objects.create(name='Electronics', description='Gadgets')
        self.prod = Product.objects.create(
            name='Laptop', description='Fast', price=Decimal('999.99'),
            stock=10, category=self.cat
        )
        self.cart = Cart.objects.create(user=self.user)
        self.item = CartItem.objects.create(cart=self.cart, product=self.prod, quantity=2)

    def test_category_str(self):
        self.assertEqual(str(self.cat), 'Electronics')

    def test_product_str(self):
        self.assertEqual(str(self.prod), 'Laptop')

    def test_cart_str(self):
        self.assertEqual(str(self.cart), f'Cart of {self.user.username}')

    def test_cart_item_str_and_subtotal(self):
        self.assertEqual(str(self.item), '2x Laptop')
        self.assertEqual(self.item.subtotal, Decimal('1999.98'))


# ── Soft Delete & Restore Tests ───────────────────────────────────────────────

class SoftDeleteTests(APITestCase):
    def setUp(self):
        self.admin = make_user(username='admin', is_staff=True)
        self.cat = Category.objects.create(name='Gadgets')
        self.prod = Product.objects.create(
            name='Phone', price=Decimal('499.00'), stock=5, category=self.cat
        )

    # ── Product ──

    def test_soft_delete_product(self):
        """DELETE sets is_deleted=True and returns 200; row still exists."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('product-detail', kwargs={'pk': self.prod.pk})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('soft-deleted', res.data['message'])

        # Row still in DB
        self.prod.refresh_from_db()
        self.assertTrue(self.prod.is_deleted)
        self.assertIsNotNone(self.prod.deleted_at)

    def test_soft_deleted_product_hidden_from_list(self):
        """Soft-deleted products don't appear in the public list."""
        self.prod.delete()  # soft delete
        res = self.client.get(reverse('product-list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        names = [p['name'] for p in res.data['results']]
        self.assertNotIn('Phone', names)

    def test_restore_product(self):
        """Admin can restore a soft-deleted product."""
        self.prod.delete()
        self.client.force_authenticate(user=self.admin)
        url = reverse('product-restore', kwargs={'pk': self.prod.pk})
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.prod.refresh_from_db()
        self.assertFalse(self.prod.is_deleted)
        self.assertIsNone(self.prod.deleted_at)

    def test_restore_non_deleted_product_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('product-restore', kwargs={'pk': self.prod.pk})
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Category ──

    def test_soft_delete_category_with_no_products(self):
        empty_cat = Category.objects.create(name='Empty')
        self.client.force_authenticate(user=self.admin)
        url = reverse('category-detail', kwargs={'pk': empty_cat.pk})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        empty_cat.refresh_from_db()
        self.assertTrue(empty_cat.is_deleted)

    def test_delete_category_with_products_blocked(self):
        """Cannot soft-delete a category that still has active products."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('category-detail', kwargs={'pk': self.cat.pk})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restore_category(self):
        empty_cat = Category.objects.create(name='Temp')
        empty_cat.delete()
        self.client.force_authenticate(user=self.admin)
        url = reverse('category-restore', kwargs={'pk': empty_cat.pk})
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        empty_cat.refresh_from_db()
        self.assertFalse(empty_cat.is_deleted)


# ── Auth Tests ────────────────────────────────────────────────────────────────

class AuthTests(APITestCase):
    def setUp(self):
        self.user = make_user(username='joel', password='secret99')

    def test_login_returns_tokens(self):
        res = self.client.post(reverse('token-obtain-pair'), {
            'username': 'joel', 'password': 'secret99'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

    def test_login_bad_credentials(self):
        res = self.client.post(reverse('token-obtain-pair'), {
            'username': 'joel', 'password': 'wrong'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        login = self.client.post(reverse('token-obtain-pair'), {
            'username': 'joel', 'password': 'secret99'
        }, format='json')
        res = self.client.post(reverse('token-refresh'), {
            'refresh': login.data['refresh']
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)

    def test_register_user_public(self):
        """Anyone can POST /users/ to register."""
        res = self.client.post(reverse('user-list'), {
            'username': 'newuser', 'email': 'new@example.com', 'password': 'pass1234'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_list_users_requires_admin(self):
        self.client.force_authenticate(user=self.user)  # regular user
        res = self.client.get(reverse('user-list'))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_protected_endpoint_unauthenticated(self):
        """Cart requires auth — unauthenticated request must get 401."""
        res = self.client.get(reverse('cart-detail'))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ── Category API Tests ────────────────────────────────────────────────────────

class CategoryAPITests(APITestCase):
    def setUp(self):
        self.admin = make_user(username='admin', is_staff=True)
        self.user = make_user(username='regular')
        self.cat1 = Category.objects.create(name='Electronics')
        self.cat2 = Category.objects.create(name='Clothing')

    def test_list_categories_public(self):
        res = self.client.get(reverse('category-list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_category_requires_admin(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post(reverse('category-list'), {'name': 'Books'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_category_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(reverse('category-list'), {'name': 'Sports'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'Sports')

    def test_duplicate_category_name_rejected(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(reverse('category-list'), {'name': 'electronics'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# ── Product API Tests ─────────────────────────────────────────────────────────

class ProductAPITests(APITestCase):
    def setUp(self):
        self.admin = make_user(username='admin', is_staff=True)
        self.cat = Category.objects.create(name='Tech')
        self.prod = Product.objects.create(
            name='Tablet', price=Decimal('299.99'), stock=20, category=self.cat
        )

    def test_list_products_public(self):
        res = self.client.get(reverse('product-list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_search_products(self):
        res = self.client.get(reverse('product-list'), {'search': 'Tablet'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'][0]['name'], 'Tablet')

    def test_create_product_requires_admin(self):
        res = self.client.post(reverse('product-list'), {
            'name': 'Headphones', 'price': '49.99', 'stock': 10, 'category': self.cat.pk
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_product_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(reverse('product-list'), {
            'name': 'Headphones', 'price': '49.99', 'stock': 10, 'category': self.cat.pk
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_product_stats_public(self):
        res = self.client.get(reverse('product-stats'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('overall', res.data)
        self.assertIn('by_category', res.data)


# ── Cart Tests ────────────────────────────────────────────────────────────────

class CartTests(APITestCase):
    def setUp(self):
        self.user = make_user()
        self.cat = Category.objects.create(name='Food')
        self.prod1 = Product.objects.create(
            name='Apple', price=Decimal('1.00'), stock=50, category=self.cat
        )
        self.prod2 = Product.objects.create(
            name='Banana', price=Decimal('0.50'), stock=30, category=self.cat
        )
        self.client.force_authenticate(user=self.user)

    def test_view_empty_cart(self):
        res = self.client.get(reverse('cart-detail'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['item_count'], 0)

    def test_add_item_to_cart(self):
        res = self.client.post(reverse('cart-add'), {
            'product': self.prod1.pk, 'quantity': 3
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['item_count'], 1)

    def test_add_same_item_accumulates_quantity(self):
        self.client.post(reverse('cart-add'), {'product': self.prod1.pk, 'quantity': 2}, format='json')
        self.client.post(reverse('cart-add'), {'product': self.prod1.pk, 'quantity': 3}, format='json')
        res = self.client.get(reverse('cart-detail'))
        self.assertEqual(res.data['items'][0]['quantity'], 5)

    def test_add_item_exceeds_stock(self):
        res = self.client.post(reverse('cart-add'), {
            'product': self.prod1.pk, 'quantity': 999
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_item_from_cart(self):
        self.client.post(reverse('cart-add'), {'product': self.prod1.pk, 'quantity': 1}, format='json')
        res = self.client.post(reverse('cart-remove'), {'product': self.prod1.pk}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['item_count'], 0)

    def test_remove_item_not_in_cart(self):
        res = self.client.post(reverse('cart-remove'), {'product': self.prod1.pk}, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_missing_product_id(self):
        res = self.client.post(reverse('cart-remove'), {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_clear_cart(self):
        self.client.post(reverse('cart-add'), {'product': self.prod1.pk, 'quantity': 1}, format='json')
        self.client.post(reverse('cart-add'), {'product': self.prod2.pk, 'quantity': 2}, format='json')
        res = self.client.delete(reverse('cart-clear'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        cart_res = self.client.get(reverse('cart-detail'))
        self.assertEqual(cart_res.data['item_count'], 0)

    def test_cart_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        res = self.client.get(reverse('cart-detail'))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ── External API Tests ────────────────────────────────────────────────────────

class ExternalAPITests(APITestCase):
    @responses.activate
    def test_external_exchange_rate_success(self):
        responses.add(
            responses.GET,
            'https://api.exchangerate-api.com/v4/latest/USD',
            json={'base': 'USD', 'rates': {'EUR': 0.85, 'GBP': 0.75}},
            status=200
        )
        res = self.client.get(reverse('external-rates'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['base'], 'USD')
        self.assertIn('EUR', res.data['rates'])

    @responses.activate
    def test_external_exchange_rate_failure(self):
        responses.add(
            responses.GET,
            'https://api.exchangerate-api.com/v4/latest/USD',
            json={'error': 'server error'},
            status=500
        )
        res = self.client.get(reverse('external-rates'))
        self.assertEqual(res.status_code, status.HTTP_502_BAD_GATEWAY)
