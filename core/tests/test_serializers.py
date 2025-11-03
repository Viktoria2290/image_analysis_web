from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from ..models import Document, Pricing
from ..serializers import (
    UserRegistrationSerializer,
    DocumentSerializer,
    OrderSerializer
)


class SerializerTests(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.factory = APIRequestFactory()

    def test_user_registration_serializer_valid(self):
        """Тест валидных данных регистрации пользователя"""
        serializer = UserRegistrationSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())

    def test_user_registration_serializer_missing_username(self):
        """Тест отсутствия имени пользователя"""
        invalid_data = self.user_data.copy()
        invalid_data.pop('username')

        serializer = UserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_user_registration_serializer_missing_password(self):
        """Тест отсутствия пароля"""
        invalid_data = self.user_data.copy()
        invalid_data.pop('password')

        serializer = UserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_user_registration_serializer_valid_without_email(self):
        """Тест валидной регистрации без email (email опционально)"""
        data_without_email = {
            'username': 'testuser2',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        serializer = UserRegistrationSerializer(data=data_without_email)
        self.assertTrue(serializer.is_valid())

    def test_document_serializer_valid(self):
        """Тест валидных данных документа"""
        user = User.objects.create_user('testuser', 'test@example.com', 'testpass')

        # Получим допустимые значения file_type из модели
        file_type_choices = Document._meta.get_field('file_type').choices
        valid_file_type = file_type_choices[0][0] if file_type_choices else 'image/jpeg'

        document_data = {
            'user': user.pk,
            'original_name': 'test.pdf',
            'file_path': '/uploads/test.pdf',
            'size': 1024,
            'file_type': valid_file_type,
            'status': 'uploaded'
        }

        serializer = DocumentSerializer(data=document_data)
        if not serializer.is_valid():
            print("DocumentSerializer errors:", serializer.errors)
        self.assertTrue(serializer.is_valid())

    def test_document_serializer_invalid_file_type(self):
        """Тест невалидного типа файла"""
        user = User.objects.create_user('testuser', 'test@example.com', 'testpass')

        document_data = {
            'user': user.pk,
            'original_name': 'test.pdf',
            'file_path': '/uploads/test.pdf',
            'size': 1024,
            'file_type': 'invalid_type',  # Невалидный тип
            'status': 'uploaded'
        }

        serializer = DocumentSerializer(data=document_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('file_type', serializer.errors)

    def test_order_serializer_valid(self):
        """Тест валидных данных заказа"""
        user = User.objects.create_user('testuser', 'test@example.com', 'testpass')

        # Используем правильный file_type
        file_type_choices = Document._meta.get_field('file_type').choices
        valid_file_type = file_type_choices[0][0] if file_type_choices else 'image/jpeg'

        document = Document.objects.create(
            user=user,
            original_name='test.pdf',
            file_path='/uploads/test.pdf',
            size=1024,
            file_type=valid_file_type
        )
        pricing = Pricing.objects.create(
            service_name='OCR',
            price_per_unit=10.00,
            unit_type='page',
            is_active=True
        )

        request = self.factory.post('/')
        request.user = user

        order_data = {
            'user': user.pk,
            'document': document.pk,
            'pricing': pricing.pk,
            'total_price': 10.00,
            'status': 'pending'
        }

        serializer = OrderSerializer(data=order_data, context={'request': request})
        if not serializer.is_valid():
            print("OrderSerializer errors:", serializer.errors)
        self.assertTrue(serializer.is_valid())

    def test_order_serializer_invalid_document(self):
        """Тест заказа с документом, не принадлежащим пользователю"""
        user1 = User.objects.create_user('testuser1', 'test1@example.com', 'testpass')
        user2 = User.objects.create_user('testuser2', 'test2@example.com', 'testpass')

        # Используем правильный file_type
        file_type_choices = Document._meta.get_field('file_type').choices
        valid_file_type = file_type_choices[0][0] if file_type_choices else 'image/jpeg'

        document = Document.objects.create(
            user=user2,
            original_name='test.pdf',
            file_path='/uploads/test.pdf',
            size=1024,
            file_type=valid_file_type
        )
        pricing = Pricing.objects.create(
            service_name='OCR',
            price_per_unit=10.00,
            unit_type='page',
            is_active=True
        )

        request = self.factory.post('/')
        request.user = user1

        order_data = {
            'user': user1.pk,
            'document': document.pk,
            'pricing': pricing.pk,
            'total_price': 10.00,
            'status': 'pending'
        }

        serializer = OrderSerializer(data=order_data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('document', serializer.errors)