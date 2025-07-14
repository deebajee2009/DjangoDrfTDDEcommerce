import pytest
import sys
from django.test import TestCase
from decimal import Decimal
import asyncio
from typing import List, Dict, Optional


class PythonVersionCompatibilityTests(TestCase):
    """Test Python version compatibility"""

    def test_python_version_support(self):
        """Test current Python version is supported"""
        supported_versions = [(3, 8), (3, 9), (3, 10), (3, 11), (3, 12)]
        current_version = sys.version_info[:2]

        self.assertIn(current_version, supported_versions)

    def test_f_string_compatibility(self):
        """Test f-string formatting (Python 3.6+)"""
        name = "Django"
        version = "4.2"

        formatted = f"{name} {version}"
        self.assertEqual(formatted, "Django 4.2")

    def test_type_hints_compatibility(self):
        """Test type hints compatibility (Python 3.5+)"""
        def process_data(items: List[Dict[str, str]]) -> Optional[str]:
            if not items:
                return None
            return items[0].get('name')

        test_data = [{'name': 'test', 'value': '123'}]
        result = process_data(test_data)
        self.assertEqual(result, 'test')

    def test_async_await_compatibility(self):
        """Test async/await compatibility (Python 3.5+)"""
        async def async_function():
            await asyncio.sleep(0.01)
            return "async_result"

        # Test that async function can be created
        self.assertTrue(asyncio.iscoroutinefunction(async_function))

    def test_pathlib_compatibility(self):
        """Test pathlib compatibility (Python 3.4+)"""
        from pathlib import Path

        path = Path(__file__)
        self.assertTrue(path.exists())
        self.assertTrue(path.is_file())

    def test_dataclasses_compatibility(self):
        """Test dataclasses compatibility (Python 3.7+)"""
        if sys.version_info >= (3, 7):
            from dataclasses import dataclass

            @dataclass
            class Product:
                name: str
                price: Decimal
                stock: int = 0

            product = Product("iPhone", Decimal("999.99"), 10)
            self.assertEqual(product.name, "iPhone")
            self.assertEqual(product.price, Decimal("999.99"))

    def test_walrus_operator_compatibility(self):
        """Test walrus operator compatibility (Python 3.8+)"""
        if sys.version_info >= (3, 8):
            data = [1, 2, 3, 4, 5]

            # Using walrus operator
            result = [(x, y) for x in data if (y := x * 2) > 6]
            expected = [(4, 8), (5, 10)]
            self.assertEqual(result, expected)

    def test_match_statement_compatibility(self):
        """Test match statement compatibility (Python 3.10+)"""
        if sys.version_info >= (3, 10):
            def process_status(status):
                match status:
                    case "pending":
                        return "Order is pending"
                    case "paid":
                        return "Order is paid"
                    case _:
                        return "Unknown status"

            result = process_status("paid")
            self.assertEqual(result, "Order is paid")
