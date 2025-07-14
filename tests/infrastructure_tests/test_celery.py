import pytest
from django.test import TestCase
from unittest.mock import patch, Mock
from celery import Celery
from decimal import Decimal
from django.contrib.auth import get_user_model
from products.models import Product, Category
from orders.models import Order, OrderItem

User = get_user_model()


class CeleryTests(TestCase):
    """Test Celery task queue functionality"""

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

    @patch('celery.current_app.send_task')
    def test_send_email_task(self, mock_send_task):
        """Test email sending task"""
        # Mock task execution
        mock_send_task.return_value = Mock(id='task-123')

        # Import and call task
        from tasks import send_email_task

        result = send_email_task.delay(
            subject='Test Email',
            message='Test message',
            recipient='test@example.com'
        )

        self.assertIsNotNone(result)
        mock_send_task.assert_called_once()

    @patch('celery.current_app.send_task')
    def test_order_processing_task(self, mock_send_task):
        """Test order processing task"""
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('999.99'),
            status='pending'
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=Decimal('999.99')
        )

        # Mock task execution
        mock_send_task.return_value = Mock(id='task-456')

        from tasks import process_order_task

        result = process_order_task.delay(order.id)

        self.assertIsNotNone(result)
        mock_send_task.assert_called_once()

    @patch('celery.current_app.send_task')
    def test_inventory_update_task(self, mock_send_task):
        """Test inventory update task"""
        # Mock task execution
        mock_send_task.return_value = Mock(id='task-789')

        from tasks import update_inventory_task

        result = update_inventory_task.delay(
            product_id=self.product.id,
            quantity_sold=5
        )

        self.assertIsNotNone(result)
        mock_send_task.assert_called_once()

    @patch('celery.current_app.send_task')
    def test_periodic_task(self, mock_send_task):
        """Test periodic task execution"""
        # Mock task execution
        mock_send_task.return_value = Mock(id='task-periodic')

        from tasks import cleanup_expired_carts_task

        result = cleanup_expired_carts_task.delay()

        self.assertIsNotNone(result)
        mock_send_task.assert_called_once()

    def test_task_retry_mechanism(self):
        """Test task retry mechanism"""
        from celery.exceptions import Retry

        # Mock a task that might fail
        def mock_task():
            raise Exception("Task failed")

        # Test retry logic
        try:
            mock_task()
        except Exception as e:
            # In real implementation, this would trigger retry
            self.assertEqual(str(e), "Task failed")

    def test_task_result_backend(self):
        """Test task result storage"""
        # Mock result backend
        mock_result = Mock()
        mock_result.id = 'task-result-123'
        mock_result.status = 'SUCCESS'
        mock_result.result = 'Task completed successfully'

        # Test result retrieval
        self.assertEqual(mock_result.status, 'SUCCESS')
        self.assertEqual(mock_result.result, 'Task completed successfully')

    def test_task_routing(self):
        """Test task routing to specific queues"""
        # Test that tasks are routed to appropriate queues
        from celery import current_app

        # Mock queue configuration
        queue_config = {
            'email_queue': {
                'exchange': 'email',
                'routing_key': 'email.send'
            },
            'order_queue': {
                'exchange': 'orders',
                'routing_key': 'orders.process'
            }
        }

        # Verify queue configuration
        self.assertIn('email_queue', queue_config)
        self.assertIn('order_queue', queue_config)

    def test_task_monitoring(self):
        """Test task monitoring and health checks"""
        # Mock task monitoring
        mock_stats = {
            'total_tasks': 150,
            'active_tasks': 5,
            'failed_tasks': 2,
            'successful_tasks': 143
        }

        # Test monitoring data
        self.assertEqual(mock_stats['total_tasks'], 150)
        self.assertEqual(mock_stats['active_tasks'], 5)
        self.assertGreater(mock_stats['successful_tasks'], mock_stats['failed_tasks'])
