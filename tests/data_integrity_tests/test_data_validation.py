import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal
from products.models import Product, Category
from orders.models import Order, OrderItem
from cart.models import Cart, CartItem
from django.core.validators import validate_email

User = get_user_model()


class DataValidationTests(TestCase):
    """Test data validation rules and constraints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        self.product = Product.objects.create(
            name='iPhone 15',
            slug='iphone-15',
            price=Decimal('999.99'),
            category=self.category,
            stock=10
        )

    def test_email_validation(self):
        """Test email format validation"""
        # Valid email
        try:
            validate_email('test@example.com')
        except ValidationError:
            self.fail("Valid email should not raise ValidationError")

        # Invalid email
        with self.assertRaises(ValidationError):
            validate_email('invalid-email')

    def test_product_price_validation(self):
        """Test product price validation"""
        # Valid price
        product = Product(
            name='Valid Product',
            slug='valid-product',
            price=Decimal('99.99'),
            category=self.category,
            stock=5
        )
        try:
            product.full_clean()
        except ValidationError:
            self.fail("Valid product should not raise ValidationError")

        # Invalid negative price
        with self.assertRaises(ValidationError):
            product = Product(
                name='Invalid Product',
                slug='invalid-product',
                price=Decimal('-10.00'),
                category=self.category,
                stock=5
            )
            product.full_clean()

    def test_slug_validation(self):
        """Test slug format validation"""
        # Valid slug
        category = Category(
            name='Test Category',
            slug='test-category'
        )
        try:
            category.full_clean()
        except ValidationError:
            self.fail("Valid category should not raise ValidationError")

        # Invalid slug with spaces
        with self.assertRaises(ValidationError):
            category = Category(
                name='Invalid Category',
                slug='invalid category'  # Spaces not allowed
            )
            category.full_clean()

    def test_stock_validation(self):
        """Test stock quantity validation"""
        # Valid stock
        product = Product(
            name='Valid Product',
            slug='valid-product-2',
            price=Decimal('99.99'),
            category=self.category,
            stock=100
        )
        try:
            product.full_clean()
        except ValidationError:
            self.fail("Valid product should not raise ValidationError")

        # Invalid negative stock
        with self.assertRaises(ValidationError):
            product = Product(
                name='Invalid Product',
                slug='invalid-product-2',
                price=Decimal('99.99'),
                category=self.category,
                stock=-5
            )
            product.full_clean()

    def test_order_item_quantity_validation(self):
        """Test order item quantity validation"""
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('999.99'),
            status='pending'
        )

        # Valid quantity
        order_item = OrderItem(
            order=order,
            product=self.product,
            quantity=5,
            price=Decimal('999.99')
        )
        try:
            order_item.full_clean()
        except ValidationError:
            self.fail("Valid order item should not raise ValidationError")

        # Invalid zero quantity
        with self.assertRaises(ValidationError):
            order_item = OrderItem(
                order=order,
                product=self.product,
                quantity=0,
                price=Decimal('999.99')
            )
            order_item.full_clean()

    def test_cart_item_validation(self):
        """Test cart item validation"""
        cart = Cart.objects.create(user=self.user)

        # Valid cart item
        cart_item = CartItem(
            cart=cart,
            product=self.product,
            quantity=2
        )
        try:
            cart_item.full_clean()
        except ValidationError:
            self.fail("Valid cart item should not raise ValidationError")

        # Invalid quantity exceeding stock
        with self.assertRaises(ValidationError):
            cart_item = CartItem(
                cart=cart,
                product=self.product,
                quantity=15  # Exceeds stock of 10
            )
            cart_item.full_clean()

    def test_username_validation(self):
        """Test username validation"""
        # Valid username
        user = User(
            username='validuser123',
            email='valid@example.com'
        )
        try:
            user.full_clean()
        except ValidationError:
            self.fail("Valid user should not raise ValidationError")

        # Invalid username with special characters
        with self.assertRaises(ValidationError):
            user = User(
                username='invalid@user',
                email='invalid@example.com'
            )
            user.full_clean()
