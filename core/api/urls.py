from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .. import views

router = DefaultRouter()
router.register(r'profile', views.UserProfileViewSet, basename='profile')
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'pricing', views.PricingViewSet, basename='pricing')
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', views.user_registration, name='api-register'),
    path('auth/login/', views.user_login, name='api-login'),
    path('auth/logout/', views.user_logout, name='api-logout'),
    path('health/proxy/', views.proxy_health_check, name='proxy-health'),
]