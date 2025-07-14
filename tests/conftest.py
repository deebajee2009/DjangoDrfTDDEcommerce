import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from tests.factories import UserFactory, ProductFactory, CategoryFactory

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client):
    user = UserFactory()
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    api_client.user = user
    return api_client

@pytest.fixture
def admin_client(api_client):
    user = UserFactory(is_staff=True, is_superuser=True)
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    api_client.user = user
    return api_client

@pytest.fixture
def sample_user():
    return UserFactory()

@pytest.fixture
def sample_category():
    return CategoryFactory()

@pytest.fixture
def sample_product():
    return ProductFactory()

@pytest.fixture
def sample_products():
    return ProductFactory.create_batch(10)

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Give all tests access to the database.
    """
    pass
