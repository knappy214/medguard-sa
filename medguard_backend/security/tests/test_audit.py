"""
Tests for audit logging system.

These tests ensure that all HIPAA-required audit trails are properly
created and maintained.
"""

import json
from datetime import datetime, timedelta
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.exceptions import ValidationError

from security.audit import AuditLog, AuditLogger, log_audit_event
from security.hipaa_compliance import get_compliance_monitor

User = get_user_model()


class AuditLogModelTest(TestCase):
    """Test AuditLog model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = RequestFactory()
    
    def test_audit_log_creation(self):
        """Test basic audit log creation."""
        audit_log = AuditLog.objects.create(
            user=self.user,
            action=AuditLog.ActionType.READ,
            content_type=ContentType.objects.get_for_model(User),
            object_id=self.user.id,
            object_repr=str(self.user),
            description="Test audit log entry",
            severity=AuditLog.Severity.LOW
        )
        
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, AuditLog.ActionType.READ)
        self.assertEqual(audit_log.severity, AuditLog.Severity.LOW)
        self.assertTrue(audit_log.retention_date)
    
    def test_retention_date_auto_set(self):
        """Test that retention date is automatically set."""
        audit_log = AuditLog.objects.create(
            user=self.user,
            action=AuditLog.ActionType.READ,
            content_type=ContentType.objects.get_for_model(User),
            object_id=self.user.id,
            object_repr=str(self.user),
            description="Test audit log entry"
        )
        
        # Check that retention date is set to 7 years from now
        expected_retention = timezone.now() + timedelta(days=2555)
        self.assertAlmostEqual(
            audit_log.retention_date,
            expected_retention,
            delta=timedelta(seconds=10)
        )
    
    def test_sensitive_action_detection(self):
        """Test detection of sensitive actions."""
        # Test sensitive actions
        sensitive_actions = [
            AuditLog.ActionType.READ,
            AuditLog.ActionType.UPDATE,
            AuditLog.ActionType.DELETE,
            AuditLog.ActionType.EXPORT,
        ]
        
        for action in sensitive_actions:
            audit_log = AuditLog.objects.create(
                user=self.user,
                action=action,
                content_type=ContentType.objects.get_for_model(User),
                object_id=self.user.id,
                object_repr=str(self.user),
                description="Test sensitive action"
            )
            self.assertTrue(audit_log.is_sensitive_action)
        
        # Test non-sensitive actions
        non_sensitive_actions = [
            AuditLog.ActionType.CREATE,
            AuditLog.ActionType.LOGIN,
            AuditLog.ActionType.LOGOUT,
        ]
        
        for action in non_sensitive_actions:
            audit_log = AuditLog.objects.create(
                user=self.user,
                action=action,
                content_type=ContentType.objects.get_for_model(User),
                object_id=self.user.id,
                object_repr=str(self.user),
                description="Test non-sensitive action"
            )
            self.assertFalse(audit_log.is_sensitive_action)
    
    def test_requires_review_detection(self):
        """Test detection of actions requiring review."""
        # Test high severity actions
        high_severity_actions = [
            AuditLog.Severity.HIGH,
            AuditLog.Severity.CRITICAL,
        ]
        
        for severity in high_severity_actions:
            audit_log = AuditLog.objects.create(
                user=self.user,
                action=AuditLog.ActionType.READ,
                content_type=ContentType.objects.get_for_model(User),
                object_id=self.user.id,
                object_repr=str(self.user),
                description="Test high severity action",
                severity=severity
            )
            self.assertTrue(audit_log.requires_review)
        
        # Test low severity actions
        low_severity_actions = [
            AuditLog.Severity.LOW,
            AuditLog.Severity.MEDIUM,
        ]
        
        for severity in low_severity_actions:
            audit_log = AuditLog.objects.create(
                user=self.user,
                action=AuditLog.ActionType.READ,
                content_type=ContentType.objects.get_for_model(User),
                object_id=self.user.id,
                object_repr=str(self.user),
                description="Test low severity action",
                severity=severity
            )
            self.assertFalse(audit_log.requires_review)


class AuditLoggerTest(TestCase):
    """Test AuditLogger functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = RequestFactory()
        self.audit_logger = AuditLogger()
    
    def test_log_action_basic(self):
        """Test basic action logging."""
        audit_log = self.audit_logger.log_action(
            user=self.user,
            action=AuditLog.ActionType.READ,
            obj=self.user,
            description="Test action logging"
        )
        
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, AuditLog.ActionType.READ)
        self.assertEqual(audit_log.object_repr, str(self.user))
    
    def test_log_action_with_request(self):
        """Test action logging with request context."""
        request = self.factory.get('/test/')
        request.META['HTTP_USER_AGENT'] = 'Test Browser'
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        audit_log = self.audit_logger.log_action(
            user=self.user,
            action=AuditLog.ActionType.READ,
            obj=self.user,
            description="Test action with request",
            request=request
        )
        
        self.assertEqual(audit_log.ip_address, '127.0.0.1')
        self.assertEqual(audit_log.user_agent, 'Test Browser')
        self.assertEqual(audit_log.request_path, '/test/')
        self.assertEqual(audit_log.request_method, 'GET')
    
    def test_log_medication_access(self):
        """Test medication-specific access logging."""
        audit_log = self.audit_logger.log_medication_access(
            user=self.user,
            medication=self.user,  # Using user as placeholder for medication
            action=AuditLog.ActionType.READ,
            description="Test medication access"
        )
        
        self.assertEqual(audit_log.severity, AuditLog.Severity.MEDIUM)
        self.assertIn('medication_type', audit_log.metadata)
    
    def test_log_patient_data_access(self):
        """Test patient data access logging."""
        audit_log = self.audit_logger.log_patient_data_access(
            user=self.user,
            patient=self.user,  # Using user as placeholder for patient
            action=AuditLog.ActionType.READ,
            description="Test patient data access"
        )
        
        self.assertEqual(audit_log.severity, AuditLog.Severity.HIGH)
        self.assertIn('data_type', audit_log.metadata)
    
    def test_log_security_event(self):
        """Test security event logging."""
        audit_log = self.audit_logger.log_security_event(
            user=self.user,
            action=AuditLog.ActionType.BREACH_ATTEMPT,
            description="Test security event",
            severity=AuditLog.Severity.CRITICAL
        )
        
        self.assertEqual(audit_log.severity, AuditLog.Severity.CRITICAL)
        self.assertIn('event_type', audit_log.metadata)


