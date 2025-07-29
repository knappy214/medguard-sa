"""
HIPAA Compliance Security Module

This module implements comprehensive HIPAA compliance measures for the MedGuard SA system,
including encryption, access controls, audit trails, and data protection mechanisms.
"""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()
logger = logging.getLogger(__name__)


class HIPAAEncryptionManager:
    """
    Encryption manager for HIPAA-compliant data protection.
    
    This class provides encryption and decryption services for sensitive
    medical data, ensuring data confidentiality and integrity.
    """
    
    def __init__(self):
        self.key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key from environment or generate new one."""
        key = getattr(settings, 'HIPAA_ENCRYPTION_KEY', None)
        
        if key:
            # Decode base64 key
            return key.encode('utf-8')
        else:
            # Generate new key (for development only)
            new_key = Fernet.generate_key()
            logger.warning("Generated new encryption key. Set HIPAA_ENCRYPTION_KEY in production.")
            return new_key
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode('utf-8'))
            return encrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data as base64 string
            
        Returns:
            Decrypted data
        """
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode('utf-8'))
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def hash_sensitive_data(self, data: str, salt: str = None) -> str:
        """
        Hash sensitive data for storage.
        
        Args:
            data: Data to hash
            salt: Salt for hashing (optional)
            
        Returns:
            Hashed data
        """
        if not salt:
            salt = secrets.token_hex(16)
        
        hash_obj = hashlib.sha256()
        hash_obj.update(f"{salt}:{data}".encode('utf-8'))
        return f"{salt}:{hash_obj.hexdigest()}"


class HIPAAAccessControl:
    """
    HIPAA-compliant access control system.
    
    This class implements role-based access control (RBAC) with
    principle of least privilege for medical data access.
    """
    
    # HIPAA-defined roles
    class UserRole(models.TextChoices):
        PATIENT = 'patient', _('Patient')
        CAREGIVER = 'caregiver', _('Caregiver')
        HEALTHCARE_PROVIDER = 'healthcare_provider', _('Healthcare Provider')
        PHARMACIST = 'pharmacist', _('Pharmacist')
        ADMINISTRATOR = 'administrator', _('Administrator')
        RESEARCHER = 'researcher', _('Researcher')
        AUDITOR = 'auditor', _('Auditor')
    
    # Data sensitivity levels
    class SensitivityLevel(models.TextChoices):
        PUBLIC = 'public', _('Public')
        INTERNAL = 'internal', _('Internal')
        CONFIDENTIAL = 'confidential', _('Confidential')
        RESTRICTED = 'restricted', _('Restricted')
        HIGHLY_RESTRICTED = 'highly_restricted', _('Highly Restricted')
    
    def __init__(self):
        self.role_permissions = self._define_role_permissions()
    
    def _define_role_permissions(self) -> Dict[str, List[str]]:
        """Define permissions for each role."""
        return {
            self.UserRole.PATIENT: [
                'view_own_medications',
                'view_own_schedule',
                'update_own_medications',
                'view_own_profile',
            ],
            self.UserRole.CAREGIVER: [
                'view_patient_medications',
                'view_patient_schedule',
                'update_patient_medications',
                'view_patient_profile',
                'manage_patient_reminders',
            ],
            self.UserRole.HEALTHCARE_PROVIDER: [
                'view_patient_medications',
                'view_patient_schedule',
                'update_patient_medications',
                'view_patient_profile',
                'prescribe_medications',
                'view_medication_history',
                'export_patient_data',
            ],
            self.UserRole.PHARMACIST: [
                'view_medication_inventory',
                'update_medication_stock',
                'view_patient_medications',
                'dispense_medications',
                'view_medication_interactions',
            ],
            self.UserRole.ADMINISTRATOR: [
                'view_all_data',
                'manage_users',
                'manage_system_settings',
                'view_audit_logs',
                'export_system_data',
                'manage_backups',
            ],
            self.UserRole.RESEARCHER: [
                'view_anonymized_data',
                'export_research_data',
                'view_aggregate_statistics',
            ],
            self.UserRole.AUDITOR: [
                'view_audit_logs',
                'view_compliance_reports',
                'view_system_logs',
                'export_audit_data',
            ],
        }
    
    def has_permission(self, user: User, permission: str, resource: Any = None) -> bool:
        """
        Check if user has specific permission.
        
        Args:
            user: User to check
            permission: Permission to check
            resource: Resource being accessed (optional)
            
        Returns:
            True if user has permission
        """
        if not user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if user.is_superuser:
            return True
        
        # Get user's role
        user_role = getattr(user, 'user_type', self.UserRole.PATIENT)
        
        # Check role-based permissions
        role_permissions = self.role_permissions.get(user_role, [])
        if permission not in role_permissions:
            return False
        
        # Check resource-specific permissions
        if resource and hasattr(resource, 'user'):
            if permission.startswith('view_own_') or permission.startswith('update_own_'):
                return resource.user == user
        
        return True
    
    def check_data_access(self, user: User, data_type: str, data_id: Any = None) -> bool:
        """
        Check if user can access specific data.
        
        Args:
            user: User requesting access
            data_type: Type of data being accessed
            data_id: ID of specific data (optional)
            
        Returns:
            True if access is allowed
        """
        # Define data access rules
        access_rules = {
            'patient_data': {
                'roles': [self.UserRole.HEALTHCARE_PROVIDER, self.UserRole.ADMINISTRATOR],
                'permission': 'view_patient_data',
            },
            'medication_data': {
                'roles': [self.UserRole.HEALTHCARE_PROVIDER, self.UserRole.PHARMACIST, self.UserRole.ADMINISTRATOR],
                'permission': 'view_medication_data',
            },
            'audit_data': {
                'roles': [self.UserRole.AUDITOR, self.UserRole.ADMINISTRATOR],
                'permission': 'view_audit_data',
            },
        }
        
        rule = access_rules.get(data_type)
        if not rule:
            return False
        
        user_role = getattr(user, 'user_type', self.UserRole.PATIENT)
        return user_role in rule['roles'] and self.has_permission(user, rule['permission'])


