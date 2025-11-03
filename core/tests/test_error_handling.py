from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
import os
import tempfile
from ..services import ProxyClientError


class ErrorHandlingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @patch('core.views.DocumentService.upload_document')
    def test_document_upload_proxy_error(self, mock_upload):
        """Тест обработки ошибок Proxy Service при загрузке документа"""
        mock_upload.side_effect = ProxyClientError("Proxy service unavailable")

        self.client.force_login(self.user)
        url = reverse('document-list')

        # Создаем временный файл для теста
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b'fake pdf content')
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as file:
                data = {'file': file}
                response = self.client.post(url, data, format='multipart')
        finally:
            # Удаляем временный файл
            os.unlink(temp_file_path)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('error', response.json())
        self.assertIn('Proxy Service error', response.json()['error'])

    @patch('core.views.OrderService.create_order')
    def test_order_creation_proxy_error(self, mock_create):
        """Тест обработки ошибок Proxy Service при создании заказа"""
        from ..models import Document, Pricing

        document = Document.objects.create(
            user=self.user,
            original_name='test.pdf',
            file_path='/uploads/test.pdf',
            size=1024,
            file_type='pdf',
            status='uploaded',
            proxy_document_id='test_document_id_123'
        )

        pricing = Pricing.objects.create(
            service_name='OCR',
            price_per_unit=10.00,
            is_active=True
        )

        mock_create.side_effect = ProxyClientError("Order creation failed")

        self.client.force_login(self.user)
        url = reverse('order-list')

        data = {
            'document': document.pk,
            'pricing': pricing.pk
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('error', response.json())

    def test_invalid_json_payload(self):
        """Тест обработки невалидного JSON payload"""
        self.client.force_login(self.user)
        url = reverse('order-list')

        response = self.client.post(
            url,
            'invalid json data',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_resource(self):
        """Тест обработки запросов к несуществующим ресурсам"""
        self.client.force_login(self.user)
        url = reverse('document-detail', kwargs={'pk': 9999})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_method_not_allowed(self):
        """Тест обработки неподдерживаемых HTTP методов"""
        self.client.force_login(self.user)
        url = reverse('document-list')

        response = self.client.put(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)