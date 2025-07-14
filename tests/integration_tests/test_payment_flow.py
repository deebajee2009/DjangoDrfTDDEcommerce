import pytest
from django.urls import reverse
from rest_framework import status
from decimal import Decimal
from unittest.mock import patch, Mock
from tests.factories import UserFactory, OrderFactory
from apps.payments.models import Payment

@pytest.mark.integration
class TestPaymentFlow:
    @patch('apps.payments.gateways.PaymentGateway.process_payment')
    def test_successful_payment_flow(self, mock_process_payment, authenticated_client):
        # Setup mock response
        mock_process_payment.return_value = {
            'success': True,
            'transaction_id': 'txn_123456',
            'gateway_response': {'status': 'approved'}
        }

        # Create order
        order = OrderFactory(user=authenticated_client.user, total_amount=Decimal('50.00'))

        # Process payment
        payment_url = reverse('payment-process')
        payment_data = {
            'order': order.id,
            'amount': '50.00',
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': '12',
            'expiry_year': '2025',
            'cvv': '123'
        }
        response = authenticated_client.post(payment_url, payment_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'completed'
        assert response.data['transaction_id'] == 'txn_123456'

        # Verify payment record
        payment = Payment.objects.get(order=order)
        assert payment.status == 'completed'
        assert payment.amount == Decimal('50.00')
        assert payment.transaction_id == 'txn_123456'

        # Verify order status updated
        order.refresh_from_db()
        assert order.status == 'confirmed'

    @patch('apps.payments.gateways.PaymentGateway.process_payment')
    def test_failed_payment_flow(self, mock_process_payment, authenticated_client):
        # Setup mock response for failed payment
        mock_process_payment.return_value = {
            'success': False,
            'error': 'Card declined',
            'gateway_response': {'status': 'declined'}
        }

        order = OrderFactory(user=authenticated_client.user, total_amount=Decimal('50.00'))

        payment_url = reverse('payment-process')
        payment_data = {
            'order': order.id,
            'amount': '50.00',
            'payment_method': 'credit_card',
            'card_number': '4000000000000002',  # Test card for declined
            'expiry_month': '12',
            'expiry_year': '2025',
            'cvv': '123'
        }
        response = authenticated_client.post(payment_url, payment_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Card declined' in response.data['error']

        # Verify payment record
        payment = Payment.objects.get(order=order)
        assert payment.status == 'failed'

        # Verify order status unchanged
        order.refresh_from_db()
        assert order.status == 'pending'

    def test_payment_amount_validation(self, authenticated_client):
        order = OrderFactory(user=authenticated_client.user, total_amount=Decimal('50.00'))

        payment_url = reverse('payment-process')
        payment_data = {
            'order': order.id,
            'amount': '100.00',  # Different from order total
            'payment_method': 'credit_card',
            'card_number': '4111111111111111',
            'expiry_month': '12',
            'expiry_year': '2025',
            'cvv': '123'
        }
        response = authenticated_client.post(payment_url, payment_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'amount mismatch' in str(response.data).lower()
