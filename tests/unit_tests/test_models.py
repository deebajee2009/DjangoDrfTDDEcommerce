# import pytest
# from apps.products.models import Product
#
# @pytest.mark.django_db
# def test_product_discounted_price():
#     """
#     Tests that the discounted_price property of the Product model
#     calculates the correct price after applying a discount.
#     """
#     product = Product.objects.create(
#         name="Test Product",
#         price=100.00,
#         discount_percent=20.00
#     )
#     assert product.discounted_price == 80.00
#
# @pytest.mark.django_db
# def test_product_no_discount():
#     """
#     Tests that the discounted_price is the same as the original price
#     when no discount is applied.
#     """
#     product = Product.objects.create(
#         name="Test Product without Discount",
#         price=150.00
#     )
#     assert product.discounted_price == 150.00

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from tests.factories import UserFactory, ProductFactory, CategoryFactory, OrderFactory

@pytest.mark.unit
class TestUserModel:
    def test_user_creation(self):
        user = UserFactory()
        assert user.email
        assert user.username
        assert user.is_active
        assert user.is_verified

    def test_user_string_representation(self):
        user = UserFactory(username="testuser")
        assert str(user) == "testuser"

    def test_user_email_uniqueness(self):
        user1 = UserFactory(email="test@example.com")
        with pytest.raises(IntegrityError):
            UserFactory(email="test@example.com")

    def test_phone_number_validation(self):
        user = UserFactory()
        user.phone_number = "invalid_phone"
        with pytest.raises(ValidationError):
            user.full_clean()

@pytest.mark.unit
class TestCategoryModel:
    def test_category_creation(self):
        category = CategoryFactory()
        assert category.name
        assert category.slug
        assert category.is_active

    def test_category_slug_auto_generation(self):
        category = CategoryFactory(name="Test Category")
        assert category.slug == "test-category"

    def test_category_string_representation(self):
        category = CategoryFactory(name="Electronics")
        assert str(category) == "Electronics"

    def test_category_parent_child_relationship(self):
        parent = CategoryFactory(name="Electronics")
        child = CategoryFactory(name="Smartphones", parent=parent)
        assert child.parent == parent
        assert child in parent.children.all()

@pytest.mark.unit
class TestProductModel:
    def test_product_creation(self):
        product = ProductFactory()
        assert product.name
        assert product.slug
        assert product.description
        assert product.price > 0
        assert product.category
        assert product.is_active

    def test_product_slug_auto_generation(self):
        product = ProductFactory(name="Test Product")
        assert product.slug == "test-product"

    def test_product_string_representation(self):
        product = ProductFactory(name="iPhone 14")
        assert str(product) == "iPhone 14"

    def test_product_is_in_stock_property(self):
        product = ProductFactory(stock_quantity=10)
        assert product.is_in_stock is True

        product.stock_quantity = 0
        assert product.is_in_stock is False

    def test_product_price_validation(self):
        product = ProductFactory()
        product.price = Decimal('-10.00')
        with pytest.raises(ValidationError):
            product.full_clean()

@pytest.mark.unit
class TestOrderModel:
    def test_order_creation(self):
        order = OrderFactory()
        assert order.user
        assert order.status == 'pending'
        assert order.total_amount > 0
        assert order.shipping_address

    def test_order_string_representation(self):
        order = OrderFactory()
        expected = f"Order #{order.id} - {order.user.email}"
        assert str(order) == expected

    def test_order_status_choices(self):
        order = OrderFactory()
        valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
        for status in valid_statuses:
            order.status = status
            order.full_clean()  # Should not raise ValidationError
