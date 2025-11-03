from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from ..models import Document, Pricing, Order


class APITests(TestCase):

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=False)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.document = Document.objects.create(
            user=self.user,
            original_name='test.pdf',
            file_path='/uploads/test.pdf',
            size=1024,
            file_type='pdf',
            status='uploaded'
        )

        self.pricing = Pricing.objects.create(
            service_name='OCR',
            price_per_unit=10.00,
            unit_type='page',
            is_active=True
        )

        self.order = Order.objects.create(
            user=self.user,
            document=self.document,
            pricing=self.pricing,
            total_price=10.00,
            status='pending'
        )

    def test_user_registration_success(self):
        """Тест успешной регистрации пользователя"""
        url = reverse('user-registration')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_login_success(self):
        """Тест успешного входа пользователя"""
        url = reverse('user-login')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.json())

    def test_user_login_invalid_credentials(self):
        """Тест входа с неверными учетными данными"""
        url = reverse('user-login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.json())

    def test_get_documents_authenticated(self):
        """Тест получения списка документов при аутентификации"""
        self.client.force_login(self.user)
        url = reverse('document-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_documents_unauthenticated(self):
        """Тест получения списка документов без аутентификации"""
        url = reverse('document-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_order_invalid_document(self):
        """Тест создания заказа с несуществующим документом"""
        self.client.force_login(self.user)
        url = reverse('order-list')

        data = {
            'document': 999,
            'pricing': self.pricing.pk
        }

        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])