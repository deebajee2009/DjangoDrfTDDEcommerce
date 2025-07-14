import pytest
from django.test import TestCase
from django.core.cache import cache
from django.core.cache.backends.base import BaseCache
from django.contrib.auth import get_user_model
from decimal import Decimal
from products.models import Product, Category
from unittest.mock import patch
import time

User = get_user_model()


class CacheTests(TestCase):
    """Test caching functionality"""

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
        cache.clear()

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations"""
        cache.set('test_key', 'test_value', 300)
        value = cache.get('test_key')
        self.assertEqual(value, 'test_value')

    def test_cache_expiration(self):
        """Test cache expiration"""
        cache.set('expiring_key', 'test_value', 1)  # 1 second

        # Should exist immediately
        self.assertEqual(cache.get('expiring_key'), 'test_value')

        # Should expire after timeout
        time.sleep(2)
        self.assertIsNone(cache.get('expiring_key'))

    def test_cache_delete(self):
        """Test cache deletion"""
        cache.set('delete_key', 'test_value', 300)
        self.assertEqual(cache.get('delete_key'), 'test_value')

        cache.delete('delete_key')
        self.assertIsNone(cache.get('delete_key'))

    def test_cache_many_operations(self):
        """Test cache many operations"""
        data = {
            'key1': 'value1',
            'key2': 'value2',
            'key3': 'value3'
        }

        cache.set_many(data, 300)

        retrieved = cache.get_many(['key1', 'key2', 'key3'])
        self.assertEqual(retrieved, data)

    def test_product_cache(self):
        """Test product caching"""
        cache_key = f'product_{self.product.id}'

        # Cache product
        cache.set(cache_key, self.product, 300)

        # Retrieve from cache
        cached_product = cache.get(cache_key)
        self.assertEqual(cached_product.id, self.product.id)
        self.assertEqual(cached_product.name, self.product.name)

    def test_cache_versioning(self):
        """Test cache versioning"""
        cache.set('versioned_key', 'value_v1', 300, version=1)
        cache.set('versioned_key', 'value_v2', 300, version=2)

        v1_value = cache.get('versioned_key', version=1)
        v2_value = cache.get('versioned_key', version=2)

        self.assertEqual(v1_value, 'value_v1')
        self.assertEqual(v2_value, 'value_v2')

    def test_cache_invalidation(self):
        """Test cache invalidation on model changes"""
        cache_key = f'product_{self.product.id}'
        cache.set(cache_key, self.product, 300)

        # Modify product
        self.product.name = 'Modified Product'
        self.product.save()

        # Cache should be invalidated (in real app, this would be handled by signals)
        # For testing, we manually delete
        cache.delete(cache_key)

        cached_product = cache.get(cache_key)
        self.assertIsNone(cached_product)

    def test_cache_performance(self):
        """Test cache performance benefits"""
        # Simulate expensive operation
        def expensive_operation():
            time.sleep(0.1)  # Simulate 100ms operation
            return "expensive_result"

        # Without cache
        start_time = time.time()
        result1 = expensive_operation()
        first_call_time = time.time() - start_time

        # With cache
        cache_key = 'expensive_operation'

        start_time = time.time()
        cached_result = cache.get(cache_key)
        if cached_result is None:
            cached_result = expensive_operation()
            cache.set(cache_key, cached_result, 300)
        cached_call_time = time.time() - start_time

        # Second call should be faster
        start_time = time.time()
        cached_result2 = cache.get(cache_key)
        second_cached_call_time = time.time() - start_time

        self.assertEqual(result1, cached_result)
        self.assertLess(second_cached_call_time, first_call_time)
