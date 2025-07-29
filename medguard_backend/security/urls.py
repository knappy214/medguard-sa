"""
URL configuration for security app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'security'

# API router for security views
router = DefaultRouter()
router.register(r'audit-logs', views.AuditLogViewSet)
router.register(r'security-events', views.SecurityEventViewSet)

urlpatterns = [
    # Security logging endpoints
    path('log/', views.log_security_event_view, name='log_security_event'),
    path('dashboard/', views.security_dashboard_view, name='security_dashboard'),
    
    # API endpoints
    path('', include(router.urls)),
] 