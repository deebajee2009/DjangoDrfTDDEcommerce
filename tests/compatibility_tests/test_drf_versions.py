import pytest
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status, version
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ModelSerializer
from django.contrib.auth import get_user_model


User = get_user_model()


class DRFVersionCompatibilityTests(APITestCase):
    """Test Django REST Framework version compatibility"""

    def test_drf_version_support(self):
        """Test current DRF version is supported"""
        supported_versions = ['3.14', '3.15']
        current_version = '.'.join(version.VERSION.split('.')[:2])

        # Check if current version is supported
        self.assertTrue(any(current_version >= v for v in supported_versions))

    def test_drf_serializer_compatibility(self):
        """Test DRF serializer compatibility"""
        from rest_framework import serializers

        class TestSerializer(serializers.Serializer):
            name = serializers.CharField(max_length=100)
            email = serializers.EmailField()

        data = {'name': 'Test User', 'email': 'test@example.com'}
        serializer = TestSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['name'], 'Test User')

    def test_drf_viewset_compatibility(self):
        """Test DRF ViewSet compatibility"""
        from rest_framework.viewsets import ModelViewSet
        from rest_framework.decorators import action

        class TestViewSet(ModelViewSet):
            queryset = User.objects.all()

            @action(detail=True, methods=['post'])
            def custom_action(self, request, pk=None):
                return Response({'status': 'ok'})

        viewset = TestViewSet()
        self.assertTrue(hasattr(viewset, 'custom_action'))

    def test_drf_authentication_compatibility(self):
        """Test DRF authentication compatibility"""
        from rest_framework.authentication import TokenAuthentication
        from rest_framework.authtoken.models import Token

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        token, created = Token.objects.get_or_create(user=user)

        self.assertIsInstance(token, Token)
        self.assertEqual(token.user, user)

    def test_drf_permissions_compatibility(self):
        """Test DRF permissions compatibility"""
        from rest_framework.permissions import IsAuthenticated, AllowAny

        class TestView(APIView):
            permission_classes = [IsAuthenticated]

            def get(self, request):
                return Response({'message': 'Hello'})

        view = TestView()
        self.assertEqual(view.permission_classes, [IsAuthenticated])

    def test_drf_pagination_compatibility(self):
        """Test DRF pagination compatibility"""
        from rest_framework.pagination import PageNumberPagination

        class TestPagination(PageNumberPagination):
            page_size = 10
            page_size_query_param = 'page_size'
            max_page_size = 100

        pagination = TestPagination()
        self.assertEqual(pagination.page_size, 10)

    def test_drf_filtering_compatibility(self):
        """Test DRF filtering compatibility"""
        from rest_framework.filters import SearchFilter, OrderingFilter

        class TestView(APIView):
            filter_backends = [SearchFilter, OrderingFilter]
            search_fields = ['name', 'email']
            ordering_fields = ['created_at']

        view = TestView()
        self.assertEqual(len(view.filter_backends), 2)
