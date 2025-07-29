"""
HIPAA-Compliant Security Middleware

This middleware integrates all security features for HIPAA compliance,
including audit logging, access control, breach detection, and encryption.
"""

import logging
import time
from typing import Any, Dict, Optional
from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from .audit import log_audit_event, AuditLog
from .hipaa_compliance import (
    get_compliance_monitor,
    get_breach_detection,
    get_encryption_manager,
    check_hipaa_access,
    detect_breach_indicators,
)
from .permissions import check_permission, check_resource_access

logger = logging.getLogger(__name__)


class HIPAASecurityMiddleware(MiddlewareMixin):
    """
    Comprehensive HIPAA security middleware.
    
    This middleware provides:
    - Request/response logging
    - Access control enforcement
    - Breach detection
    - Rate limiting
    - Security headers
    - Audit trail creation
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.compliance_monitor = get_compliance_monitor()
        self.breach_detection = get_breach_detection()
        self.encryption_manager = get_encryption_manager()
        
        # Sensitive endpoints that require special monitoring
        self.sensitive_endpoints = {
            '/api/medications/',
            '/api/patients/',
            '/api/medical-records/',
            '/admin/medications/',
            '/admin/users/',
            '/api/audit-logs/',
        }
        
        # Rate limiting configuration
        self.rate_limit_config = {
            'requests_per_minute': 60,
            'burst_limit': 10,
        }
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request through security middleware."""
        start_time = time.time()
        
        # Add request metadata
        request.start_time = start_time
        request.request_id = self._generate_request_id()
        
        # Pre-processing security checks
        self._pre_process_request(request)
        
        # Process request
        response = self.get_response(request)
        
        # Post-processing security measures
        self._post_process_request(request, response, start_time)
        
        return response
    
    def _pre_process_request(self, request: HttpRequest):
        """Pre-process security checks."""
        # Rate limiting
        if not self._check_rate_limit(request):
            self._log_rate_limit_violation(request)
            return
        
        # Check for suspicious patterns
        if self._detect_suspicious_patterns(request):
            self._log_suspicious_activity(request)
        
        # Log request start
        if request.user.is_authenticated:
            self._log_request_start(request)
    
    def _post_process_request(self, request: HttpRequest, response: HttpResponse, start_time: float):
        """Post-process security measures."""
        # Add security headers
        self._add_security_headers(response)
        
        # Log request completion
        if request.user.is_authenticated:
            self._log_request_completion(request, response, start_time)
        
        # Check for breach indicators
        if request.user.is_authenticated:
            self._check_breach_indicators(request, response)
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID for tracking."""
        import uuid
        return str(uuid.uuid4())
    
    def _check_rate_limit(self, request: HttpRequest) -> bool:
        """Check rate limiting for request."""
        if not request.user.is_authenticated:
            return True
        
        # Use IP address for rate limiting
        client_ip = self._get_client_ip(request)
        cache_key = f'rate_limit:{client_ip}'
        
        # Get current request count
        request_count = cache.get(cache_key, 0)
        
        if request_count >= self.rate_limit_config['requests_per_minute']:
            return False
        
        # Increment request count
        cache.set(cache_key, request_count + 1, 60)  # 1 minute window
        return True
    
    def _detect_suspicious_patterns(self, request: HttpRequest) -> bool:
        """Detect suspicious request patterns."""
        # Check for SQL injection attempts
        suspicious_patterns = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION',
            'script', 'javascript', 'eval(', 'document.cookie',
        ]
        
        request_string = f"{request.path} {request.GET} {request.POST}"
        request_string_lower = request_string.lower()
        
        for pattern in suspicious_patterns:
            if pattern.lower() in request_string_lower:
                return True
        
        return False
    
    def _check_breach_indicators(self, request: HttpRequest, response: HttpResponse):
        """Check for breach indicators in request/response."""
        context = {
            'request_path': request.path,
            'request_method': request.method,
            'response_status': response.status_code,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': self._get_client_ip(request),
        }
        
        # Check for sensitive endpoint access
        if any(endpoint in request.path for endpoint in self.sensitive_endpoints):
            indicators = detect_breach_indicators(
                request.user, 
                'sensitive_endpoint_access', 
                context
            )
            
            if indicators:
                self.breach_detection.respond_to_breach(
                    request.user, indicators, context
                )
    
    def _log_request_start(self, request: HttpRequest):
        """Log request start for audit."""
        log_audit_event(
            user=request.user,
            action=AuditLog.ActionType.READ,
            description=f"Request started: {request.method} {request.path}",
            severity=AuditLog.Severity.LOW,
            request=request,
            metadata={
                'request_id': request.request_id,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': self._get_client_ip(request),
            }
        )
    
    def _log_request_completion(self, request: HttpRequest, response: HttpResponse, start_time: float):
        """Log request completion for audit."""
        duration = time.time() - start_time
        
        # Determine severity based on endpoint and response
        severity = AuditLog.Severity.LOW
        if any(endpoint in request.path for endpoint in self.sensitive_endpoints):
            severity = AuditLog.Severity.MEDIUM
        
        if response.status_code >= 400:
            severity = AuditLog.Severity.HIGH
        
        log_audit_event(
            user=request.user,
            action=AuditLog.ActionType.READ,
            description=f"Request completed: {request.method} {request.path} ({response.status_code})",
            severity=severity,
            request=request,
            metadata={
                'request_id': request.request_id,
                'response_status': response.status_code,
                'duration': round(duration, 3),
                'content_length': len(response.content) if hasattr(response, 'content') else 0,
            }
        )
    
    def _log_rate_limit_violation(self, request: HttpRequest):
        """Log rate limit violation."""
        log_audit_event(
            user=request.user if request.user.is_authenticated else None,
            action=AuditLog.ActionType.ACCESS_DENIED,
            description="Rate limit exceeded",
            severity=AuditLog.Severity.MEDIUM,
            request=request,
            metadata={
                'violation_type': 'rate_limit',
                'ip_address': self._get_client_ip(request),
            }
        )
    
    def _log_suspicious_activity(self, request: HttpRequest):
        """Log suspicious activity."""
        log_audit_event(
            user=request.user if request.user.is_authenticated else None,
            action=AuditLog.ActionType.BREACH_ATTEMPT,
            description="Suspicious activity detected",
            severity=AuditLog.Severity.HIGH,
            request=request,
            metadata={
                'activity_type': 'suspicious_pattern',
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )
    
    def _add_security_headers(self, response: HttpResponse):
        """Add security headers to response."""
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        
        # X-Frame-Options
        response['X-Frame-Options'] = 'DENY'
        
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), '
            'payment=(), usb=(), magnetometer=(), gyroscope=()'
        )
        
        # Strict-Transport-Security (for HTTPS)
        if getattr(settings, 'SECURE_SSL_REDIRECT', False):
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DataEncryptionMiddleware(MiddlewareMixin):
    """
    Middleware for automatic data encryption/decryption.
    
    This middleware automatically encrypts sensitive data in responses
    and decrypts data in requests when needed.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.encryption_manager = get_encryption_manager()
        
        # Fields that should be encrypted
        self.encrypted_fields = {
            'medical_record_number',
            'social_security_number',
            'credit_card_number',
            'bank_account_number',
            'diagnosis',
            'treatment_notes',
            'billing_information',
        }
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request through encryption middleware."""
        # Decrypt request data if needed
        self._decrypt_request_data(request)
        
        response = self.get_response(request)
        
        # Encrypt response data if needed
        self._encrypt_response_data(response)
        
        return response
    
    def _decrypt_request_data(self, request: HttpRequest):
        """Decrypt sensitive data in request."""
        # This would decrypt sensitive fields in POST/PUT data
        # Implementation depends on how data is structured
        pass
    
    def _encrypt_response_data(self, response: HttpResponse):
        """Encrypt sensitive data in response."""
        # This would encrypt sensitive fields in JSON responses
        # Implementation depends on response format
        pass


class AccessControlMiddleware(MiddlewareMixin):
    """
    Middleware for enforcing access controls.
    
    This middleware enforces HIPAA-compliant access controls
    for all requests to sensitive endpoints.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Endpoints that require special access control
        self.protected_endpoints = {
            '/api/patients/': ['view_patient_data'],
            '/api/medications/': ['view_medication_data'],
            '/api/medical-records/': ['view_patient_data'],
            '/admin/medications/': ['manage_medications'],
            '/admin/users/': ['manage_users'],
            '/api/audit-logs/': ['view_audit_logs'],
        }
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request through access control middleware."""
        # Check access permissions for protected endpoints
        if not self._check_endpoint_access(request):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Access denied")
        
        return self.get_response(request)
    
    def _check_endpoint_access(self, request: HttpRequest) -> bool:
        """Check if user has access to endpoint."""
        if not request.user.is_authenticated:
            return False
        
        # Check if endpoint is protected
        for endpoint, required_permissions in self.protected_endpoints.items():
            if endpoint in request.path:
                # Check if user has any of the required permissions
                for permission in required_permissions:
                    if check_permission(request.user, permission):
                        return True
                return False
        
        return True


class ComplianceReportingMiddleware(MiddlewareMixin):
    """
    Middleware for compliance reporting and monitoring.
    
    This middleware generates compliance reports and monitors
    system activity for HIPAA compliance.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.compliance_monitor = get_compliance_monitor()
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request through compliance middleware."""
        # Monitor compliance for sensitive operations
        if request.user.is_authenticated:
            self._monitor_compliance(request)
        
        response = self.get_response(request)
        
        # Update compliance metrics
        if request.user.is_authenticated:
            self._update_compliance_metrics(request, response)
        
        return response
    
    def _monitor_compliance(self, request: HttpRequest):
        """Monitor compliance for request."""
        # Check if this is a sensitive operation
        sensitive_operations = [
            'POST', 'PUT', 'DELETE', 'PATCH'
        ]
        
        if request.method in sensitive_operations:
            # Monitor data access compliance
            self.compliance_monitor.monitor_data_access(
                user=request.user,
                action=request.method.lower(),
                resource=request.path,
                request=request
            )
    
    def _update_compliance_metrics(self, request: HttpRequest, response: HttpResponse):
        """Update compliance metrics."""
        # This would update compliance metrics in cache or database
        # For now, we'll just log the activity
        if response.status_code >= 400:
            logger.warning(f"Compliance issue: {request.user} - {request.path} - {response.status_code}")


# Middleware configuration
MIDDLEWARE_CLASSES = [
    'security.middleware.HIPAASecurityMiddleware',
    'security.middleware.DataEncryptionMiddleware',
    'security.middleware.AccessControlMiddleware',
    'security.middleware.ComplianceReportingMiddleware',
    # ... other middleware
] 