class ComplianceMonitorTest(TestCase):
    """Test compliance monitoring functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = RequestFactory()
        self.compliance_monitor = get_compliance_monitor()
    
    def test_monitor_data_access_compliant(self):
        """Test monitoring of compliant data access."""
        request = self.factory.get('/api/medications/')
        request.user = self.user
        
        result = self.compliance_monitor.monitor_data_access(
            user=self.user,
            action='read',
            resource='/api/medications/',
            request=request
        )
        
        # Should return True for compliant access
        self.assertTrue(result)
    
    def test_generate_compliance_report(self):
        """Test compliance report generation."""
        # Create some audit logs
        for i in range(10):
            log_audit_event(
                user=self.user,
                action=AuditLog.ActionType.READ,
                description=f"Test audit log {i}",
                severity=AuditLog.Severity.LOW
            )
        
        # Create some access denied logs
        for i in range(2):
            log_audit_event(
                user=self.user,
                action=AuditLog.ActionType.ACCESS_DENIED,
                description=f"Test access denied {i}",
                severity=AuditLog.Severity.HIGH
            )
        
        # Generate report
        start_date = timezone.now() - timedelta(days=1)
        end_date = timezone.now() + timedelta(days=1)
        
        report = self.compliance_monitor.generate_compliance_report(
            start_date, end_date
        )
        
        # Check report structure
        self.assertIn('period', report)
        self.assertIn('metrics', report)
        self.assertIn('violations', report)
        self.assertIn('recommendations', report)
        
        # Check metrics
        metrics = report['metrics']
        self.assertEqual(metrics['total_access_attempts'], 12)
        self.assertEqual(metrics['successful_access'], 10)
        self.assertEqual(metrics['denied_access'], 2)
        self.assertGreater(metrics['compliance_rate'], 80)
        
        # Check violations
        violations = report['violations']
        self.assertEqual(len(violations), 2)
        
        # Check recommendations
        recommendations = report['recommendations']
        self.assertIsInstance(recommendations, list)


class AuditMiddlewareTest(TestCase):
    """Test audit middleware functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = RequestFactory()
    
    def test_middleware_request_logging(self):
        """Test that middleware logs requests properly."""
        from security.middleware import HIPAASecurityMiddleware
        
        # Create a simple middleware
        def dummy_get_response(request):
            from django.http import HttpResponse
            return HttpResponse("OK")
        
        middleware = HIPAASecurityMiddleware(dummy_get_response)
        
        # Create a request
        request = self.factory.get('/api/medications/')
        request.user = self.user
        
        # Process request
        response = middleware(request)
        
        # Check that audit logs were created
        audit_logs = AuditLog.objects.filter(user=self.user)
        self.assertGreater(audit_logs.count(), 0)
        
        # Check that request metadata was captured
        log = audit_logs.first()
        self.assertIsNotNone(log.request_path)
        self.assertIsNotNone(log.request_method)
    
    def test_middleware_security_headers(self):
        """Test that middleware adds security headers."""
        from security.middleware import HIPAASecurityMiddleware
        
        def dummy_get_response(request):
            from django.http import HttpResponse
            return HttpResponse("OK")
        
        middleware = HIPAASecurityMiddleware(dummy_get_response)
        
        request = self.factory.get('/test/')
        response = middleware(request)
        
        # Check security headers
        self.assertIn('X-Frame-Options', response)
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-XSS-Protection', response)
        self.assertIn('Referrer-Policy', response)
        self.assertIn('Permissions-Policy', response)


