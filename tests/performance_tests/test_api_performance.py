import pytest
import time
from django.urls import reverse
from rest_framework import status
from tests.factories import ProductFactory, CategoryFactory, UserFactory

@pytest.mark.performance
class TestAPIPerformance:
    def test_product_list_performance(self, api_client):
        """Test that product list endpoint responds within acceptable time"""
        # Create test data
        ProductFactory.create_batch(100)

        url = reverse('product-list')
        start_time = time.time()
        response = api_client.get(url)
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK
        assert end_time - start_time < 1.0  # Should respond within 1 second

    def test_product_search_performance(self, api_client):
        """Test search performance with large dataset"""
        # Create products with searchable names
        for i in range(1000):
            ProductFactory(name=f"Product {i}")

        url = reverse('product-list')
        start_time = time.time()
        response = api_client.get(url, {'search': 'Product'})
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK
        assert end_time - start_time < 2.0  # Search should complete within 2 seconds

    def test_concurrent_request_handling(self, api_client):
        """Test system performance under concurrent load"""
        import threading

        ProductFactory.create_batch(50)
        url = reverse('product-list')

        results = []

        def make_request():
            start_time = time.time()
            response = api_client.get(url)
            end_time = time.time()
            results.append({
                'status': response.status_code,
                'time': end_time - start_time
            })

        # Create 20 concurrent requests
        threads = []
        for i in range(20):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all requests succeeded
        assert all(result['status'] == status.HTTP_200_OK for result in results)

        # Verify average response time is acceptable
        avg_time = sum(result['time'] for result in results) / len(results)
        assert avg_time < 1.5  # Average response time should be under 1.5 seconds

    def test_database_query_optimization(self, api_client):
        """Test that database queries are optimized"""
        from django.test.utils import override_settings
        from django.db import connection

        # Create test data with relationships
        categories = CategoryFactory.create_batch(5)
        for category in categories:
            ProductFactory.create_batch(20, category=category)

        url = reverse('product-list')

        with override_settings(DEBUG=True):
            connection.queries_log.clear()
            response = api_client.get(url)
            query_count = len(connection.queries)

        assert response.status_code == status.HTTP_200_OK
        # Should not have N+1 query problems
        assert query_count < 10  # Reasonable number of queries
