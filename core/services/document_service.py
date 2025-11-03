import os
import uuid
from .proxy_client import ProxyClient, ProxyClientError, ProxyConnectionError
import logging

logger = logging.getLogger(__name__)


class DocumentService:


    def __init__(self):
        self.proxy_client = ProxyClient()

    def upload_document(self, file_obj, user_id, original_name):

        try:

            file_extension = os.path.splitext(original_name)[1]
            file_path = f"users/{user_id}/{uuid.uuid4()}{file_extension}"


            files = {
                'file': (original_name, file_obj, f'application/{file_extension[1:]}')
            }

            data = {
                'file_path': file_path,
                'user_id': str(user_id),
                'original_name': original_name
            }


            response = self.proxy_client.post('/api/documents/upload/', files=files, data=data)

            if response.status_code == 201:
                document_data = response.json()
                logger.info(f"Document uploaded successfully: {document_data['id']}")
                return document_data
            else:
                logger.error(f"Document upload failed: {response.status_code} - {response.text}")
                raise ProxyClientError(f"Upload failed: {response.text}")

        except ProxyConnectionError as e:
            logger.error(f"Connection error during document upload: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during document upload: {str(e)}")
            raise ProxyClientError(f"Document upload failed: {str(e)}")

    def get_document_status(self, proxy_document_id):
        try:
            response = self.proxy_client.get(f'/api/documents/{proxy_document_id}/status/')

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get document status: {response.status_code}")
                return None

        except ProxyClientError as e:
            logger.error(f"Error getting document status: {str(e)}")
            return None

    def get_document_analysis(self, proxy_document_id):
        try:
            response = self.proxy_client.get(f'/api/documents/{proxy_document_id}/analysis/')

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Analysis not available: {response.status_code}")
                return None

        except ProxyClientError as e:
            logger.error(f"Error getting document analysis: {str(e)}")
            return None

    def delete_document(self, proxy_document_id):
        try:
            response = self.proxy_client.delete(f'/api/documents/{proxy_document_id}/')

            if response.status_code in [200, 204]:
                logger.info(f"Document deleted from Proxy Service: {proxy_document_id}")
                return True
            else:
                logger.error(f"Failed to delete document: {response.status_code}")
                return False

        except ProxyClientError as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False

    def start_analysis(self, proxy_document_id, analysis_type='ocr'):
        try:
            data = {
                'document_id': proxy_document_id,
                'analysis_type': analysis_type
            }

            response = self.proxy_client.post('/api/analysis/start/', json=data)

            if response.status_code == 202:
                job_data = response.json()
                logger.info(f"Analysis started: {job_data['job_id']}")
                return job_data
            else:
                logger.error(f"Failed to start analysis: {response.status_code}")
                raise ProxyClientError(f"Analysis start failed: {response.text}")

        except ProxyClientError as e:
            logger.error(f"Error starting analysis: {str(e)}")
            raise

    def get_analysis_status(self, job_id):
        try:
            response = self.proxy_client.get(f'/api/analysis/{job_id}/status/')

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Analysis status not available: {response.status_code}")
                return None

        except ProxyClientError as e:
            logger.error(f"Error getting analysis status: {str(e)}")
            return None

    def list_user_documents(self, user_id):

        try:
            response = self.proxy_client.get(f'/api/documents/?user_id={user_id}')

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to list documents: {response.status_code}")
                return []

        except ProxyClientError as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []