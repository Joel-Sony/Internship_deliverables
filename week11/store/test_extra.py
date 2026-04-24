import json
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from decimal import Decimal

from .models import Category, Product, ProductImage, Cart, CartItem

def create_test_image(name='test_image.jpg'):
    f = BytesIO()
    image = Image.new('RGB', (100, 100), 'white')
    image.save(f, 'JPEG')
    f.seek(0)
    return SimpleUploadedFile(name, f.read(), content_type='image/jpeg')

class ProductImageTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Cameras')
        self.product = Product.objects.create(
            name='DSLR',
            price=Decimal('500.00'),
            category=self.category,
            stock=5
        )
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_upload_image(self):
        url = reverse('product-image-upload', kwargs={'product_pk': self.product.id})
        image_file = create_test_image()
        response = self.client.post(url, {'images': image_file, 'alt_text': 'A camera', 'is_primary': True}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductImage.objects.count(), 1)
        
        # Test model thumbnail generation logic
        img_obj = ProductImage.objects.first()
        self.assertTrue(img_obj.is_primary)
        self.assertTrue(bool(img_obj.thumbnail))

    def test_list_and_retrieve_images(self):
        img_obj = ProductImage.objects.create(
            product=self.product,
            image=create_test_image('1.jpg'),
            is_primary=True
        )
        url_list = reverse('product-image-list', kwargs={'product_pk': self.product.id})
        res_list = self.client.get(url_list)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(res_list.data['image_count'], 1)

        url_detail = reverse('product-image-detail', kwargs={'product_pk': self.product.id, 'pk': img_obj.id})
        res_detail = self.client.get(url_detail)
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)

    def test_set_primary_image(self):
        img1 = ProductImage.objects.create(product=self.product, image=create_test_image('1.jpg'), is_primary=True)
        img2 = ProductImage.objects.create(product=self.product, image=create_test_image('2.jpg'), is_primary=False)

        url = reverse('product-image-set-primary', kwargs={'product_pk': self.product.id, 'pk': img2.id})
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        img1.refresh_from_db()
        img2.refresh_from_db()
        self.assertFalse(img1.is_primary)
        self.assertTrue(img2.is_primary)

    def test_delete_image(self):
        img1 = ProductImage.objects.create(product=self.product, image=create_test_image('1.jpg'))
        url = reverse('product-image-detail', kwargs={'product_pk': self.product.id, 'pk': img1.id})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ProductImage.objects.count(), 0)

    def test_upload_invalid_product(self):
        url = reverse('product-image-upload', kwargs={'product_pk': 9999})
        image_file = create_test_image()
        response = self.client.post(url, {'images': image_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class AdditionalViewsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.category = Category.objects.create(name='Food')
        self.product = Product.objects.create(name='Apple', price=Decimal('1.00'), stock=100, category=self.category)
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_remove_nonexistent(self):
        url = reverse('cart-remove', kwargs={'pk': self.user.id})
        res = self.client.post(url, {'product': self.product.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_category_delete_with_products(self):
        url = reverse('category-detail', kwargs={'pk': self.category.id})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cart_not_found(self):
        url = reverse('cart-detail', kwargs={'pk': 9999})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
