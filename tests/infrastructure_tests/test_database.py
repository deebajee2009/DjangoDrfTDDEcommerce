import pytest
from django.test import TestCase, TransactionTestCase
from django.db import connection, transaction
from django.contrib.auth import get_user_model
from django.core.management import call_command
from decimal import Decimal
from products.models import Product, Category
from orders.models import Order, OrderItem
import threading
import time

User = get_user_model()


class DatabaseTests(TestCase):
    """Test database operations and performance"""

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

    def test_database_connection(self):
        """Test database connection is working"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)

    def test_transaction_isolation(self):
        """Test database transaction isolation"""
        with transaction.atomic():
            product = Product.objects.create(
                name='Test Product',
                slug='test-product',
                price=Decimal('99.99'),
                category=self.category,
                stock=10
            )

            # Verify product exists in current transaction
            self.assertTrue(Product.objects.filter(id=product.id).exists())

    def test_database_indexes(self):
        """Test database indexes are working"""
        # Create multiple products
        for i in range(100):
            Product.objects.create(
                name=f'Product {i}',
                slug=f'product-{i}',
                price=Decimal('99.99'),
                category=self.category,
                stock=10
            )

        # Query should be fast with proper indexing
        import time
        start_time = time.time()

        products = Product.objects.filter(category=self.category)[:10]
        list(products)  # Force evaluation

        end_time = time.time()
        query_time = end_time - start_time

        # Should complete in reasonable time (less than 1 second)
        self.assertLess(query_time, 1.0)

    def test_database_constraints(self):
        """Test database constraints are enforced"""
        # Test unique constraint
        with self.assertRaises(Exception):
            Category.objects.create(
                name='Electronics Duplicate',
                slug='electronics'  # Duplicate slug
            )

    def test_database_migrations(self):
        """Test database migrations work correctly"""
        # Check if migrations table exists
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='django_migrations'
            """)
            result = cursor.fetchone()
            self.assertIsNotNone(result)

    def test_bulk_operations(self):
        """Test bulk database operations"""
        # Bulk create
        products = [
            Product(
                name=f'Bulk Product {i}',
                slug=f'bulk-product-{i}',
                price=Decimal('99.99'),
                category=self.category,
                stock=10
            ) for i in range(100)
        ]

        created_products = Product.objects.bulk_create(products)
        self.assertEqual(len(created_products), 100)

        # Bulk update
        Product.objects.filter(name__startswith='Bulk').update(stock=20)

        updated_count = Product.objects.filter(
            name__startswith='Bulk',
            stock=20
        ).count()
        self.assertEqual(updated_count, 100)

    def test_database_concurrency(self):
        """Test database handles concurrent operations"""
        product = Product.objects.create(
            name='Concurrent Product',
            slug='concurrent-product',
            price=Decimal('99.99'),
            category=self.category,
            stock=100
        )

        def decrease_stock():
            with transaction.atomic():
                p = Product.objects.select_for_update().get(id=product.id)
                p.stock -= 1
                p.save()

        # Create multiple threads to decrease stock
        threads = []
        for i in range(10):
            thread = threading.Thread(target=decrease_stock)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify final stock
        product.refresh_from_db()
        self.assertEqual(product.stock, 90)
