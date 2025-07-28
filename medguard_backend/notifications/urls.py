"""
URL configuration for notifications app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'notifications'

# API router for notifications
router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet)
router.register(r'user-notifications', views.UserNotificationViewSet, basename='user-notification')
router.register(r'templates', views.NotificationTemplateViewSet)

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
] 