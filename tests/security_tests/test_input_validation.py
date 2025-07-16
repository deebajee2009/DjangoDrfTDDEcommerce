import pytest
from django.urls import reverse
from rest_framework import status
from tests.factories import UserFactory, CategoryFactory

@pytest.mark.security
class TestInputValidation:
    def test_sql_injection_prevention(self, authenticated_client):
        """Test that SQL injection attempts are prevented"""
        malicious_inputs = [
            "'; DROP TABLE products; --",
            "1' OR '1'='1",
            "1'; SELECT * FROM users; --",
            "admin'--",
            "' OR 1=1#"
        ]
        
        url = reverse('product-list')
        for malicious_input in malicious_inputs:
            response = authenticated_client.get(url, {'search': malicious_input})
            # Should not cause server error or expose data
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_xss_prevention(self, authenticated_client):
        """Test that XSS attempts are prevented"""
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            'javascript:alert("XSS")',
            '<svg onload=alert("XSS")>',
            '"><script>alert("XSS")</script>'
        ]
        
        category = CategoryFactory()
        url = reverse('product-list')
        
        for payload in xss_payloads:
            data = {
                'name': payload,
                'description': f'Description with {payload}',
                'price': '10.00',
                'category': category.id,
                'stock_quantity': 1
            }
            response = authenticated_client.post(url, data)
            
            if response.status_code == status.HTTP_201_CREATED:
                # Verify that the payload was sanitized
                assert '<script>' not in response.data['name']
                assert '<script>' not in response.data['description']
    
    def test_file_upload_validation(self, authenticated_client):
        """Test file upload security"""
        # Test malicious file uploads
        malicious_files = [
            ('malicious.php', b'<?php system($_GET["cmd"]); ?>'),
            ('malicious.jsp', b'<% Runtime.getRuntime().exec("cmd"); %>'),
            ('malicious.exe', b'MZ\x90\x00'),  # PE header
        ]
        
        for filename, content in malicious_files:
            # This would test file upload endpoints
            # Implementation depends on your file upload structure
            pass
    
    def test_command_injection_prevention(self, authenticated_client):
        """Test prevention of command injection"""
        command_payloads = [
            '; ls -la',
            '| cat /etc/passwd',
            '&& rm -rf /',
            '`whoami`',
            '$(id)'
        ]
        
        # Test in various input fields
        for payload in command_payloads:
            response = authenticated_client.get(reverse('product-list'), {'search': payload})
            assert response.status_code == status.HTTP_200_OK
            # Should not execute system commands
