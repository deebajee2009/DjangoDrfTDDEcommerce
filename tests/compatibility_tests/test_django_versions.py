import pytest
import django
from django.test import TestCase
from django.conf import settings
from django.core.management import call_command
from django.test.utils import override_settings
import sys


class DjangoVersionCompatibilityTests(TestCase):
    """Test compatibility across Django versions"""

    def test_django_version_support(self):
        """Test current Django version is supported"""
        supported_versions = ['4.2', '5.0', '5.1']
        current_version = '.'.join(django.VERSION[:2])

        self.assertIn(current_version, [v for v in supported_versions])

    def test_django_settings_compatibility(self):
        """Test Django settings compatibility"""
        # Test required settings exist
        required_settings = [
            'SECRET_KEY',
            'DEBUG',
            'ALLOWED_HOSTS',
            'INSTALLED_APPS',
            'MIDDLEWARE',
            'ROOT_URLCONF',
            'DATABASES',
        ]

        for setting in required_settings:
            self.assertTrue(hasattr(settings, setting))

    def test_django_admin_compatibility(self):
        """Test Django admin compatibility"""
        from django.contrib import admin
        from django.contrib.admin.sites import AdminSite

        # Test admin site creation
        admin_site = AdminSite()
        self.assertIsInstance(admin_site, AdminSite)

    def test_django_orm_compatibility(self):
        """Test Django ORM compatibility"""
        from django.db import models
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Test model creation
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.assertIsInstance(user, User)
        self.assertEqual(user.username, 'testuser')

    def test_django_migrations_compatibility(self):
        """Test Django migrations compatibility"""
        try:
            call_command('makemigrations', '--dry-run', verbosity=0)
            call_command('migrate', '--run-syncdb', verbosity=0)
        except Exception as e:
            self.fail(f"Migration compatibility test failed: {e}")

    @override_settings(USE_TZ=True)
    def test_timezone_compatibility(self):
        """Test timezone handling compatibility"""
        from django.utils import timezone

        now = timezone.now()
        self.assertTrue(timezone.is_aware(now))

    def test_url_routing_compatibility(self):
        """Test URL routing compatibility"""
        from django.urls import reverse, NoReverseMatch

        # Test that basic URL patterns work
        try:
            url = reverse('admin:index')
            self.assertTrue(url.startswith('/'))
        except NoReverseMatch:
            # Admin might not be enabled in test settings
            pass
