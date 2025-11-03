from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
import json
from .models import UserProfile, Document, Pricing, Order
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer,
    DocumentSerializer, PricingSerializer, OrderSerializer
)
from .permissions import IsDocumentOwner, IsOrderOwner
from .services import DocumentService, OrderService, ProxyClientError


class IsProfileOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


def home_view(_request):
    return render(_request, 'core/index.html')


@login_required
def profile_view(_request):
    return render(_request, 'core/profile.html')


@login_required
def documents_view(_request):
    return redirect('upload_document')


@login_required
def upload_document_view(_request):
    return render(_request, 'core/documents/upload.html')


@login_required
def orders_view(_request):
    return render(_request, 'core/orders/list.html')


@login_required
def gallery_view(_request):
    return render(_request, 'core/gallery.html')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(_request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return Response({
        "status": "healthy",
        "database": db_status,
        "timestamp": timezone.now().isoformat()
    })


class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwner]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get', 'put'])
    def me(self, request):
        if hasattr(self.request.user, 'profile'):
            profile = self.request.user.profile
        else:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        elif request.method == 'PUT':
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsDocumentOwner]

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user).order_by('-uploaded_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            if 'file' not in request.FILES:
                return Response(
                    {'error': 'No file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file_obj = request.FILES['file']
            original_name = file_obj.name

            document_service = DocumentService()
            proxy_document_data = document_service.upload_document(
                file_obj, request.user.id, original_name
            )

            document_data = {
                'user': request.user.id,
                'file_path': proxy_document_data.get('file_path', ''),
                'original_name': original_name,
                'size': proxy_document_data.get('size', file_obj.size),
                'file_type': self._get_file_type(original_name),
                'status': 'uploaded',
                'proxy_document_id': proxy_document_data.get('id'),
                'external_metadata': proxy_document_data
            }

            serializer = self.get_serializer(data=document_data)
            serializer.is_valid(raise_exception=True)
            document = serializer.save()

            from .tasks import start_document_analysis
            start_document_analysis.delay(document.id, 'ocr')

            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )

        except ProxyClientError as e:
            return Response(
                {'error': f'Proxy Service error: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except (ValueError, KeyError, AttributeError, IOError) as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def _get_file_type(filename):
        extension = filename.lower().split('.')[-1]
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']
        pdf_extensions = ['pdf']
        text_extensions = ['txt', 'doc', 'docx']

        if extension in image_extensions:
            return 'image'
        elif extension in pdf_extensions:
            return 'pdf'
        elif extension in text_extensions:
            return 'text'
        else:
            return 'other'

    @action(detail=True, methods=['post'])
    def process(self, _request, _pk=None):
        document = self.get_object()
        document.status = 'processing'
        document.save()
        return Response({'status': 'processing started'})

    @action(detail=True, methods=['get'])
    def sync_status(self, _request, _pk=None):
        document = self.get_object()
        from .tasks import sync_document_status
        sync_document_status.delay(document.id)
        return Response({'status': 'sync started'})

    @action(detail=True, methods=['get'])
    def analysis_results(self, _request, _pk=None):
        document = self.get_object()
        if not document.proxy_document_id:
            return Response(
                {'error': 'Document not uploaded to Proxy Service'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            document_service = DocumentService()
            results = document_service.get_document_analysis(document.proxy_document_id)

            if results:
                document.analysis_result = results
                document.save()
                return Response(results)
            else:
                return Response(
                    {'error': 'Analysis results not available'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except ProxyClientError as e:
            return Response(
                {'error': f'Proxy Service error: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class PricingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pricing.objects.filter(is_active=True)
    serializer_class = PricingSerializer
    permission_classes = [permissions.IsAuthenticated]


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderOwner]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            if request.content_type == 'application/json':
                try:
                    json.loads(request.body)
                except json.JSONDecodeError:
                    return Response(
                        {'error': 'Invalid JSON payload'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            validated_data = serializer.validated_data
            document = validated_data['document']
            pricing = validated_data['pricing']

            if document.status not in ['uploaded', 'completed']:
                return Response(
                    {'error': 'Document not ready for analysis'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            order_service = OrderService()
            proxy_order_data = order_service.create_order(
                document.proxy_document_id or 'test_document_id',
                pricing.service_name.lower(),
                request.user.id
            )

            total_price = pricing.price_per_unit

            order_data = {
                'user': request.user.id,
                'document': document.id,
                'pricing': pricing.id,
                'total_price': total_price,
                'status': 'pending',
                'proxy_order_id': proxy_order_data.get('id'),
                'external_order_data': proxy_order_data
            }

            order_serializer = self.get_serializer(data=order_data)
            order_serializer.is_valid(raise_exception=True)
            order = order_serializer.save()

            from .tasks import sync_order_status
            sync_order_status.delay(order.id)

            headers = self.get_success_headers(order_serializer.data)
            return Response(
                order_serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )

        except ProxyClientError as e:
            return Response(
                {'error': f'Proxy Service error: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except (ValueError, KeyError, AttributeError) as e:
            return Response(
                {'error': f'Order creation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def cancel(self, _request, _pk=None):
        order = self.get_object()
        if order.status in ['pending', 'processing']:
            order.status = 'cancelled'
            order.save()

            if order.proxy_order_id:
                try:
                    order_service = OrderService()
                    order_service.cancel_order(order.proxy_order_id)
                except ProxyClientError:
                    pass

            return Response({'status': 'order cancelled'})
        return Response(
            {'error': 'Cannot cancel completed or already cancelled order'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['get'])
    def sync_status(self, _request, _pk=None):
        order = self.get_object()
        from .tasks import sync_order_status
        sync_order_status.delay(order.id)
        return Response({'status': 'sync started'})

    @action(detail=True, methods=['get'])
    def results(self, _request, _pk=None):
        order = self.get_object()
        if not order.proxy_order_id:
            return Response(
                {'error': 'Order not created in Proxy Service'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order_service = OrderService()
            results = order_service.get_order_analysis_results(order.proxy_order_id)

            if results:
                order.external_order_data = results
                order.save()
                return Response(results)
            else:
                return Response(
                    {'error': 'Order results not available'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except ProxyClientError as e:
            return Response(
                {'error': f'Proxy Service error: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_registration(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        login(request, user)
        return Response(
            {'message': 'User registered successfully'},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        return Response({'message': 'Login successful'})
    else:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
def user_logout(_request):
    logout(_request)
    return Response({'message': 'Logout successful'})


@api_view(['GET'])
def proxy_health_check(_request):
    from .services import ProxyClient

    try:
        proxy_client = ProxyClient()
        is_healthy = proxy_client.health_check()
        status_data = proxy_client.get_service_status()

        return Response({
            'proxy_service_healthy': is_healthy,
            'proxy_service_status': status_data,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return Response({
            'proxy_service_healthy': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)