import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from products.models import Product, Category
from orders.models import Order, OrderItem
from cart.models import Cart, CartItem
from django.contrib.auth import get_user_model

User = get_user_model()


class BusinessRulesTests(TestCase):
    """Test business rules and constraints"""

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

    def test_product_price_validation(self):
        """Business rule: Product price must be positive"""
        with self.assertRaises(ValidationError):
            product = Product(
                name='Invalid Product',
                slug='invalid',
                price=Decimal('-10.00'),
                category=self.category,
                stock=5
            )
            product.full_clean()

    def test_stock_availability_rule(self):
        """Business rule: Cannot order more than available stock"""
        cart = Cart.objects.create(user=self.user)

        with self.assertRaises(ValidationError):
            cart_item = CartItem(
                cart=cart,
                product=self.product,
                quantity=15  # More than available stock (10)
            )
            cart_item.full_clean()

    def test_order_minimum_amount_rule(self):
        """Business rule: Order must meet minimum amount"""
        cheap_product = Product.objects.create(
            name='Cheap Item',
            slug='cheap-item',
            price=Decimal('5.00'),
            category=self.category,
            stock=10
        )

        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('5.00'),
            status='pending'
        )

        # Assuming minimum order amount is $10
        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_discount_percentage_rule(self):
        """Business rule: Discount cannot exceed 70%"""
        from promotions.models import Discount

        with self.assertRaises(ValidationError):
            discount = Discount(
                name='Invalid Discount',
                percentage=80,  # Exceeds 70%
                product=self.product
            )
            discount.full_clean()

    def test_user_cart_single_instance_rule(self):
        """Business rule: User can only have one active cart"""
        cart1 = Cart.objects.create(user=self.user)

        with self.assertRaises(ValidationError):
            cart2 = Cart(user=self.user)
            cart2.full_clean()
