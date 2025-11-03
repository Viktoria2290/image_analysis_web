from unittest.mock import Mock, patch
from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Document, Pricing, Order
from core.services.document_service import DocumentService
from core.services.order_service import OrderService


class ServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.document = Document.objects.create(
            user=self.user,
            original_name='test.pdf',
            file_path='/uploads/test.pdf',
            size=1024,
            file_type='pdf'
        )
        self.pricing = Pricing.objects.create(
            service_name='OCR',
            price_per_unit=10.00,
            unit_type='page',
            is_active=True
        )
        self.document_service = DocumentService()
        self.order_service = OrderService()

    @patch('core.services.proxy_client.ProxyClient.post')
    def test_create_order_success(self, mock_post):
        """Тест успешного создания заказа"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'order_123',
            'status': 'pending',
            'service_type': 'ocr'
        }
        mock_post.return_value = mock_response

        result = self.order_service.create_order('doc_123', 'ocr', 1)

        self.assertEqual(result['id'], 'order_123')
        self.assertEqual(result['status'], 'pending')
        mock_post.assert_called_once_with(
            '/orders/',
            json={
                'document_id': 'doc_123',
                'service_type': 'ocr',
                'user_id': 1,
                'callback_url': ''
            }
        )

    @patch('core.services.proxy_client.ProxyClient.post')
    def test_create_order_failure(self, mock_post):
        """Тест неудачного создания заказа"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad request'
        mock_post.return_value = mock_response

        with self.assertRaises(Exception):
            self.order_service.create_order('doc_123', 'ocr', 1)

    @patch('core.services.proxy_client.ProxyClient.post')
    def test_create_order_connection_error(self, mock_post):
        """Тест создания заказа с ошибкой соединения"""
        mock_post.side_effect = Exception("Connection failed")

        with self.assertRaises(Exception):
            self.order_service.create_order('doc_123', 'ocr', 1)

    @patch('core.services.proxy_client.ProxyClient.get')
    def test_get_order_success(self, mock_get):
        """Тест успешного получения заказа"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'order_123',
            'status': 'completed',
            'service_type': 'ocr',
            'result': {'text': 'Recognized text'}
        }
        mock_get.return_value = mock_response

        result = self.order_service.get_order('order_123')

        self.assertEqual(result['id'], 'order_123')
        self.assertEqual(result['status'], 'completed')
        mock_get.assert_called_once_with('/orders/order_123/')

    @patch('core.services.proxy_client.ProxyClient.get')
    def test_get_order_not_found(self, mock_get):
        """Тест ненайденного заказа"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            self.order_service.get_order('order_123')

    @patch('core.services.proxy_client.ProxyClient.post')
    def test_upload_document_success(self, mock_post):
        """Тест успешной загрузки документа"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'doc_123',
            'status': 'uploaded',
            'file_size': 1024
        }
        mock_post.return_value = mock_response

        mock_file = Mock()
        mock_file.name = 'test.pdf'

        result = self.document_service.upload_document(
            file_obj=mock_file,
            user_id=self.user.pk,
            original_name='test.pdf'
        )

        self.assertEqual(result['id'], 'doc_123')
        self.assertEqual(result['status'], 'uploaded')
        mock_post.assert_called_once()

    @patch('core.services.proxy_client.ProxyClient.post')
    def test_upload_document_failure(self, mock_post):
        """Тест неудачной загрузки документа"""
        mock_response = Mock()
        mock_response.status_code = 413
        mock_response.text = 'File too large'
        mock_post.return_value = mock_response

        mock_file = Mock()
        mock_file.name = 'test.pdf'

        with self.assertRaises(Exception):
            self.document_service.upload_document(
                file_obj=mock_file,
                user_id=self.user.pk,
                original_name='test.pdf'
            )

    def test_calculate_order_price(self):
        """Тест расчета стоимости заказа"""
        pricing_page = Pricing.objects.create(
            service_name='OCR',
            price_per_unit=2.50,
            unit_type='page',
            is_active=True
        )

        pricing_doc = Pricing.objects.create(
            service_name='Classification',
            price_per_unit=15.00,
            unit_type='document',
            is_active=True
        )

        price_page = self.order_service.calculate_price(self.document, pricing_page)
        self.assertIsInstance(price_page, float)
        self.assertGreater(price_page, 0)

        price_doc = self.order_service.calculate_price(self.document, pricing_doc)
        self.assertEqual(price_doc, 15.00)

    def test_order_creation_with_database(self):
        """Тест создания заказа в базе данных"""
        order = Order.objects.create(
            user=self.user,
            document=self.document,
            pricing=self.pricing,
            total_price=10.00,
            status='pending'
        )

        self.assertEqual(order.user, self.user)
        self.assertEqual(order.document, self.document)
        self.assertEqual(order.pricing, self.pricing)
        self.assertEqual(order.total_price, 10.00)
        self.assertEqual(order.status, 'pending')
        self.assertTrue(order.is_pending())

    @patch('core.services.proxy_client.ProxyClient.get')
    def test_get_document_status_success(self, mock_get):
        """Тест успешного получения статуса документа"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'doc_123',
            'status': 'processed',
            'progress': 100
        }
        mock_get.return_value = mock_response

        result = self.document_service.get_document_status('doc_123')

        self.assertEqual(result['id'], 'doc_123')
        self.assertEqual(result['status'], 'processed')
        mock_get.assert_called_once_with('/api/documents/doc_123/status/')

    @patch('core.services.proxy_client.ProxyClient.post')
    def test_start_analysis_success(self, mock_post):
        """Тест успешного запуска анализа"""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.json.return_value = {
            'job_id': 'job_123',
            'status': 'started'
        }
        mock_post.return_value = mock_response

        result = self.document_service.start_analysis('doc_123', 'ocr')

        self.assertEqual(result['job_id'], 'job_123')
        self.assertEqual(result['status'], 'started')
        mock_post.assert_called_once_with('/api/analysis/start/', json={
            'document_id': 'doc_123',
            'analysis_type': 'ocr'
        })