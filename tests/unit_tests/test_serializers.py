import pytest
from apps.products.serializers import ProductSerializer, CategorySerializer
from apps.accounts.serializers import UserSerializer
from tests.factories import ProductFactory, CategoryFactory, UserFactory

@pytest.mark.unit
class TestProductSerializer:
    def test_product_serialization(self):
        product = ProductFactory()
        serializer = ProductSerializer(product)
        data = serializer.data

        assert data['name'] == product.name
        assert data['slug'] == product.slug
        assert data['description'] == product.description
        assert float(data['price']) == float(product.price)
        assert data['is_active'] == product.is_active

    def test_product_deserialization(self):
        category = CategoryFactory()
        data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': '99.99',
            'category': category.id,
            'stock_quantity': 10
        }
        serializer = ProductSerializer(data=data)
        assert serializer.is_valid()

        product = serializer.save()
        assert product.name == 'Test Product'
        assert product.slug == 'test-product'

    def test_product_serializer_validation(self):
        data = {
            'name': '',  # Invalid: empty name
            'description': 'Test Description',
            'price': '-10.00',  # Invalid: negative price
            'category': 9999,  # Invalid: non-existent category
            'stock_quantity': -5  # Invalid: negative stock
        }
        serializer = ProductSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
        assert 'price' in serializer.errors
        assert 'category' in serializer.errors
        assert 'stock_quantity' in serializer.errors

@pytest.mark.unit
class TestCategorySerializer:
    def test_category_serialization(self):
        category = CategoryFactory()
        serializer = CategorySerializer(category)
        data = serializer.data

        assert data['name'] == category.name
        assert data['slug'] == category.slug
        assert data['is_active'] == category.is_active

    def test_category_with_children_serialization(self):
        parent = CategoryFactory()
        child1 = CategoryFactory(parent=parent)
        child2 = CategoryFactory(parent=parent)

        serializer = CategorySerializer(parent)
        data = serializer.data

        assert len(data['children']) == 2
        child_names = [child['name'] for child in data['children']]
        assert child1.name in child_names
        assert child2.name in child_names

@pytest.mark.unit
class TestUserSerializer:
    def test_user_serialization(self):
        user = UserFactory()
        serializer = UserSerializer(user)
        data = serializer.data

        assert data['username'] == user.username
        assert data['email'] == user.email
        assert data['first_name'] == user.first_name
        assert data['last_name'] == user.last_name
        assert 'password' not in data  # Password should not be serialized

    def test_user_deserialization(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }
        serializer = UserSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')  # Password should be hashed
