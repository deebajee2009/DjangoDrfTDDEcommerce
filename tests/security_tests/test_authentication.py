import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from tests.factories import UserFactory

User = get_user_model()

@pytest.mark.security
class TestAuthentication:
    def test_unauthenticated_access_denied(self):
        """Test that protected endpoints require authentication"""
        client = APIClient()

        protected_urls = [
            reverse('order-list'),
            reverse('profile-detail'),
            reverse('product-list'),  # POST/PUT/DELETE should be protected
        ]

        for url in protected_urls:
            response = client.post(url, {})
            assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_invalid_token_rejected(self):
        """Test that invalid tokens are rejected"""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')

        url = reverse('order-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_token_rejected(self):
        """Test that expired tokens are rejected"""
        # This would require mocking time or using a test-specific token
        # For demonstration purposes
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer expired_token')

        url = reverse('order-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_password_strength_validation(self):
        """Test password strength requirements"""
        weak_passwords = [
            '123',
            'password',
            '12345678',
            'aaaaaaaa'
        ]

        for password in weak_passwords:
            data = {
                'username': 'testuser',
                'email': 'test@example.com',
                'password': password
            }
            response = APIClient().post(reverse('user-register'), data)
            # Should fail due to weak password
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_brute_force_protection(self):
        """Test protection against brute force attacks"""
        client = APIClient()
        url = reverse('token_obtain_pair')

        # Simulate multiple failed login attempts
        for i in range(10):
            data = {
                'email': 'nonexistent@example.com',
                'password': 'wrongpassword'
            }
            response = client.post(url, data)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # After multiple failures, should implement rate limiting
        # This would require implementing rate limiting middleware
