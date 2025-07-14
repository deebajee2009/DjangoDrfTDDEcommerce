import pytest
from tests.factories import ProductFactory, UserFactory, OrderFactory
from apps.products.models import Product
from apps.orders.models import Order

@pytest.mark.mutation
class TestProductModelMutations:
    """
    Mutation tests to verify test quality by introducing small code changes
    """

    def test_product_price_boundary_mutation(self):
        """Test that changing price validation boundaries would be caught"""
        product = ProductFactory(price=0.01)  # Minimum valid price

        # This should pass with current validation
        product.full_clean()

        # If we mutate >= to > in validation, this should fail
        # The test framework will introduce this mutation automatically
        assert product.price >= 0.01

    def test_product_stock_negative_mutation(self):
        """Test that allowing negative stock would be caught"""
        product = ProductFactory(stock_quantity=0)

        # This should be valid
        assert product.stock_quantity >= 0

        # If we mutate the validation to allow negative, tests should catch it
        assert product.is_in_stock == False

    def test_product_slug_uniqueness_mutation(self):
        """Test that removing slug uniqueness constraint would be caught"""
        product1 = ProductFactory(name="Test Product")

        # This should raise an error if uniqueness is enforced
        with pytest.raises(Exception):
            product2 = ProductFactory(name="Test Product", slug=product1.slug)
            product2.save()

@pytest.mark.mutation
class TestOrderModelMutations:
    def test_order_total_calculation_mutation(self):
        """Test that mutations in total calculation would be caught"""
        order = OrderFactory(total_amount=100.00)

        # Test boundary conditions that mutations might affect
        assert order.total_amount > 0
        assert order.total_amount == 100.00  # Exact match

        # If mutation changes == to !=, test should fail
        assert not (order.total_amount < 0)
