"""
Security views for audit logging and security monitoring.

This module provides API endpoints for security logging and monitoring
for HIPAA compliance and South African POPIA regulations.
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.contrib.auth import get_user_model

from .audit import AuditLog, log_audit_event, get_audit_logger
from .models import SecurityEvent
from .serializers import AuditLogSerializer, SecurityEventSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs.
    
    Provides read-only access to audit logs with filtering and search capabilities.
    Only accessible by admin users for security compliance.
    """
    
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'severity', 'user', 'content_type', 'timestamp']
    search_fields = ['description', 'object_repr', 'ip_address', 'user_agent']
    ordering_fields = ['timestamp', 'action', 'severity', 'user']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter queryset based on request parameters."""
        queryset = super().get_queryset()
        
        # Date range filtering
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__gte=start_datetime)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(timestamp__lt=end_datetime)
            except ValueError:
                pass
        
        # User filtering
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Action type filtering
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action=action_type)
        
        # Severity filtering
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # IP address filtering
        ip_address = self.request.query_params.get('ip_address')
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get audit log summary statistics."""
        try:
            # Get date range from query parameters
            days = int(request.query_params.get('days', 30))
            start_date = timezone.now() - timedelta(days=days)
            
            # Filter logs for the date range
            logs = self.get_queryset().filter(timestamp__gte=start_date)
            
            # Calculate statistics
            total_actions = logs.count()
            actions_by_type = logs.values('action').annotate(count=Count('id')).order_by('-count')
            actions_by_severity = logs.values('severity').annotate(count=Count('id')).order_by('-count')
            actions_by_user = logs.values('user__username').annotate(count=Count('id')).order_by('-count')[:10]
            
            # Get recent security events
            recent_security_events = logs.filter(
                Q(severity__in=['high', 'critical']) | 
                Q(action__in=['login_failed', 'access_denied', 'breach_attempt'])
            ).order_by('-timestamp')[:10]
            
            return Response({
                'total_actions': total_actions,
                'actions_by_type': list(actions_by_type),
                'actions_by_severity': list(actions_by_severity),
                'top_users': list(actions_by_user),
                'recent_security_events': AuditLogSerializer(recent_security_events, many=True).data,
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': timezone.now().isoformat(),
                    'days': days
                }
            })
            
        except Exception as e:
            logger.error(f"Audit log summary error: {str(e)}")
            return Response({
                'error': 'Failed to generate summary'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export audit logs to CSV format."""
        try:
            from django.http import HttpResponse
            import csv
            
            # Get filtered queryset
            queryset = self.get_queryset()
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="audit_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            writer = csv.writer(response)
            
            # Write header
            writer.writerow([
                'Timestamp', 'User', 'Action', 'Severity', 'Object', 'IP Address',
                'User Agent', 'Description', 'Metadata'
            ])
            
            # Write data
            for log in queryset:
                writer.writerow([
                    log.timestamp.isoformat(),
                    log.user.username if log.user else 'Anonymous',
                    log.action,
                    log.severity,
                    log.object_repr,
                    log.ip_address,
                    log.user_agent,
                    log.description,
                    str(log.metadata)
                ])
            
            # Log the export action
            log_audit_event(
                user=request.user,
                action='audit_log_export',
                description=f'Audit logs exported by {request.user.username}',
                severity='medium',
                request=request,
                metadata={'export_format': 'csv', 'record_count': queryset.count()}
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Audit log export error: {str(e)}")
            return Response({
                'error': 'Failed to export audit logs'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SecurityEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing security events.
    
    Provides read-only access to security events with filtering capabilities.
    Only accessible by admin users for security compliance.
    """
    
    queryset = SecurityEvent.objects.all()
    serializer_class = SecurityEventSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'severity', 'user', 'timestamp']
    search_fields = ['description', 'ip_address', 'user_agent']
    ordering_fields = ['timestamp', 'event_type', 'severity']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter queryset based on request parameters."""
        queryset = super().get_queryset()
        
        # Date range filtering
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__gte=start_datetime)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(timestamp__lt=end_datetime)
            except ValueError:
                pass
        
        # Event type filtering
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Severity filtering
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_security_event_view(request):
    """
    API endpoint to log security events.
    
    This endpoint allows authenticated users to log security events
    for monitoring and compliance purposes.
    """
    try:
        event_type = request.data.get('event_type')
        description = request.data.get('description')
        severity = request.data.get('severity', 'medium')
        metadata = request.data.get('metadata', {})
        
        if not event_type or not description:
            return Response({
                'error': 'event_type and description are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Log the security event
        log_audit_event(
            user=request.user,
            action=event_type,
            description=description,
            severity=severity,
            request=request,
            metadata=metadata
        )
        
        return Response({
            'message': 'Security event logged successfully'
        })
        
    except Exception as e:
        logger.error(f"Security event logging error: {str(e)}")
        return Response({
            'error': 'Failed to log security event'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def security_dashboard_view(request):
    """
    Security dashboard view providing overview of security metrics.
    """
    try:
        # Get date range from query parameters
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # Get audit logs for the period
        audit_logs = AuditLog.objects.filter(timestamp__gte=start_date)
        
        # Calculate security metrics
        total_events = audit_logs.count()
        failed_logins = audit_logs.filter(action='login_failed').count()
        access_denied = audit_logs.filter(action='access_denied').count()
        security_events = audit_logs.filter(severity__in=['high', 'critical']).count()
        
        # Get recent security incidents
        recent_incidents = audit_logs.filter(
            Q(severity__in=['high', 'critical']) |
            Q(action__in=['login_failed', 'access_denied', 'breach_attempt'])
        ).order_by('-timestamp')[:5]
        
        # Get top IP addresses with failed attempts
        suspicious_ips = audit_logs.filter(
            action='login_failed'
        ).values('ip_address').annotate(
            count=Count('id')
        ).filter(count__gte=3).order_by('-count')[:5]
        
        return Response({
            'metrics': {
                'total_events': total_events,
                'failed_logins': failed_logins,
                'access_denied': access_denied,
                'security_events': security_events,
                'suspicious_ips': len(suspicious_ips)
            },
            'recent_incidents': AuditLogSerializer(recent_incidents, many=True).data,
            'suspicious_ips': list(suspicious_ips),
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': timezone.now().isoformat(),
                'days': days
            }
        })
        
    except Exception as e:
        logger.error(f"Security dashboard error: {str(e)}")
        return Response({
            'error': 'Failed to generate security dashboard'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 