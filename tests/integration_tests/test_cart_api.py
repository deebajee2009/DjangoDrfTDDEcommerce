from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from apps.users.models import User
from apps.products.models import Product

class CartIntegrationTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.product = Product.objects.create(name='Laptop', price=1200.00, inventory=10)
        self.client.login(username='testuser', password='testpassword')
        self.add_to_cart_url = reverse('add-to-cart')

    def test_add_to_cart_success(self):
        """
        Ensure a product can be successfully added to the cart.
        """
        data = {'product_id': self.product.id, 'quantity': 1}
        response = self.client.post(self.add_to_cart_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.user.cart.items.count(), 1)

    def test_add_to_cart_insufficient_inventory(self):
        """
        Test adding a product with insufficient inventory to the cart.
        """
        data = {'product_id': self.product.id, 'quantity': 11}
        response = self.client.post(self.add_to_cart_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
