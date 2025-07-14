import pytest
from django.urls import reverse
from rest_framework import status
from decimal import Decimal
from tests.factories import UserFactory, ProductFactory, CategoryFactory
from apps.orders.models import Order, OrderItem

@pytest.mark.integration
class TestOrderFlow:
    def test_complete_order_flow(self, api_client):
        # Setup
        user = UserFactory()
        category = CategoryFactory()
        product1 = ProductFactory(category=category, price=Decimal('10.00'), stock_quantity=5)
        product2 = ProductFactory(category=category, price=Decimal('20.00'), stock_quantity=3)

        # Login
        login_url = reverse('token_obtain_pair')
        login_data = {
            'email': user.email,
            'password': 'testpass123'
        }
        response = api_client.post(login_url, login_data)
        assert response.status_code == status.HTTP_200_OK

        token = response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Create order
        order_url = reverse('order-list')
        order_data = {
            'items': [
                {
                    'product': product1.id,
                    'quantity': 2
                },
                {
                    'product': product2.id,
                    'quantity': 1
                }
            ],
            'shipping_address': '123 Test St, Test City, TC 12345'
        }
        response = api_client.post(order_url, order_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

        # Verify order creation
        order = Order.objects.get(id=response.data['id'])
        assert order.user == user
        assert order.status == 'pending'
        assert order.total_amount == Decimal('40.00')  # 2*10 + 1*20
        assert order.items.count() == 2

        # Verify stock reduction
        product1.refresh_from_db()
        product2.refresh_from_db()
        assert product1.stock_quantity == 3  # 5 - 2
        assert product2.stock_quantity == 2  # 3 - 1

    def test_order_insufficient_stock(self, authenticated_client):
        product = ProductFactory(stock_quantity=1)

        order_url = reverse('order-list')
        order_data = {
            'items': [
                {
                    'product': product.id,
                    'quantity': 5  # More than available stock
                }
            ],
            'shipping_address': '123 Test St, Test City, TC 12345'
        }
        response = authenticated_client.post(order_url, order_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'insufficient stock' in str(response.data).lower()

    def test_order_status_update_flow(self, authenticated_client):
        # Create order
        product = ProductFactory(stock_quantity=5)
        order_url = reverse('order-list')
        order_data = {
            'items': [{'product': product.id, 'quantity': 1}],
            'shipping_address': '123 Test St, Test City, TC 12345'
        }
        response = authenticated_client.post(order_url, order_data, format='json')
        order_id = response.data['id']

        # Update order status (admin only)
        admin_client = authenticated_client
        admin_client.user.is_staff = True
        admin_client.user.save()

        status_url = reverse('order-update-status', kwargs={'pk': order_id})
        status_data = {'status': 'confirmed'}
        response = admin_client.patch(status_url, status_data)
        assert response.status_code == status.HTTP_200_OK

        order = Order.objects.get(id=order_id)
        assert order.status == 'confirmed'
