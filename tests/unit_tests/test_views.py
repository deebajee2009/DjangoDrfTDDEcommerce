import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from tests.factories import ProductFactory, CategoryFactory, UserFactory
from apps.products.models import Product

@pytest.mark.unit
class TestProductViewSet:
    def test_get_product_list(self, api_client):
        ProductFactory.create_batch(5)
        url = reverse('product-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5

    def test_get_product_detail(self, api_client):
        product = ProductFactory()
        url = reverse('product-detail', kwargs={'pk': product.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == product.name

    def test_create_product_requires_authentication(self, api_client):
        category = CategoryFactory()
        url = reverse('product-list')
        data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': '99.99',
            'category': category.id,
            'stock_quantity': 10
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_product_with_authentication(self, authenticated_client):
        category = CategoryFactory()
        url = reverse('product-list')
        data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': '99.99',
            'category': category.id,
            'stock_quantity': 10
        }
        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Product.objects.filter(name='Test Product').exists()

    def test_filter_products_by_category(self, api_client):
        category1 = CategoryFactory()
        category2 = CategoryFactory()
        ProductFactory.create_batch(3, category=category1)
        ProductFactory.create_batch(2, category=category2)

        url = reverse('product-list')
        response = api_client.get(url, {'category': category1.id})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_search_products(self, api_client):
        ProductFactory(name='iPhone 14')
        ProductFactory(name='Samsung Galaxy')
        ProductFactory(name='iPad Pro')

        url = reverse('product-list')
        response = api_client.get(url, {'search': 'iPhone'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'iPhone 14'

@pytest.mark.unit
class TestCategoryViewSet:
    def test_get_category_list(self, api_client):
        CategoryFactory.create_batch(3)
        url = reverse('category-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_get_category_detail(self, api_client):
        category = CategoryFactory()
        url = reverse('category-detail', kwargs={'pk': category.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == category.name

    def test_create_category_requires_admin(self, authenticated_client):
        url = reverse('category-list')
        data = {'name': 'Test Category'}
        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_category_with_admin(self, admin_client):
        url = reverse('category-list')
        data = {'name': 'Test Category'}
        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Test Category'
        assert response.data['slug'] == 'test-category'
