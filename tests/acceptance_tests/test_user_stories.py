import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal
from products.models import Product, Category
from orders.models import Order, OrderItem
from cart.models import Cart, CartItem

User = get_user_model()


class UserStoryTests(APITestCase):
    """Test complete user stories and user journeys"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        self.product = Product.objects.create(
            name='iPhone 15',
            slug='iphone-15',
            price=Decimal('999.99'),
            category=self.category,
            stock=10
        )

    def test_user_registration_and_login_story(self):
        """As a user, I want to register and login to access my account"""
        # User registration
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        response = self.client.post('/api/auth/register/', registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # User login
        login_data = {
            'username': 'newuser',
            'password': 'newpass123'
        }
        response = self.client.post('/api/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_product_browsing_and_search_story(self):
        """As a customer, I want to browse and search products"""
        # Browse products
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Search products
        response = self.client.get('/api/products/?search=iPhone')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Filter by category
        response = self.client.get(f'/api/products/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_complete_purchase_journey(self):
        """As a customer, I want to complete a full purchase journey"""
        self.client.force_authenticate(user=self.user)

        # Add product to cart
        cart_data = {
            'product': self.product.id,
            'quantity': 2
        }
        response = self.client.post('/api/cart/add/', cart_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # View cart
        response = self.client.get('/api/cart/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)

        # Proceed to checkout
        checkout_data = {
            'shipping_address': '123 Main St',
            'payment_method': 'credit_card'
        }
        response = self.client.post('/api/checkout/', checkout_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify order creation
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.total_amount, Decimal('1999.98'))
        self.assertEqual(order.items.count(), 1)
