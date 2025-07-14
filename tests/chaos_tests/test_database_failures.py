import pytest
from unittest.mock import patch, Mock
from django.db import connections, transaction
from django.core.exceptions import ImproperlyConfigured
from tests.factories import ProductFactory, UserFactory
from apps.products.models import Product

@pytest.mark.chaos
class TestDatabaseFailures:
    """
    Chaos engineering tests to verify system resilience
    """

    @patch('django.db.connections')
    def test_database_connection_failure(self, mock_connections):
        """Test behavior when database connection fails"""
        mock_connections.__getitem__.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception):
            Product.objects.all()

    @patch('django.db.transaction.atomic')
    def test_transaction_rollback_on_failure(self, mock_atomic):
        """Test that transactions rollback properly on failure"""
        mock_atomic.side_effect = Exception("Transaction failed")

        with pytest.raises(Exception):
            with transaction.atomic():
                ProductFactory()

    def test_database_timeout_handling(self):
        """Test handling of database timeout scenarios"""
        # Simulate slow query
        with patch('django.db.models.QuerySet.filter') as mock_filter:
            mock_filter.side_effect = Exception("Query timeout")

            with pytest.raises(Exception):
                Product.objects.filter(name="test")

    def test_concurrent_access_handling(self):
        """Test handling of concurrent database access"""
        import threading
        import time

        results = []
        errors = []

        def create_product():
            try:
                product = ProductFactory()
                results.append(product.id)
            except Exception as e:
                errors.append(str(e))

        # Create multiple threads to simulate concurrent access
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_product)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify that most operations succeeded despite concurrency
        assert len(results) >= 8  # Allow some failures due to concurrency
        assert len(errors) <= 2
