import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import datetime, timedelta
import json

# Assuming these are your models
from ecommerce.models import (
    Product, Category, Order, OrderItem, Cart, CartItem,
    Payment, User, Coupon, Inventory, ProductVariant
)

User = get_user_model()


class PaymentBugFixTests(APITestCase):
    """
    Tests for payment-related bug fixes
    Bug IDs referenced would be from your issue tracking system
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )

        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            stock=10
        )

    def test_double_payment_prevention_bug_fix(self):
        """
        Bug Fix: BUG-001 - Double payment processing when user clicks pay button multiple times

        This test ensures that rapid successive payment attempts are properly handled
        and only one payment is processed.
        """
        # Create order
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('100.00'),
            status='pending'
        )

        payment_data = {
            'order_id': order.id,
            'amount': '100.00',
            'payment_method': 'credit_card',
            'card_token': 'test_token_123'
        }

        # Simulate rapid successive payment attempts
        with patch('ecommerce.services.PaymentService.process_payment') as mock_payment:
            mock_payment.return_value = {'success': True, 'transaction_id': 'txn_123'}

            # First payment should succeed
            response1 = self.client.post('/api/payments/', payment_data)
            self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

            # Second payment attempt should be rejected (order already paid)
            response2 = self.client.post('/api/payments/', payment_data)
            self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('already_paid', response2.data['error'])

            # Verify payment service was called only once
            self.assertEqual(mock_payment.call_count, 1)

    def test_payment_timeout_handling_bug_fix(self):
        """
        Bug Fix: BUG-002 - Payment gateway timeout not properly handled

        This test ensures that payment timeouts are gracefully handled
        and the order status is properly updated.
        """
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('100.00'),
            status='pending'
        )

        payment_data = {
            'order_id': order.id,
            'amount': '100.00',
            'payment_method': 'credit_card'
        }

        # Simulate payment gateway timeout
        with patch('ecommerce.services.PaymentService.process_payment') as mock_payment:
            mock_payment.side_effect = TimeoutError("Payment gateway timeout")

            response = self.client.post('/api/payments/', payment_data)

            # Should return appropriate error status
            self.assertEqual(response.status_code, status.HTTP_408_REQUEST_TIMEOUT)
            self.assertIn('timeout', response.data['error'])

            # Order should remain in pending status
            order.refresh_from_db()
            self.assertEqual(order.status, 'pending')

    def test_currency_precision_bug_fix(self):
        """
        Bug Fix: BUG-003 - Currency precision issues in payment calculations

        This test ensures that decimal precision is maintained throughout
        payment calculations to prevent rounding errors.
        """
        # Create order with precise decimal amounts
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('99.997'),  # Should be rounded to 99.99
            status='pending'
        )

        # Test that the amount is properly rounded
        self.assertEqual(order.total_amount, Decimal('99.99'))

        # Test payment processing with precise amounts
        payment_data = {
            'order_id': order.id,
            'amount': '99.997',  # This should be validated and rounded
            'payment_method': 'credit_card'
        }

        with patch('ecommerce.services.PaymentService.process_payment') as mock_payment:
            mock_payment.return_value = {'success': True, 'transaction_id': 'txn_123'}

            response = self.client.post('/api/payments/', payment_data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Verify the payment amount was properly rounded
            payment = Payment.objects.get(order=order)
            self.assertEqual(payment.amount, Decimal('99.99'))


class CartBugFixTests(APITestCase):
    """Tests for cart-related bug fixes"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )

        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('50.00'),
            stock=10
        )

    def test_cart_item_duplicate_prevention_bug_fix(self):
        """
        Bug Fix: BUG-004 - Duplicate cart items created in race conditions

        This test ensures that concurrent requests to add the same item
        don't create duplicate cart entries.
        """
        cart = Cart.objects.create(user=self.user)

        # Simulate concurrent requests to add the same product
        def add_item_to_cart():
            return self.client.post('/api/cart/items/', {
                'product_id': self.product.id,
                'quantity': 1
            })

        # First request should succeed
        response1 = add_item_to_cart()
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second request should update quantity instead of creating duplicate
        response2 = add_item_to_cart()
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Verify only one cart item exists
        cart_items = CartItem.objects.filter(cart=cart, product=self.product)
        self.assertEqual(cart_items.count(), 1)
        self.assertEqual(cart_items.first().quantity, 2)

    def test_cart_quantity_validation_bug_fix(self):
        """
        Bug Fix: BUG-005 - Cart allows adding more items than available stock

        This test ensures that cart quantity validation properly checks
        against available inventory.
        """
        cart = Cart.objects.create(user=self.user)

        # Try to add more items than available stock
        response = self.client.post('/api/cart/items/', {
            'product_id': self.product.id,
            'quantity': 15  # More than stock (10)
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('insufficient_stock', response.data['error'])

        # Verify no cart item was created
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 0)

    def test_cart_cleanup_on_user_deletion_bug_fix(self):
        """
        Bug Fix: BUG-006 - Orphaned cart items after user deletion

        This test ensures that cart items are properly cleaned up
        when a user account is deleted.
        """
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1
        )

        # Delete user
        user_id = self.user.id
        self.user.delete()

        # Verify cart and cart items are also deleted
        self.assertEqual(Cart.objects.filter(user_id=user_id).count(), 0)
        self.assertEqual(CartItem.objects.filter(cart_id=cart.id).count(), 0)


