import pytest
from django.urls import reverse
from rest_framework import status
from decimal import Decimal
from tests.factories import UserFactory, ProductFactory, CategoryFactory

@pytest.mark.e2e
class TestCompleteEcommerceWorkflow:
    def test_complete_shopping_journey(self, api_client):
        """Test complete user journey from registration to order completion"""

        # 1. User Registration
        register_url = reverse('user-register')
        register_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = api_client.post(register_url, register_data)
        assert response.status_code == status.HTTP_201_CREATED

        # 2. User Login
        login_url = reverse('token_obtain_pair')
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = api_client.post(login_url, login_data)
        assert response.status_code == status.HTTP_200_OK

        token = response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # 3. Browse Products
        category = CategoryFactory(name='Electronics')
        product1 = ProductFactory(name='iPhone 14', category=category, price=Decimal('999.99'))
        product2 = ProductFactory(name='AirPods', category=category, price=Decimal('199.99'))

        products_url = reverse('product-list')
        response = api_client.get(products_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

        # 4. Search Products
        response = api_client.get(products_url, {'search': 'iPhone'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'iPhone 14'

        # 5. View Product Details
        product_detail_url = reverse('product-detail', kwargs={'pk': product1.pk})
        response = api_client.get(product_detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'iPhone 14'

        # 6. Add to Cart (Create Order)
        order_url = reverse('order-list')
        order_data = {
            'items': [
                {
                    'product': product1.id,
                    'quantity': 1
                },
                {
                    'product': product2.id,
                    'quantity': 2
                }
            ],
            'shipping_address': '123 Main St, City, State 12345'
        }
        response = api_client.post(order_url, order_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

        order_id = response.data['id']
        expected_total = Decimal('999.99') + (Decimal('199.99') * 2)
        assert Decimal(response.data['total_amount']) == expected_total

        # 7. Process Payment
        payment_url = reverse('payment-process')
        payment_data = {
            'order': order_id,
            'amount': str(expected_total),
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': '12',
            'expiry_year': '2025',
            'cvv': '123'
        }

        # Mock successful payment
        with patch('apps.payments.gateways.PaymentGateway.process_payment') as mock_payment:
            mock_payment.return_value = {
                'success': True,
                'transaction_id': 'txn_123456',
                'gateway_response': {'status': 'approved'}
            }

            response = api_client.post(payment_url, payment_data)
            assert response.status_code == status.HTTP_200_OK
            assert response.data['status'] == 'completed'

        # 8. View Order History
        orders_url = reverse('order-list')
        response = api_client.get(orders_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == order_id

        # 9. Track Order Status
        order_detail_url = reverse('order-detail', kwargs={'pk': order_id})
        response = api_client.get(order_detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'confirmed'  # Status updated after payment

        # 10. Leave Product Review
        review_url = reverse('review-list')
        review_data = {
            'product': product1.id,
            'rating': 5,
            'comment': 'Great product! Highly recommended.'
        }
        response = api_client.post(review_url, review_data)
        assert response.status_code == status.HTTP_201_CREATED

        # Verify review appears in product details
        response = api_client.get(product_detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['reviews']) == 1
        assert response.data['reviews'][0]['rating'] == 5

    def test_admin_workflow(self, api_client):
        """Test admin workflow for product and order management"""

        # Create admin user
        admin_user = UserFactory(is_staff=True, is_superuser=True)

        # Login as admin
        login_url = reverse('token_obtain_pair')
        login_data = {
            'email': admin_user.email,
            'password': 'testpass123'
        }
        response = api_client.post(login_url, login_data)
        token = response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Create category
        category_url = reverse('category-list')
        category_data = {'name': 'Books'}
        response = api_client.post(category_url, category_data)
        assert response.status_code == status.HTTP_201_CREATED
        category_id = response.data['id']

        # Create product
        product_url = reverse('product-list')
        product_data = {
            'name': 'Django Book',
            'description': 'Learn Django framework',
            'price': '49.99',
            'category': category_id,
            'stock_quantity': 100
        }
        response = api_client.post(product_url, product_data)
        assert response.status_code == status.HTTP_201_CREATED
        product_id = response.data['id']

        # Update product
        product_detail_url = reverse('product-detail', kwargs={'pk': product_id})
        update_data = {
            'name': 'Advanced Django Book',
            'price': '59.99'
        }
        response = api_client.patch(product_detail_url, update_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Advanced Django Book'
        assert response.data['price'] == '59.99'

        # Manage orders (update status)
        # This assumes there's an existing order
        order = OrderFactory(status='pending')
        order_status_url = reverse('order-update-status', kwargs={'pk': order.pk})
        status_data = {'status': 'shipped'}
        response = api_client.patch(order_status_url, status_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'shipped'
