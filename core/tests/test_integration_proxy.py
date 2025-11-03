import requests
import jwt
import time
from django.conf import settings
from django.core.cache import cache
from requests.adapters import HTTPAdapter
import logging

logger = logging.getLogger(__name__)


class ProxyClientError(Exception):
    pass


class ProxyAuthenticationError(ProxyClientError):
    pass


class ProxyConnectionError(ProxyClientError):
    pass


class ProxyClient:
    """
    HTTP клиент для взаимодействия с Proxy Service (порт 5000)
    Обрабатывает JWT аутентификацию, повторные попытки и обработку ошибок
    """

    def __init__(self):
        self.base_url = settings.PROXY_SERVICE_URL
        self.jwt_secret = settings.PROXY_JWT_SECRET
        self.token_cache_key = 'proxy_jwt_token'

        self.session = requests.Session()

        adapter = HTTPAdapter(max_retries=3)
        self.session.mount("https://", adapter)

        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Django-Web-Service/1.0'
        })

    def _get_jwt_token(self):
        token = cache.get(self.token_cache_key)

        if not token:
            token = self._generate_jwt_token()
            cache.set(self.token_cache_key, token, 55 * 60)

        return token

    def _generate_jwt_token(self):
        try:
            payload = {
                'service': 'django_web',
                'iat': int(time.time()),
                'exp': int(time.time()) + 3600,
                'permissions': ['documents:read', 'documents:write', 'analysis:create']
            }

            token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
            return token

        except Exception as e:
            logger.error(f"JWT token generation failed: {str(e)}")
            raise ProxyAuthenticationError(f"JWT token generation failed: {str(e)}")

    def _refresh_token(self):
        cache.delete(self.token_cache_key)
        return self._get_jwt_token()

    def _make_request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}{endpoint}"

        try:
            token = self._get_jwt_token()
            headers = kwargs.get('headers', {})
            headers['Authorization'] = f'Bearer {token}'
            kwargs['headers'] = headers

            logger.info(f"Making {method} request to {url}")
            response = self.session.request(method, url, **kwargs)

            if response.status_code == 401:
                logger.warning("Token expired, refreshing...")
                token = self._refresh_token()
                headers['Authorization'] = f'Bearer {token}'
                response = self.session.request(method, url, **kwargs)

            logger.info(f"Response status: {response.status_code}")

            return response

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to Proxy Service: {str(e)}")
            raise ProxyConnectionError(f"Cannot connect to Proxy Service: {str(e)}")

        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error to Proxy Service: {str(e)}")
            raise ProxyConnectionError(f"Proxy Service timeout: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error communicating with Proxy Service: {str(e)}")
            raise ProxyClientError(f"Proxy Service communication error: {str(e)}")

    def get(self, endpoint, **kwargs):
        return self._make_request('GET', endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self._make_request('POST', endpoint, **kwargs)

    def put(self, endpoint, **kwargs):
        return self._make_request('PUT', endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        return self._make_request('DELETE', endpoint, **kwargs)

    def health_check(self):
        """
        Проверка доступности Proxy Service
        """
        try:
            response = self.get('/health/')
            return response.status_code == 200
        except ProxyClientError:
            return False

    def get_service_status(self):
        """
        Получение статуса и метрик Proxy Service
        """
        try:
            response = self.get('/status/')
            if response.status_code == 200:
                return response.json()
            return None
        except ProxyClientError as e:
            logger.error(f"Failed to get service status: {str(e)}")
            return None