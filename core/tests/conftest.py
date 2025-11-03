import pytest
from django.test import Client
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    return Client()

@pytest.fixture
def authenticated_client():
    client = Client()
    user = User.objects.create_user('testuser', 'test@example.com', 'testpass')
    client.force_login(user)
    return client

@pytest.fixture
def test_user():
    return User.objects.create_user('testuser', 'test@example.com', 'testpass')