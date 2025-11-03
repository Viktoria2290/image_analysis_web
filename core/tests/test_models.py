from django.test import TestCase
from django.contrib.auth.models import User
from ..models import UserProfile, Document, Pricing, Order


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.get(user=self.user)

    def test_user_profile_creation(self):
        """Тест автоматического создания UserProfile с User"""
        self.assertIsInstance(self.profile, UserProfile)
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(str(self.profile), "testuser Profile")

    def test_document_creation(self):
        """Тест создания модели Document и методов"""
        document = Document.objects.create(
            user=self.user,
            original_name='test.pdf',
            file_path='/uploads/test.pdf',
            size=1024,
            file_type='pdf',
            status='uploaded'
        )

        self.assertEqual(document.get_file_type_display(), 'PDF')
        self.assertEqual(str(document), 'test.pdf')
        self.assertTrue(document.is_uploaded())

        document.status = 'processing'
        self.assertTrue(document.is_processing())

    def test_pricing_model(self):
        """Тест модели Pricing"""
        pricing = Pricing.objects.create(
            service_name='OCR',
            description='Optical Character Recognition',
            price_per_unit=10.00,
            unit_type='page',
            is_active=True
        )

        self.assertEqual(str(pricing), 'OCR - $10.00')
        self.assertTrue(pricing.is_active)

    def test_order_creation(self):
        """Тест создания модели Order и методов"""
        document = Document.objects.create(
            user=self.user,
            original_name='test.pdf',
            file_path='/uploads/test.pdf',
            size=1024,
            file_type='pdf'
        )

        pricing = Pricing.objects.create(
            service_name='OCR',
            price_per_unit=10.00,
            unit_type='page',
            is_active=True
        )

        order = Order.objects.create(
            user=self.user,
            document=document,
            pricing=pricing,
            total_price=10.00,
            status='pending'
        )

        self.assertEqual(str(order), f"Order #{order.pk} - test.pdf")
        self.assertTrue(order.can_be_cancelled())

        order.status = 'completed'
        self.assertFalse(order.can_be_cancelled())