class HIPAAComplianceMonitor:
    """
    HIPAA compliance monitoring and reporting system.
    
    This class monitors system activities for HIPAA compliance
    and generates compliance reports.
    """
    
    def __init__(self):
        self.encryption_manager = HIPAAEncryptionManager()
        self.access_control = HIPAAAccessControl()
    
    def monitor_data_access(self, user: User, action: str, resource: Any, request=None) -> bool:
        """
        Monitor data access for compliance.
        
        Args:
            user: User performing the action
            action: Type of action
            resource: Resource being accessed
            request: Django request object
            
        Returns:
            True if access is compliant
        """
        # Check access permissions
        if not self.access_control.has_permission(user, action, resource):
            self._log_compliance_violation(user, action, resource, request, "Access denied")
            return False
        
        # Log compliant access
        self._log_compliant_access(user, action, resource, request)
        return True
    
    def _log_compliance_violation(self, user: User, action: str, resource: Any, request, reason: str):
        """Log compliance violation."""
        from security.audit import log_audit_event, AuditLog
        
        log_audit_event(
            user=user,
            action=AuditLog.ActionType.ACCESS_DENIED,
            obj=resource,
            description=f"HIPAA compliance violation: {reason}",
            severity=AuditLog.Severity.HIGH,
            request=request,
            metadata={
                'violation_type': 'hipaa_compliance',
                'action_attempted': action,
                'reason': reason,
            }
        )
    
    def _log_compliant_access(self, user: User, action: str, resource: Any, request):
        """Log compliant data access."""
        from security.audit import log_audit_event, AuditLog
        
        log_audit_event(
            user=user,
            action=action,
            obj=resource,
            description=f"HIPAA compliant access: {action}",
            severity=AuditLog.Severity.LOW,
            request=request,
            metadata={
                'compliance_status': 'compliant',
                'hipaa_verified': True,
            }
        )
    
    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Generate HIPAA compliance report.
        
        Args:
            start_date: Start date for report
            end_date: End date for report
            
        Returns:
            Compliance report data
        """
        from security.audit import AuditLog
        
        # Get audit logs for period
        audit_logs = AuditLog.objects.filter(
            timestamp__range=(start_date, end_date)
        )
        
        # Calculate compliance metrics
        total_access = audit_logs.count()
        denied_access = audit_logs.filter(action=AuditLog.ActionType.ACCESS_DENIED).count()
        successful_access = total_access - denied_access
        
        # Calculate compliance percentage
        compliance_rate = (successful_access / total_access * 100) if total_access > 0 else 100
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'metrics': {
                'total_access_attempts': total_access,
                'successful_access': successful_access,
                'denied_access': denied_access,
                'compliance_rate': round(compliance_rate, 2),
            },
            'violations': self._get_compliance_violations(audit_logs),
            'recommendations': self._generate_recommendations(compliance_rate),
        }
    
    def _get_compliance_violations(self, audit_logs) -> List[Dict[str, Any]]:
        """Get compliance violations from audit logs."""
        violations = []
        
        for log in audit_logs.filter(severity__in=[AuditLog.Severity.HIGH, AuditLog.Severity.CRITICAL]):
            violations.append({
                'timestamp': log.timestamp.isoformat(),
                'user': log.user.username if log.user else 'Unknown',
                'action': log.action,
                'description': log.description,
                'severity': log.severity,
                'ip_address': log.ip_address,
            })
        
        return violations
    
    def _generate_recommendations(self, compliance_rate: float) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []
        
        if compliance_rate < 95:
            recommendations.append("Review access control policies")
            recommendations.append("Implement additional security training")
        
        if compliance_rate < 90:
            recommendations.append("Conduct security audit")
            recommendations.append("Update user permissions")
        
        return recommendations


class HIPAADataRetention:
    """
    HIPAA data retention and disposal system.
    
    This class manages data retention policies and secure data disposal
    in accordance with HIPAA requirements.
    """
    
    # Retention periods (in days)
    RETENTION_PERIODS = {
        'patient_records': 2555,  # 7 years
        'medication_records': 2555,  # 7 years
        'audit_logs': 2555,  # 7 years
        'access_logs': 1825,  # 5 years
        'backup_data': 2555,  # 7 years
    }
    
    def __init__(self):
        self.encryption_manager = HIPAAEncryptionManager()
    
    def check_retention_policy(self, data_type: str, created_date: datetime) -> bool:
        """
        Check if data should be retained based on policy.
        
        Args:
            data_type: Type of data
            created_date: When data was created
            
        Returns:
            True if data should be retained
        """
        retention_days = self.RETENTION_PERIODS.get(data_type, 2555)
        retention_date = created_date + timedelta(days=retention_days)
        
        return timezone.now() < retention_date
    
    def secure_data_disposal(self, data_type: str, data_ids: List[int]) -> bool:
        """
        Securely dispose of data.
        
        Args:
            data_type: Type of data to dispose
            data_ids: IDs of data to dispose
            
        Returns:
            True if disposal was successful
        """
        try:
            # Log disposal action
            from security.audit import log_audit_event, AuditLog
            
            log_audit_event(
                user=None,
                action=AuditLog.ActionType.DELETE,
                description=f"Secure disposal of {len(data_ids)} {data_type} records",
                severity=AuditLog.Severity.MEDIUM,
                metadata={
                    'disposal_type': 'hipaa_retention',
                    'data_type': data_type,
                    'record_count': len(data_ids),
                }
            )
            
            # Implement secure disposal logic here
            # This would typically involve:
            # 1. Overwriting data with random values
            # 2. Physical destruction of storage media
            # 3. Verification of disposal
            
            return True
            
        except Exception as e:
            logger.error(f"Secure disposal failed: {str(e)}")
            return False
    
    def schedule_data_disposal(self, data_type: str, disposal_date: datetime):
        """
        Schedule data for disposal.
        
        Args:
            data_type: Type of data to dispose
            disposal_date: When to dispose the data
        """
        # This would be implemented with Celery tasks
        # For now, we'll just log the schedule
        logger.info(f"Scheduled disposal of {data_type} data for {disposal_date}")


class HIPAABreachDetection:
    """
    HIPAA breach detection and response system.
    
    This class monitors for potential HIPAA breaches and
    implements automated response mechanisms.
    """
    
    def __init__(self):
        self.breach_thresholds = {
            'failed_login_attempts': 5,
            'unusual_access_patterns': 10,
            'data_export_volume': 1000,
            'concurrent_sessions': 3,
        }
    
    def detect_breach_indicators(self, user: User, action: str, context: Dict[str, Any]) -> List[str]:
        """
        Detect potential breach indicators.
        
        Args:
            user: User performing the action
            action: Action being performed
            context: Additional context
            
        Returns:
            List of detected breach indicators
        """
        indicators = []
        
        # Check failed login attempts
        if action == 'login_failed':
            failed_attempts = self._get_failed_login_attempts(user)
            if failed_attempts >= self.breach_thresholds['failed_login_attempts']:
                indicators.append('excessive_failed_logins')
        
        # Check unusual access patterns
        if action == 'data_access':
            unusual_patterns = self._detect_unusual_patterns(user, context)
            if unusual_patterns:
                indicators.append('unusual_access_patterns')
        
        # Check data export volume
        if action == 'data_export':
            export_volume = context.get('record_count', 0)
            if export_volume > self.breach_thresholds['data_export_volume']:
                indicators.append('large_data_export')
        
        # Check concurrent sessions
        if action == 'login_successful':
            concurrent_sessions = self._get_concurrent_sessions(user)
            if concurrent_sessions > self.breach_thresholds['concurrent_sessions']:
                indicators.append('excessive_concurrent_sessions')
        
        return indicators
    
    def _get_failed_login_attempts(self, user: User) -> int:
        """Get number of failed login attempts for user."""
        from security.audit import AuditLog
        
        recent_failures = AuditLog.objects.filter(
            user=user,
            action=AuditLog.ActionType.ACCESS_DENIED,
            timestamp__gte=timezone.now() - timedelta(minutes=15)
        ).count()
        
        return recent_failures
    
    def _detect_unusual_patterns(self, user: User, context: Dict[str, Any]) -> bool:
        """Detect unusual access patterns."""
        # Implement pattern detection logic
        # This would analyze user behavior patterns
        return False
    
    def _get_concurrent_sessions(self, user: User) -> int:
        """Get number of concurrent sessions for user."""
        # This would check active sessions
        return 1
    
    def respond_to_breach(self, user: User, indicators: List[str], context: Dict[str, Any]):
        """
        Respond to detected breach indicators.
        
        Args:
            user: User involved in breach
            indicators: Detected breach indicators
            context: Breach context
        """
        from security.audit import log_audit_event, AuditLog
        
        # Log breach detection
        log_audit_event(
            user=user,
            action=AuditLog.ActionType.BREACH_ATTEMPT,
            description=f"HIPAA breach indicators detected: {', '.join(indicators)}",
            severity=AuditLog.Severity.CRITICAL,
            metadata={
                'breach_indicators': indicators,
                'context': context,
            }
        )
        
        # Implement automated responses
        if 'excessive_failed_logins' in indicators:
            self._lock_user_account(user)
        
        if 'large_data_export' in indicators:
            self._flag_for_review(user, 'large_data_export')
        
        if 'unusual_access_patterns' in indicators:
            self._flag_for_review(user, 'unusual_patterns')
    
    def _lock_user_account(self, user: User):
        """Lock user account temporarily."""
        user.is_active = False
        user.save()
        
        # Schedule account unlock
        # This would be implemented with Celery tasks
        
        logger.warning(f"User account locked: {user.username}")
    
    def _flag_for_review(self, user: User, reason: str):
        """Flag user account for manual review."""
        # This would create a review task
        logger.warning(f"User flagged for review: {user.username} - {reason}")


# Global instances
_encryption_manager = None
_access_control = None
_compliance_monitor = None
_data_retention = None
_breach_detection = None


def get_encryption_manager() -> HIPAAEncryptionManager:
    """Get global encryption manager instance."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = HIPAAEncryptionManager()
    return _encryption_manager