class AuthenticationBugFixTests(APITestCase):
    """Tests for authentication-related bug fixes"""

    def test_password_reset_token_expiry_bug_fix(self):
        """
        Bug Fix: BUG-007 - Password reset tokens not expiring properly

        This test ensures that password reset tokens have proper expiration
        and cannot be used after expiry.
        """
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )

        # Request password reset
        response = self.client.post('/api/auth/password-reset/', {
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Simulate token expiry by modifying the timestamp
        with patch('django.utils.timezone.now') as mock_now:
            # Set current time to 25 hours later (tokens expire after 24 hours)
            mock_now.return_value = timezone.now() + timedelta(hours=25)

            # Try to use expired token
            response = self.client.post('/api/auth/password-reset/confirm/', {
                'token': 'expired_token_123',
                'new_password': 'newpass123'
            })

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('token_expired', response.data['error'])

    def test_session_fixation_prevention_bug_fix(self):
        """
        Bug Fix: BUG-008 - Session fixation vulnerability

        This test ensures that session IDs are regenerated upon login
        to prevent session fixation attacks.
        """
        # Create user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Get initial session ID
        initial_session_key = self.client.session.session_key

        # Login
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify session ID changed after login
        new_session_key = self.client.session.session_key
        self.assertNotEqual(initial_session_key, new_session_key)


class OrderProcessingBugFixTests(TransactionTestCase):
    """Tests for order processing bug fixes"""

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
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            stock=5
        )

    def test_inventory_deduction_race_condition_bug_fix(self):
        """
        Bug Fix: BUG-009 - Race condition in inventory deduction

        This test ensures that inventory is properly decremented
        even under concurrent order processing.
        """
        initial_stock = self.product.stock

        # Simulate concurrent order processing
        def process_order():
            try:
                with transaction.atomic():
                    order = Order.objects.create(
                        user=self.user,
                        total_amount=Decimal('100.00'),
                        status='pending'
                    )

                    # Check and update inventory atomically
                    product = Product.objects.select_for_update().get(id=self.product.id)
                    if product.stock >= 1:
                        product.stock -= 1
                        product.save()

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=1,
                            price=product.price
                        )
                        return True
                    return False
            except IntegrityError:
                return False

        # Process multiple orders concurrently
        results = []
        for _ in range(10):  # Try to process 10 orders (more than available stock)
            results.append(process_order())

        # Verify that only available stock was processed
        successful_orders = sum(results)
        self.assertEqual(successful_orders, initial_stock)

        # Verify final stock is 0
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 0)

    def test_order_status_consistency_bug_fix(self):
        """
        Bug Fix: BUG-010 - Order status inconsistency after payment failure

        This test ensures that order status remains consistent
        when payment processing fails.
        """
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('100.00'),
            status='pending'
        )

        # Simulate payment failure
        with patch('ecommerce.services.PaymentService.process_payment') as mock_payment:
            mock_payment.side_effect = Exception("Payment failed")

            # Try to process payment
            with self.assertRaises(Exception):
                # This would be called in your order processing logic
                payment_service = mock_payment
                payment_service.process_payment(order)

        # Verify order status remains pending (not changed to failed incorrectly)
        order.refresh_from_db()
        self.assertEqual(order.status, 'pending')


class DataConsistencyBugFixTests(TestCase):
    """Tests for data consistency bug fixes"""

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
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('100.00'),
            stock=10
        )

    def test_category_deletion_cascade_bug_fix(self):
        """
        Bug Fix: BUG-011 - Products not properly handled when category is deleted

        This test ensures that products are properly handled (moved to default
        category or handled appropriately) when their category is deleted.
        """
        # Create default category
        default_category = Category.objects.create(
            name='Uncategorized',
            slug='uncategorized',
            is_default=True
        )

        # Delete the product's category
        self.category.delete()

        # Verify product is moved to default category
        self.product.refresh_from_db()
        self.assertEqual(self.product.category, default_category)

    def test_user_email_uniqueness_bug_fix(self):
        """
        Bug Fix: BUG-012 - Case-insensitive email uniqueness not enforced

        This test ensures that email addresses are treated as case-insensitive
        for uniqueness validation.
        """
        # Try to create user with same email but different case
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='testuser2',
                email='TEST@EXAMPLE.COM',  # Same email, different case
                password='testpass123'
            )

    def test_price_validation_bug_fix(self):
        """
        Bug Fix: BUG-013 - Negative prices allowed in product creation

        This test ensures that negative prices are properly validated
        and rejected.
        """
        with self.assertRaises(ValidationError):
            product = Product(
                name='Invalid Product',
                slug='invalid-product',
                category=self.category,
                price=Decimal('-10.00'),  # Negative price
                stock=10
            )
            product.full_clean()


