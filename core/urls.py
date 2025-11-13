from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'profiles', views.UserProfileViewSet, basename='profile')
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'pricing', views.PricingViewSet, basename='pricing')
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns = [
    # API routes
    path('api/', include(router.urls)),
    path('api/auth/register/', views.user_registration, name='user-registration'),
    path('api/auth/login/', views.user_login, name='user-login'),
    path('api/auth/logout/', views.user_logout, name='user-logout'),
    path('api/health/', views.health_check, name='health-check'),
    path('api/health/proxy/', views.proxy_health_check, name='proxy-health-check'),

    # Web routes
    path('', views.home_view, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('documents/', views.documents_view, name='documents'),
    path('documents/upload/', views.upload_document_view, name='upload_document'),
    path('orders/', views.orders_view, name='orders'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('login-form/', views.login_form_view, name='login-form'),  # ← ДОБАВЛЕНО
]