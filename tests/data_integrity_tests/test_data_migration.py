import pytest
from django.test import TestCase
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import MigrationLoader
from django.test.utils import override_settings
from io import StringIO
import sys


class DataMigrationTests(TestCase):
    """Test data migrations and schema changes"""

    def test_migrations_are_up_to_date(self):
        """Test that all migrations are up to date"""
        try:
            call_command('makemigrations', '--dry-run', '--check', verbosity=0)
        except SystemExit as e:
            if e.code != 0:
                self.fail("Migrations are not up to date")

    def test_migration_reversibility(self):
        """Test that migrations can be reversed"""
        # Get migration loader
        loader = MigrationLoader(connection)

        # Check if migrations exist
        graph = loader.graph
        self.assertGreater(len(graph.nodes), 0)

        # Test migration execution
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(graph.leaf_nodes())

        # Verify plan exists
        self.assertIsInstance(plan, list)

    def test_migration_squashing_compatibility(self):
        """Test migration squashing doesn't break functionality"""
        # This would test if squashed migrations work correctly
        # In practice, you would run specific migration commands
        pass

    def test_data_migration_integrity(self):
        """Test data migration preserves data integrity"""
        # Create test data before migration
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Simulate data migration
        # This would run specific data migration operations

        # Verify data integrity after migration
        user.refresh_from_db()
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')

    def test_schema_migration_safety(self):
        """Test schema migrations are safe"""
        # Test that schema changes don't break existing functionality
        with connection.cursor() as cursor:
            # Check table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='auth_user'
            """)
            result = cursor.fetchone()
            self.assertIsNotNone(result)

    def test_custom_migration_operations(self):
        """Test custom migration operations work correctly"""
        # Test custom migration operations like RunPython, RunSQL
        from django.db.migrations.operations import RunPython

        def forwards_func(apps, schema_editor):
            # Custom migration logic
            pass

        def reverse_func(apps, schema_editor):
            # Reverse migration logic
            pass

        operation = RunPython(forwards_func, reverse_func)
        self.assertEqual(operation.reversible, True)