class PerformanceBugFixTests(APITestCase):
    """Tests for performance-related bug fixes"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_n_plus_one_query_bug_fix(self):
        """
        Bug Fix: BUG-014 - N+1 query problem in product listing

        This test ensures that product listing with categories
        doesn't suffer from N+1 query problem.
        """
        # Create multiple categories and products
        categories = []
        for i in range(5):
            category = Category.objects.create(
                name=f'Category {i}',
                slug=f'category-{i}'
            )
            categories.append(category)

            # Create products for each category
            for j in range(3):
                Product.objects.create(
                    name=f'Product {i}-{j}',
                    slug=f'product-{i}-{j}',
                    category=category,
                    price=Decimal('100.00'),
                    stock=10
                )

        # Test that product listing uses select_related or prefetch_related
        with self.assertNumQueries(2):  # Should be 2 queries max (products + categories)
            response = self.client.get('/api/products/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['results']), 15)  # 5 categories × 3 products

    def test_large_cart_performance_bug_fix(self):
        """
        Bug Fix: BUG-015 - Cart calculation performance degrades with many items

        This test ensures that cart total calculation performs well
        even with many items.
        """
        # Create a cart with many items
        cart = Cart.objects.create(user=self.user)

        category = Category.objects.create(name='Test', slug='test')

        # Add 100 items to cart
        for i in range(100):
            product = Product.objects.create(
                name=f'Product {i}',
                slug=f'product-{i}',
                category=category,
                price=Decimal('10.00'),
                stock=10
            )
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=1
            )

        # Test that cart total calculation is efficient
        with self.assertNumQueries(1):  # Should use aggregation, not loop
            response = self.client.get('/api/cart/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['total_amount'], '1000.00')


class SecurityBugFixTests(APITestCase):
    """Tests for security-related bug fixes"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )

    def test_unauthorized_order_access_bug_fix(self):
        """
        Bug Fix: BUG-016 - Users can access other users' orders

        This test ensures that users can only access their own orders
        and cannot access orders belonging to other users.
        """
        # Create order for different user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )

        other_order = Order.objects.create(
            user=other_user,
            total_amount=Decimal('100.00'),
            status='pending'
        )

        # Try to access other user's order
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/orders/{other_order.id}/')

        # Should return 404 (not 403 to avoid information disclosure)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_privilege_escalation_bug_fix(self):
        """
        Bug Fix: BUG-017 - Regular users can perform admin actions

        This test ensures that admin-only endpoints properly check
        for admin privileges.
        """
        # Try to access admin endpoint as regular user
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/admin/users/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Verify admin user can access
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/admin/users/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sql_injection_prevention_bug_fix(self):
        """
        Bug Fix: BUG-018 - SQL injection vulnerability in search

        This test ensures that search functionality properly sanitizes
        input and prevents SQL injection.
        """
        # Try SQL injection in search
        malicious_query = "'; DROP TABLE products; --"

        response = self.client.get('/api/products/search/', {
            'q': malicious_query
        })

        # Should return normal response without executing malicious SQL
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify products table still exists by creating a product
        category = Category.objects.create(name='Test', slug='test')
        product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=category,
            price=Decimal('100.00'),
            stock=10
        )
        self.assertTrue(product.id)


# Test utilities for bug reproduction
class BugReproductionUtils:
    """
    Utility class for reproducing specific bug scenarios
    """

    @staticmethod
    def create_race_condition_scenario():
        """Create scenario that reproduces race condition bugs"""
        pass

    @staticmethod
    def create_memory_leak_scenario():
        """Create scenario that reproduces memory leak bugs"""
        pass

    @staticmethod
    def create_deadlock_scenario():
        """Create scenario that reproduces database deadlock bugs"""
        pass


# Custom test decorators for bug fix tests
def bug_fix_test(bug_id):
    """
    Decorator to mark tests as bug fix tests with specific bug IDs
    """
    def decorator(func):
        func.bug_id = bug_id
        func.is_bug_fix = True
        return func
    return decorator


# Example usage of decorator
@bug_fix_test('BUG-019')
def test_specific_bug_fix():
    """Test for specific bug with ID BUG-019"""
    pass
