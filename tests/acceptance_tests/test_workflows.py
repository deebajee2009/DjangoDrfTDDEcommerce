import pytest
from django.test import TestCase, TransactionTestCase
from django.db import transaction
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal
from unittest.mock import patch, Mock
from products.models import Product, Category
from orders.models import Order, OrderItem
from cart.models import Cart, CartItem
from payments.models import Payment

User = get_user_model()


class WorkflowTests(APITestCase):
    """Test complex workflows and business processes"""

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

    def test_order_processing_workflow(self):
        """Test complete order processing workflow"""
        self.client.force_authenticate(user=self.user)

        # Step 1: Add to cart
        cart_data = {'product': self.product.id, 'quantity': 1}
        response = self.client.post('/api/cart/add/', cart_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Step 2: Checkout
        checkout_data = {
            'shipping_address': '123 Main St',
            'payment_method': 'credit_card'
        }
        response = self.client.post('/api/checkout/', checkout_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.data['id']

        # Step 3: Process payment
        payment_data = {
            'order': order_id,
            'amount': '999.99',
            'payment_method': 'credit_card'
        }
        with patch('payments.services.PaymentProcessor.process_payment') as mock_payment:
            mock_payment.return_value = {'status': 'success', 'transaction_id': 'txn_123'}
            response = self.client.post('/api/payments/', payment_data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Step 4: Verify order status
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, 'paid')

        # Step 5: Fulfill order
        response = self.client.post(f'/api/orders/{order_id}/fulfill/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.status, 'fulfilled')

    def test_inventory_management_workflow(self):
        """Test inventory management workflow"""
        self.client.force_authenticate(user=self.user)

        # Check initial stock
        self.assertEqual(self.product.stock, 10)

        # Place order
        cart_data = {'product': self.product.id, 'quantity': 3}
        self.client.post('/api/cart/add/', cart_data)

        checkout_data = {
            'shipping_address': '123 Main St',
            'payment_method': 'credit_card'
        }
        response = self.client.post('/api/checkout/', checkout_data)
        order_id = response.data['id']

        # Verify stock reservation
        self.product.refresh_from_db()
        self.assertEqual(self.product.reserved_stock, 3)

        # Process payment and fulfill
        with patch('payments.services.PaymentProcessor.process_payment') as mock_payment:
            mock_payment.return_value = {'status': 'success', 'transaction_id': 'txn_123'}
            self.client.post('/api/payments/', {'order': order_id, 'amount': '2999.97'})
            self.client.post(f'/api/orders/{order_id}/fulfill/')

        # Verify final stock
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)
        self.assertEqual(self.product.reserved_stock, 0)

    def test_return_and_refund_workflow(self):
        """Test return and refund workflow"""
        self.client.force_authenticate(user=self.user)

        # Create completed order
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('999.99'),
            status='delivered'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=Decimal('999.99')
        )

        # Request return
        return_data = {
            'order': order.id,
            'reason': 'defective',
            'items': [{'product': self.product.id, 'quantity': 1}]
        }
        response = self.client.post('/api/returns/', return_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return_id = response.data['id']

        # Approve return
        response = self.client.post(f'/api/returns/{return_id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Process refund
        with patch('payments.services.PaymentProcessor.process_refund') as mock_refund:
            mock_refund.return_value = {'status': 'success', 'refund_id': 'ref_123'}
            response = self.client.post(f'/api/returns/{return_id}/refund/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify inventory restoration
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 11)  # Original 10 + 1 returned
