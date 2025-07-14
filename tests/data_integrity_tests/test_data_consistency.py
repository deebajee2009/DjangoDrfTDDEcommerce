import pytest
from django.test import TestCase, TransactionTestCase
from django.db import transaction, IntegrityError
from decimal import Decimal
from django.contrib.auth import get_user_model
from products.models import Product, Category
from orders.models import Order, OrderItem
from cart.models import Cart, CartItem


User = get_user_model()


class DataConsistencyTests(TransactionTestCase):
    """Test data consistency across the application"""

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

    def test_foreign_key_consistency(self):
        """Test foreign key relationships maintain consistency"""
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('999.99'),
            status='pending'
        )

        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=Decimal('999.99')
        )

        # Verify relationships
        self.assertEqual(order_item.order, order)
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order.items.count(), 1)

    def test_cascade_deletion_consistency(self):
        """Test cascade deletion maintains consistency"""
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('999.99'),
            status='pending'
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=Decimal('999.99')
        )

        # Delete order should cascade to order items
        order.delete()
        self.assertEqual(OrderItem.objects.count(), 0)

    def test_unique_constraint_consistency(self):
        """Test unique constraints are enforced"""
        # Try to create duplicate category slug
        with self.assertRaises(IntegrityError):
            Category.objects.create(
                name='Electronics Duplicate',
                slug='electronics'  # Same slug as existing category
            )

    def test_transaction_consistency(self):
        """Test transaction rollback maintains consistency"""
        initial_stock = self.product.stock

        try:
            with transaction.atomic():
                # Decrease stock
                self.product.stock -= 5
                self.product.save()

                # Simulate error that causes rollback
                raise Exception("Simulated error")
        except Exception:
            pass

        # Verify stock was rolled back
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock)

    def test_cart_product_consistency(self):
        """Test cart-product relationship consistency"""
        cart = Cart.objects.create(user=self.user)

        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )

        # Verify total calculation consistency
        expected_total = self.product.price * 2
        calculated_total = cart.get_total()

        self.assertEqual(calculated_total, expected_total)

    def test_order_total_consistency(self):
        """Test order total calculation consistency"""
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('0.00'),
            status='pending'
        )

        # Add items
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price=Decimal('999.99')
        )

        # Recalculate total
        order.recalculate_total()

        expected_total = Decimal('1999.98')
        self.assertEqual(order.total_amount, expected_total)
