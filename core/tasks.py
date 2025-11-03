from celery import shared_task
from django.utils import timezone
import logging
from .models import Document, Order
from .services import DocumentService, OrderService

logger = logging.getLogger(__name__)


@shared_task
def sync_document_status(document_id):
    """
    Синхронизация статуса документа из Proxy Service
    """
    try:
        document = Document.objects.get(id=document_id)
        if not document.proxy_document_id:
            logger.warning(f"Document {document_id} has no proxy_document_id")
            return

        document_service = DocumentService()
        status_data = document_service.get_document_status(document.proxy_document_id)

        if status_data:
            document.status = status_data.get('status', document.status)
            document.processed_at = timezone.now() if status_data.get('processed') else None
            document.external_metadata = status_data
            document.save()

            logger.info(f"Synced status for document {document_id}: {document.status}")

    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
    except Exception as e:
        logger.error(f"Error syncing document status {document_id}: {str(e)}")


@shared_task
def sync_order_status(order_id):
    """
    Синхронизация статуса заказа из Proxy Service
    """
    try:
        order = Order.objects.get(id=order_id)
        if not order.proxy_order_id:
            logger.warning(f"Order {order_id} has no proxy_order_id")
            return

        order_service = OrderService()
        status_data = order_service.get_order_status(order.proxy_order_id)

        if status_data:
            order.status = status_data.get('status', order.status)
            order.completed_at = timezone.now() if status_data.get('completed') else None
            order.external_order_data = status_data
            order.save()

            logger.info(f"Synced status for order {order_id}: {order.status}")

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
    except Exception as e:
        logger.error(f"Error syncing order status {order_id}: {str(e)}")


@shared_task
def start_document_analysis(document_id, analysis_type='ocr'):
    """
    Запуск анализа документа в Proxy Service
    """
    try:
        document = Document.objects.get(id=document_id)
        if not document.proxy_document_id:
            logger.warning(f"Document {document_id} has no proxy_document_id")
            return

        document_service = DocumentService()
        analysis_data = document_service.start_analysis(document.proxy_document_id, analysis_type)

        if analysis_data:
            document.status = 'processing'
            document.external_metadata = analysis_data
            document.save()

            logger.info(f"Started analysis for document {document_id}: {analysis_data.get('job_id')}")

    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
    except Exception as e:
        logger.error(f"Error starting analysis for document {document_id}: {str(e)}")
        try:
            document = Document.objects.get(id=document_id)
            document.status = 'failed'
            document.save()
        except Document.DoesNotExist:
            logger.error(f"Document {document_id} not found when trying to set failed status")


@shared_task
def check_proxy_service_health():
    """
    Периодическая задача проверки здоровья Proxy Service
    """
    from .services import ProxyClient

    try:
        proxy_client = ProxyClient()
        is_healthy = proxy_client.health_check()

        logger.info(f"Proxy Service health check: {'HEALTHY' if is_healthy else 'UNHEALTHY'}")
        return is_healthy

    except Exception as e:
        logger.error(f"Proxy Service health check failed: {str(e)}")
        return False