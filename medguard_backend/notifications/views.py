"""
Views for notifications app.

This module contains API views for managing notifications, user notifications, and notification templates.
"""

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Notification, UserNotification, NotificationTemplate
from .serializers import (
    NotificationSerializer,
    UserNotificationSerializer,
    NotificationTemplateSerializer,
    NotificationDetailSerializer,
    UserNotificationDetailSerializer
)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notifications.
    
    Provides CRUD operations for system notifications with filtering and search capabilities.
    """
    
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'priority', 'status', 'is_active']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions and request parameters."""
        queryset = super().get_queryset()
        
        # Filter by active notifications if requested
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True)
        
        # Filter by dashboard visibility if requested
        if self.request.query_params.get('dashboard_only') == 'true':
            queryset = queryset.filter(show_on_dashboard=True)
        
        # Filter by expiration
        if self.request.query_params.get('not_expired') == 'true':
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve actions."""
        if self.action == 'retrieve':
            return NotificationDetailSerializer
        return NotificationSerializer
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a notification."""
        notification = self.get_object()
        notification.status = Notification.Status.ACTIVE
        notification.is_active = True
        notification.save()
        return Response({'status': 'notification activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a notification."""
        notification = self.get_object()
        notification.status = Notification.Status.INACTIVE
        notification.is_active = False
        notification.save()
        return Response({'status': 'notification deactivated'})
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a notification."""
        notification = self.get_object()
        notification.status = Notification.Status.ARCHIVED
        notification.is_active = False
        notification.save()
        return Response({'status': 'notification archived'})


class UserNotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications.
    
    Provides CRUD operations for individual user notification states.
    """
    
    serializer_class = UserNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'notification__notification_type', 'notification__priority']
    search_fields = ['notification__title', 'notification__content']
    ordering_fields = ['sent_at', 'read_at', 'acknowledged_at']
    ordering = ['-sent_at']
    
    def get_queryset(self):
        """Filter queryset to show only notifications for the current user."""
        return UserNotification.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve actions."""
        if self.action == 'retrieve':
            return UserNotificationDetailSerializer
        return UserNotificationSerializer
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a user notification as read."""
        user_notification = self.get_object()
        user_notification.mark_as_read()
        return Response({'status': 'marked as read'})
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge a user notification."""
        user_notification = self.get_object()
        user_notification.acknowledge()
        return Response({'status': 'acknowledged'})
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Dismiss a user notification."""
        user_notification = self.get_object()
        user_notification.dismiss()
        return Response({'status': 'dismissed'})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all unread notifications as read for the current user."""
        UserNotification.objects.filter(
            user=request.user,
            status=UserNotification.Status.UNREAD
        ).update(
            status=UserNotification.Status.READ,
            read_at=timezone.now()
        )
        return Response({'status': 'all notifications marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications for the current user."""
        count = UserNotification.objects.filter(
            user=request.user,
            status=UserNotification.Status.UNREAD
        ).count()
        return Response({'unread_count': count})


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification templates.
    
    Provides CRUD operations for reusable notification templates.
    """
    
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template_type', 'is_active']
    search_fields = ['name', 'subject', 'content']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter queryset based on request parameters."""
        queryset = super().get_queryset()
        
        # Filter by active templates if requested
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a notification template."""
        template = self.get_object()
        template.is_active = True
        template.save()
        return Response({'status': 'template activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a notification template."""
        template = self.get_object()
        template.is_active = False
        template.save()
        return Response({'status': 'template deactivated'})
    
    @action(detail=True, methods=['post'])
    def render_preview(self, request, pk=None):
        """Render a preview of the template with provided context."""
        template = self.get_object()
        context = request.data.get('context', {})
        
        try:
            rendered_content = template.render_content(context)
            return Response({
                'rendered_content': rendered_content,
                'template_name': template.name
            })
        except Exception as e:
            return Response(
                {'error': f'Template rendering failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
