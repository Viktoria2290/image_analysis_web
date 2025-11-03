import logging
from typing import Dict, Any, Optional
from django.conf import settings
from core.models import Document, Pricing
from .proxy_client import ProxyClient, ProxyClientError

logger = logging.getLogger(__name__)


class OrderService:

    def __init__(self):
        self.proxy_client = ProxyClient()

    def create_order(self, document_id: str, service_type: str, user_id: int) -> Dict[str, Any]:

        try:
            order_data = {
                'document_id': document_id,
                'service_type': service_type,
                'user_id': user_id,
                'callback_url': getattr(settings, 'PROXY_CALLBACK_URL', '')
            }

            response = self.proxy_client.create_order(order_data)
            logger.info(f"Order created in Proxy Service: {response.get('id')}")
            return response

        except ProxyClientError as e:
            logger.error(f"Failed to create order in Proxy Service: {str(e)}")
            raise

    def get_order_status(self, order_id: str) -> Dict[str, Any]:

        try:
            status_data = self.proxy_client.get_order_status(order_id)
            return status_data

        except ProxyClientError as e:
            logger.error(f"Failed to get order status from Proxy Service: {str(e)}")
            raise

    def get_order_analysis_results(self, order_id: str) -> Optional[Dict[str, Any]]:

        try:
            results = self.proxy_client.get_order_results(order_id)
            return results

        except ProxyClientError as e:
            logger.error(f"Failed to get order results from Proxy Service: {str(e)}")
            return None

    def cancel_order(self, order_id: str) -> bool:

        try:
            result = self.proxy_client.cancel_order(order_id)
            logger.info(f"Order {order_id} cancelled in Proxy Service")
            return result

        except ProxyClientError as e:
            logger.error(f"Failed to cancel order in Proxy Service: {str(e)}")
            return False

    def list_user_orders(self, user_id: int) -> list:

        try:
            orders = self.proxy_client.get_user_orders(user_id)
            return orders

        except ProxyClientError as e:
            logger.error(f"Failed to get user orders from Proxy Service: {str(e)}")
            return []

    @staticmethod
    def calculate_price(document: Document, pricing: Pricing) -> float:

        try:
            base_price = float(pricing.price_per_unit)
            if pricing.unit_type == Pricing.UNIT_PAGE:
                if document.file_type in ['pdf', 'text']:
                    estimated_pages = max(1, document.size // (50 * 1024))
                else:
                    estimated_pages = max(1, document.size // (500 * 1024))
                total_price = base_price * estimated_pages

            elif pricing.unit_type == Pricing.UNIT_DOCUMENT:
                total_price = base_price

            elif pricing.unit_type == Pricing.UNIT_MB:
                size_in_mb = document.size / (1024 * 1024)
                total_price = base_price * size_in_mb

            else:
                total_price = base_price

            return round(total_price, 2)

        except Exception as e:
            logger.error(f"Error calculating price: {str(e)}")
            return float(pricing.price_per_unit)

    def get_order(self, order_id: str) -> Dict[str, Any]:

        try:
            response = self.proxy_client.get_order(order_id)
            return response

        except Exception as e:
            logger.error(f"Failed to get order from Proxy Service: {str(e)}")
            raise