def get_access_control() -> HIPAAAccessControl:
    """Get global access control instance."""
    global _access_control
    if _access_control is None:
        _access_control = HIPAAAccessControl()
    return _access_control


def get_compliance_monitor() -> HIPAAComplianceMonitor:
    """Get global compliance monitor instance."""
    global _compliance_monitor
    if _compliance_monitor is None:
        _compliance_monitor = HIPAAComplianceMonitor()
    return _compliance_monitor


def get_data_retention() -> HIPAADataRetention:
    """Get global data retention instance."""
    global _data_retention
    if _data_retention is None:
        _data_retention = HIPAADataRetention()
    return _data_retention


def get_breach_detection() -> HIPAABreachDetection:
    """Get global breach detection instance."""
    global _breach_detection
    if _breach_detection is None:
        _breach_detection = HIPAABreachDetection()
    return _breach_detection


# Convenience functions
def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data."""
    manager = get_encryption_manager()
    return manager.encrypt_data(data)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data."""
    manager = get_encryption_manager()
    return manager.decrypt_data(encrypted_data)


def check_hipaa_access(user: User, permission: str, resource: Any = None) -> bool:
    """Check HIPAA-compliant access."""
    control = get_access_control()
    return control.has_permission(user, permission, resource)


def monitor_hipaa_compliance(user: User, action: str, resource: Any, request=None) -> bool:
    """Monitor HIPAA compliance."""
    monitor = get_compliance_monitor()
    return monitor.monitor_data_access(user, action, resource, request)


def detect_breach_indicators(user: User, action: str, context: Dict[str, Any]) -> List[str]:
    """Detect breach indicators."""
    detection = get_breach_detection()
    return detection.detect_breach_indicators(user, action, context) 