class IntegrationTest(TestCase):
    """Integration tests for the complete audit system."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = RequestFactory()
    
    def test_complete_audit_workflow(self):
        """Test complete audit workflow from request to report."""
        # Simulate a series of actions
        actions = [
            (AuditLog.ActionType.LOGIN, AuditLog.Severity.LOW),
            (AuditLog.ActionType.READ, AuditLog.Severity.MEDIUM),
            (AuditLog.ActionType.UPDATE, AuditLog.Severity.MEDIUM),
            (AuditLog.ActionType.ACCESS_DENIED, AuditLog.Severity.HIGH),
            (AuditLog.ActionType.LOGOUT, AuditLog.Severity.LOW),
        ]
        
        for action, severity in actions:
            log_audit_event(
                user=self.user,
                action=action,
                description=f"Test {action} action",
                severity=severity
            )
        
        # Verify all logs were created
        self.assertEqual(AuditLog.objects.count(), 5)
        
        # Check sensitive actions
        sensitive_logs = AuditLog.objects.filter(
            action__in=[AuditLog.ActionType.READ, AuditLog.ActionType.UPDATE]
        )
        self.assertEqual(sensitive_logs.count(), 2)
        
        # Check high severity actions
        high_severity_logs = AuditLog.objects.filter(severity=AuditLog.Severity.HIGH)
        self.assertEqual(high_severity_logs.count(), 1)
        
        # Generate compliance report
        compliance_monitor = get_compliance_monitor()
        start_date = timezone.now() - timedelta(hours=1)
        end_date = timezone.now() + timedelta(hours=1)
        
        report = compliance_monitor.generate_compliance_report(start_date, end_date)
        
        # Verify report accuracy
        self.assertEqual(report['metrics']['total_access_attempts'], 5)
        self.assertEqual(report['metrics']['denied_access'], 1)
        self.assertEqual(len(report['violations']), 1) 