from io import BytesIO
from decimal import Decimal
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

from .models import Category, Product, ProductImage, Cart, CartItem


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_user(username='user', password='pass1234', is_staff=False):
    return User.objects.create_user(username=username, password=password, is_staff=is_staff)


def create_test_image(name='test.jpg'):
    f = BytesIO()
    Image.new('RGB', (100, 100), 'white').save(f, 'JPEG')
    f.seek(0)
    return SimpleUploadedFile(name, f.read(), content_type='image/jpeg')


# ── Product Image Tests ───────────────────────────────────────────────────────

class ProductImageTests(APITestCase):
    def setUp(self):
        self.admin = make_user(username='admin', is_staff=True)
        self.user = make_user(username='regular')
        self.category = Category.objects.create(name='Cameras')
        self.product = Product.objects.create(
            name='DSLR', price=Decimal('500.00'), stock=5, category=self.category
        )

    # ── Upload ──

    def test_upload_image_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('product-image-upload', kwargs={'product_pk': self.product.pk})
        res = self.client.post(url, {
            'images': create_test_image(), 'alt_text': 'A camera', 'is_primary': True
        }, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductImage.objects.count(), 1)
        img = ProductImage.objects.first()
        self.assertTrue(img.is_primary)
        self.assertTrue(bool(img.thumbnail))  # thumbnail auto-generated

    def test_upload_image_requires_admin(self):
        """Regular authenticated user cannot upload images."""
        self.client.force_authenticate(user=self.user)
        url = reverse('product-image-upload', kwargs={'product_pk': self.product.pk})
        res = self.client.post(url, {'images': create_test_image()}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_upload_image_unauthenticated(self):
        url = reverse('product-image-upload', kwargs={'product_pk': self.product.pk})
        res = self.client.post(url, {'images': create_test_image()}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_image_invalid_product(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('product-image-upload', kwargs={'product_pk': 9999})
        res = self.client.post(url, {'images': create_test_image()}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_upload_no_files_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('product-image-upload', kwargs={'product_pk': self.product.pk})
        res = self.client.post(url, {}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ── List & Retrieve (public) ──

    def test_list_images_public(self):
        ProductImage.objects.create(product=self.product, image=create_test_image('1.jpg'), is_primary=True)
        url = reverse('product-image-list', kwargs={'product_pk': self.product.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['image_count'], 1)

    def test_retrieve_image_public(self):
        img = ProductImage.objects.create(product=self.product, image=create_test_image('1.jpg'))
        url = reverse('product-image-detail', kwargs={'product_pk': self.product.pk, 'pk': img.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], img.pk)

    def test_retrieve_image_wrong_product(self):
        other_cat = Category.objects.create(name='Other')
        other_prod = Product.objects.create(name='X', price=Decimal('1.00'), stock=1, category=other_cat)
        img = ProductImage.objects.create(product=self.product, image=create_test_image('1.jpg'))
        url = reverse('product-image-detail', kwargs={'product_pk': other_prod.pk, 'pk': img.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # ── Set Primary ──

    def test_set_primary_image_as_admin(self):
        img1 = ProductImage.objects.create(product=self.product, image=create_test_image('1.jpg'), is_primary=True)
        img2 = ProductImage.objects.create(product=self.product, image=create_test_image('2.jpg'), is_primary=False)
        self.client.force_authenticate(user=self.admin)
        url = reverse('product-image-set-primary', kwargs={'product_pk': self.product.pk, 'pk': img2.pk})
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        img1.refresh_from_db()
        img2.refresh_from_db()
        self.assertFalse(img1.is_primary)
        self.assertTrue(img2.is_primary)

    def test_set_primary_requires_admin(self):
        img = ProductImage.objects.create(product=self.product, image=create_test_image('1.jpg'))
        self.client.force_authenticate(user=self.user)
        url = reverse('product-image-set-primary', kwargs={'product_pk': self.product.pk, 'pk': img.pk})
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ── Delete ──

    def test_delete_image_as_admin(self):
        img = ProductImage.objects.create(product=self.product, image=create_test_image('1.jpg'))
        self.client.force_authenticate(user=self.admin)
        url = reverse('product-image-detail', kwargs={'product_pk': self.product.pk, 'pk': img.pk})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ProductImage.objects.count(), 0)

    def test_delete_image_requires_admin(self):
        img = ProductImage.objects.create(product=self.product, image=create_test_image('1.jpg'))
        self.client.force_authenticate(user=self.user)
        url = reverse('product-image-detail', kwargs={'product_pk': self.product.pk, 'pk': img.pk})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_nonexistent_image(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('product-image-detail', kwargs={'product_pk': self.product.pk, 'pk': 9999})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


# ── Category + Product Write Permission Edge Cases ────────────────────────────

class PermissionEdgeCaseTests(APITestCase):
    def setUp(self):
        self.admin = make_user(username='admin', is_staff=True)
        self.user = make_user(username='regular')
        self.cat = Category.objects.create(name='Furniture')
        self.prod = Product.objects.create(
            name='Chair', price=Decimal('89.99'), stock=15, category=self.cat
        )

    def test_anonymous_cannot_create_category(self):
        res = self.client.post(reverse('category-list'), {'name': 'New'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_delete_product(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.delete(reverse('product-detail', kwargs={'pk': self.prod.pk}))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_product(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(
            reverse('product-detail', kwargs={'pk': self.prod.pk}),
            {'stock': 99}, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['stock'], 99)

    def test_category_delete_blocked_when_has_products(self):
        """Soft-delete a category that still has active products → 400."""
        self.client.force_authenticate(user=self.admin)
        res = self.client.delete(reverse('category-detail', kwargs={'pk': self.cat.pk}))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_include_deleted_visible_to_admin(self):
        """Admin can see soft-deleted products with ?include_deleted=true."""
        self.prod.delete()  # soft delete
        self.client.force_authenticate(user=self.admin)
        res = self.client.get(reverse('product-list'), {'include_deleted': 'true'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        names = [p['name'] for p in res.data['results']]
        self.assertIn('Chair', names)
