from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password123'
        )

    def test_user_registration(self):
        """Тест регистрации пользователя"""
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

    def test_user_login(self):
        """Тест входа пользователя"""
        url = reverse('user-login')
        data = {
            'username': 'user1',
            'password': 'password123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_logout(self):
        """Тест выхода пользователя"""
        self.client.force_login(self.user1)
        url = reverse('user-logout')

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_profile_access(self):
        """Тест доступа пользователя к своему профилю"""
        self.client.force_login(self.user1)
        url = reverse('profile-me')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_profile_update(self):
        """Тест обновления профиля пользователем"""
        self.client.force_login(self.user1)
        url = reverse('profile-me')

        data = {
            'phone': '+1234567890',
            'company': 'Test Company'
        }

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_access_other_profile(self):
        """Тест невозможности доступа к чужому профилю"""
        self.client.force_login(self.user1)
        url = reverse('profile-detail', kwargs={'pk': self.user2.pk})

        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])