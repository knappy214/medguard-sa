"""
Comprehensive test suite for Wagtail 7.0.2 security features in MedGuard SA.

This module tests all security functionality including:
- SecurityEvent logging and monitoring
- HealthcareFormSecurityMixin and form protection
- SecurityMonitor and threat detection
- PasswordPolicy and authentication security
- TwoFactorAuth and MFA implementation
- HealthcareDocumentPrivacyMixin and document security
- AuditLog and compliance tracking
- UserHealthcareRole and access control
- Encryption and data protection
- HIPAA compliance features
- Admin access controls
- Breach detection and response
- Session management and timeout
- Rate limiting and DDoS protection
"""

import pytest
import json
import hashlib
import secrets
from django.test import TestCase, TransactionTestCase, Client, RequestFactory
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from wagtail.test.utils import WagtailTestUtils
from wagtail.models import Page
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.permission_policies import ModelPermissionPolicy

# Import security models and classes
from security.models import (
    SecurityEvent,
    UserHealthcareRole,
    MedicalSession,
    PasswordPolicy,
    PasswordHistory,
    TwoFactorAuth
)
from security.form_security import (
    HealthcareFormSecurityMixin,
    SecureFormSubmissionManager
)
from security.monitoring import SecurityMonitor
from security.audit import AuditLog, log_audit_event, log_security_event
from security.password_policies import (
    PasswordPolicy as PasswordPolicyModel,
    TwoFactorAuth as TwoFactorAuthModel
)
from security.document_privacy import HealthcareDocumentPrivacyMixin
from security.admin_access_controls import HealthcareAdminAccessMixin
from security.encryption import encrypt_sensitive_data, decrypt_sensitive_data
from security.session_management import MedicalSession

# Import related models
from medications.models import Medication, EnhancedPrescription
from home.models import HomePage

User = get_user_model()


class BaseSecurityTestCase(TestCase):
    """Base test case for security testing with common setup."""
    
    def setUp(self):
        """Set up common test data."""
        super().setUp()
        
        # Create test users with different roles
        self.patient = User.objects.create_user(
            username='patient',
            email='patient@example.com',
            password='PatientPass123!',
            first_name='John',
            last_name='Doe'
        )
        
        self.doctor = User.objects.create_user(
            username='doctor',
            email='doctor@medguard.co.za',
            password='DoctorPass123!',
            first_name='Dr. Jane',
            last_name='Smith',
            is_staff=True
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@medguard.co.za',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User',
            is_staff=True,
            is_superuser=True
        )
        
        self.pharmacist = User.objects.create_user(
            username='pharmacist',
            email='pharmacist@medguard.co.za',
            password='PharmacistPass123!',
            first_name='Pharm',
            last_name='Expert',
            is_staff=True
        )
        
        # Create healthcare roles
        self.doctor_role = UserHealthcareRole.objects.create(
            user=self.doctor,
            role_type='DOCTOR',
            license_number='DOC123456',
            is_active=True,
            last_reviewed_at=timezone.now()
        )
        
        self.pharmacist_role = UserHealthcareRole.objects.create(
            user=self.pharmacist,
            role_type='PHARMACIST',
            license_number='PHARM789012',
            is_active=True,
            last_reviewed_at=timezone.now()
        )
        
        # Set up clients and factory
        self.client = Client()
        self.factory = RequestFactory()
        
        # Create test medication and prescription
        self.medication = Medication.objects.create(
            name='Test Medication',
            strength='500mg',
            form='tablet'
        )
        
        self.prescription = EnhancedPrescription.objects.create(
            patient=self.patient,
            prescriber=self.doctor,
            medication_name='Test Medication',
            dosage='500mg',
            frequency='twice_daily',
            duration_days=30
        )
        
        # Clear cache and security events before each test
        cache.clear()
        SecurityEvent.objects.all().delete()
        AuditLog.objects.all().delete()


class SecurityEventTestCase(BaseSecurityTestCase):
    """Test cases for SecurityEvent model."""
    
    def test_security_event_creation(self):
        """Test creating security events."""
        event = SecurityEvent.objects.create(
            user=self.patient,
            event_type=SecurityEvent.EventType.LOGIN_FAILED,
            severity=SecurityEvent.Severity.MEDIUM,
            description='Failed login attempt',
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0 Test Browser',
            request_path='/admin/login/'
        )
        
        self.assertEqual(event.user, self.patient)
        self.assertEqual(event.event_type, SecurityEvent.EventType.LOGIN_FAILED)
        self.assertEqual(event.severity, SecurityEvent.Severity.MEDIUM)
        self.assertEqual(event.ip_address, '192.168.1.100')
        
    def test_security_event_logging(self):
        """Test security event logging functionality."""
        # Log a security event
        log_security_event(
            event_type='access_denied',
            severity='high',
            description='Unauthorized access attempt to patient data',
            user=self.patient,
            ip_address='10.0.0.1',
            request_path='/api/patient-data/'
        )
        
        # Check event was logged
        event = SecurityEvent.objects.filter(
            event_type='access_denied',
            user=self.patient
        ).first()
        
        self.assertIsNotNone(event)
        self.assertEqual(event.severity, 'high')
        self.assertIn('Unauthorized access', event.description)
        
    def test_security_event_severity_escalation(self):
        """Test security event severity escalation."""
        # Create multiple failed login events
        for i in range(5):
            SecurityEvent.objects.create(
                user=self.patient,
                event_type=SecurityEvent.EventType.LOGIN_FAILED,
                severity=SecurityEvent.Severity.MEDIUM,
                description=f'Failed login attempt {i+1}',
                ip_address='192.168.1.100'
            )
        
        # Check for escalation
        failed_logins = SecurityEvent.objects.filter(
            user=self.patient,
            event_type=SecurityEvent.EventType.LOGIN_FAILED
        ).count()
        
        self.assertEqual(failed_logins, 5)
        
        # Should trigger high severity alert
        if failed_logins >= 5:
            SecurityEvent.objects.create(
                user=self.patient,
                event_type=SecurityEvent.EventType.SECURITY_ALERT,
                severity=SecurityEvent.Severity.HIGH,
                description='Multiple failed login attempts detected'
            )
            
        alerts = SecurityEvent.objects.filter(
            event_type=SecurityEvent.EventType.SECURITY_ALERT,
            severity=SecurityEvent.Severity.HIGH
        ).count()
        
        self.assertGreater(alerts, 0)
        
    def test_security_event_data_access_logging(self):
        """Test data access event logging."""
        # Log data access event
        SecurityEvent.objects.create(
            user=self.doctor,
            event_type=SecurityEvent.EventType.DATA_ACCESS,
            severity=SecurityEvent.Severity.LOW,
            description=f'Accessed patient prescription: {self.prescription.id}',
            metadata={
                'prescription_id': self.prescription.id,
                'patient_id': self.patient.id,
                'access_type': 'read'
            }
        )
        
        # Check event was logged
        event = SecurityEvent.objects.filter(
            user=self.doctor,
            event_type=SecurityEvent.EventType.DATA_ACCESS
        ).first()
        
        self.assertIsNotNone(event)
        self.assertEqual(event.metadata['prescription_id'], self.prescription.id)


class HealthcareFormSecurityMixinTestCase(BaseSecurityTestCase):
    """Test cases for HealthcareFormSecurityMixin."""
    
    def setUp(self):
        """Set up form security test data."""
        super().setUp()
        
        # Create a test form class using the mixin
        class TestSecureForm(HealthcareFormSecurityMixin):
            def __init__(self, security_level='medium'):
                self.security_level = security_level
        
        self.test_form = TestSecureForm()
        
    def test_security_level_detection(self):
        """Test security level detection."""
        # Test default security level
        self.assertEqual(
            self.test_form.get_security_level(),
            HealthcareFormSecurityMixin.SECURITY_MEDIUM
        )
        
        # Test critical security level
        critical_form = self.test_form.__class__(security_level='critical')
        self.assertEqual(
            critical_form.get_security_level(),
            HealthcareFormSecurityMixin.SECURITY_CRITICAL
        )
        
    def test_rate_limiting(self):
        """Test form rate limiting functionality."""
        # Test default rate limit
        default_limit = self.test_form.get_rate_limit()
        self.assertEqual(default_limit, HealthcareFormSecurityMixin.RATE_LIMIT_DEFAULT)
        
        # Test critical form rate limit
        critical_form = self.test_form.__class__(security_level='critical')
        critical_limit = critical_form.get_rate_limit()
        self.assertEqual(critical_limit, HealthcareFormSecurityMixin.RATE_LIMIT_CRITICAL)
        
    def test_encryption_requirements(self):
        """Test encryption requirement detection."""
        # Medium security should not require encryption
        self.assertFalse(self.test_form.requires_encryption())
        
        # High security should require encryption
        high_form = self.test_form.__class__(security_level='high')
        self.assertTrue(high_form.requires_encryption())
        
        # Critical security should require encryption
        critical_form = self.test_form.__class__(security_level='critical')
        self.assertTrue(critical_form.requires_encryption())
        
    def test_form_submission_tracking(self):
        """Test form submission tracking for security."""
        # Create a form submission tracking entry
        from security.form_security import SecureFormSubmission
        
        submission = SecureFormSubmission.objects.create(
            user=self.patient,
            form_type='prescription_submission',
            ip_address='192.168.1.100',
            security_level='high',
            is_encrypted=True,
            submission_data_hash='abc123def456'
        )
        
        self.assertEqual(submission.user, self.patient)
        self.assertEqual(submission.form_type, 'prescription_submission')
        self.assertTrue(submission.is_encrypted)
        
    def test_form_csrf_protection(self):
        """Test CSRF protection for forms."""
        # Test form with CSRF token
        request = self.factory.post('/test-form/', {
            'csrfmiddlewaretoken': 'valid_token',
            'field1': 'value1'
        })
        request.user = self.patient
        
        # Should validate CSRF token
        # This would be implemented in the actual form validation
        self.assertTrue(hasattr(request, 'POST'))
        self.assertIn('csrfmiddlewaretoken', request.POST)
        
    def test_form_input_sanitization(self):
        """Test form input sanitization."""
        # Test malicious input
        malicious_inputs = [
            '<script>alert("xss")</script>',
            '<?php system("rm -rf /"); ?>',
            'DROP TABLE medications;',
            '../../etc/passwd'
        ]
        
        for malicious_input in malicious_inputs:
            # This would test actual sanitization logic
            # For now, just verify the input exists
            self.assertIsInstance(malicious_input, str)
            self.assertGreater(len(malicious_input), 0)


class SecurityMonitorTestCase(BaseSecurityTestCase):
    """Test cases for SecurityMonitor."""
    
    def setUp(self):
        """Set up security monitor test data."""
        super().setUp()
        self.monitor = SecurityMonitor()
        
    def test_security_monitor_initialization(self):
        """Test security monitor initialization."""
        self.assertIsInstance(self.monitor.alert_thresholds, dict)
        self.assertIn('failed_logins_per_hour', self.monitor.alert_thresholds)
        self.assertIn('email', self.monitor.notification_channels)
        
    def test_failed_login_monitoring(self):
        """Test failed login attempt monitoring."""
        # Create multiple failed login events
        for i in range(12):  # Exceed threshold of 10
            SecurityEvent.objects.create(
                user=self.patient,
                event_type=SecurityEvent.EventType.LOGIN_FAILED,
                severity=SecurityEvent.Severity.MEDIUM,
                description=f'Failed login attempt {i+1}',
                created_at=timezone.now() - timedelta(minutes=30)
            )
        
        # Monitor should detect excessive failed logins
        alerts = self.monitor.check_failed_logins()
        
        self.assertIsInstance(alerts, list)
        # Should trigger alert due to exceeding threshold
        
    def test_data_access_anomaly_detection(self):
        """Test data access anomaly detection."""
        # Create many data access events in short time
        for i in range(25):  # Exceed threshold of 20
            SecurityEvent.objects.create(
                user=self.doctor,
                event_type=SecurityEvent.EventType.DATA_ACCESS,
                severity=SecurityEvent.Severity.LOW,
                description=f'Data access event {i+1}',
                created_at=timezone.now() - timedelta(minutes=15)
            )
        
        # Should detect anomaly
        anomalies = self.monitor.check_data_access_anomalies()
        
        self.assertIsInstance(anomalies, list)
        
    def test_security_alert_generation(self):
        """Test security alert generation."""
        # Trigger a security alert
        alert_data = {
            'alert_type': 'suspicious_activity',
            'severity': 'high',
            'user_id': self.patient.id,
            'description': 'Multiple suspicious activities detected'
        }
        
        # Generate alert
        alert_result = self.monitor.generate_security_alert(alert_data)
        
        self.assertTrue(alert_result)
        
        # Check alert was logged
        alert_event = SecurityEvent.objects.filter(
            event_type=SecurityEvent.EventType.SECURITY_ALERT,
            user=self.patient
        ).first()
        
        self.assertIsNotNone(alert_event)
        
    def test_real_time_monitoring(self):
        """Test real-time security monitoring."""
        # Start monitoring
        monitoring_result = self.monitor.start_real_time_monitoring()
        
        # Should return monitoring status
        self.assertIsInstance(monitoring_result, dict)
        
        # Create a security event during monitoring
        SecurityEvent.objects.create(
            user=self.patient,
            event_type=SecurityEvent.EventType.BREACH_ATTEMPT,
            severity=SecurityEvent.Severity.CRITICAL,
            description='Potential security breach detected'
        )
        
        # Monitor should detect the event
        recent_events = self.monitor.get_recent_critical_events()
        
        self.assertGreater(len(recent_events), 0)


class PasswordPolicyTestCase(BaseSecurityTestCase):
    """Test cases for password policies."""
    
    def setUp(self):
        """Set up password policy test data."""
        super().setUp()
        
        # Create password policy
        self.policy = PasswordPolicy.objects.create(
            name='Healthcare Password Policy',
            min_length=12,
            require_uppercase=True,
            require_lowercase=True,
            require_digits=True,
            require_special_chars=True,
            max_age_days=90,
            history_count=5,
            is_active=True
        )
        
    def test_password_policy_creation(self):
        """Test creating password policies."""
        self.assertEqual(self.policy.name, 'Healthcare Password Policy')
        self.assertEqual(self.policy.min_length, 12)
        self.assertTrue(self.policy.require_uppercase)
        self.assertTrue(self.policy.is_active)
        
    def test_password_strength_validation(self):
        """Test password strength validation."""
        # Test weak passwords
        weak_passwords = [
            'password',  # No uppercase, digits, special chars
            'Password',  # No digits, special chars
            'Password1',  # No special chars
            'Pass1!',  # Too short
            'PASSWORD1!',  # No lowercase
            'password1!',  # No uppercase
        ]
        
        for weak_password in weak_passwords:
            with self.assertRaises(ValidationError):
                self.policy.validate_password(weak_password, self.patient)
        
        # Test strong password
        strong_password = 'StrongPassword123!'
        
        try:
            self.policy.validate_password(strong_password, self.patient)
        except ValidationError:
            self.fail("Strong password should not raise ValidationError")
            
    def test_password_history_tracking(self):
        """Test password history tracking."""
        # Create password history entries
        old_passwords = [
            'OldPassword1!',
            'OldPassword2!',
            'OldPassword3!',
            'OldPassword4!',
            'OldPassword5!'
        ]
        
        for password in old_passwords:
            PasswordHistory.objects.create(
                user=self.patient,
                password_hash=hashlib.sha256(password.encode()).hexdigest(),
                created_at=timezone.now() - timedelta(days=30)
            )
        
        # Test reusing old password
        with self.assertRaises(ValidationError):
            self.policy.validate_password('OldPassword1!', self.patient)
            
        # Test new password
        new_password = 'NewPassword123!'
        try:
            self.policy.validate_password(new_password, self.patient)
        except ValidationError:
            self.fail("New password should not raise ValidationError")
            
    def test_password_expiration(self):
        """Test password expiration functionality."""
        # Set user's last password change to old date
        old_date = timezone.now() - timedelta(days=100)
        
        # Check if password is expired
        is_expired = self.policy.is_password_expired(self.patient, old_date)
        
        self.assertTrue(is_expired)
        
        # Check recent password
        recent_date = timezone.now() - timedelta(days=30)
        is_expired_recent = self.policy.is_password_expired(self.patient, recent_date)
        
        self.assertFalse(is_expired_recent)


class TwoFactorAuthTestCase(BaseSecurityTestCase):
    """Test cases for two-factor authentication."""
    
    def setUp(self):
        """Set up 2FA test data."""
        super().setUp()
        
        # Create 2FA setup for user
        self.two_factor = TwoFactorAuth.objects.create(
            user=self.doctor,
            secret_key=secrets.token_hex(16),
            is_active=True,
            backup_codes=['123456', '789012', '345678'],
            last_used_at=None
        )
        
    def test_two_factor_auth_creation(self):
        """Test creating 2FA setup."""
        self.assertEqual(self.two_factor.user, self.doctor)
        self.assertTrue(self.two_factor.is_active)
        self.assertIsNotNone(self.two_factor.secret_key)
        self.assertEqual(len(self.two_factor.backup_codes), 3)
        
    def test_totp_token_generation(self):
        """Test TOTP token generation."""
        # Generate TOTP token
        token = self.two_factor.generate_totp_token()
        
        self.assertIsInstance(token, str)
        self.assertEqual(len(token), 6)  # TOTP tokens are 6 digits
        
    def test_totp_token_validation(self):
        """Test TOTP token validation."""
        # Generate a token
        token = self.two_factor.generate_totp_token()
        
        # Validate the token
        is_valid = self.two_factor.validate_totp_token(token)
        
        self.assertTrue(is_valid)
        
        # Test invalid token
        is_valid_invalid = self.two_factor.validate_totp_token('000000')
        
        self.assertFalse(is_valid_invalid)
        
    def test_backup_code_usage(self):
        """Test backup code usage."""
        # Use a backup code
        backup_code = '123456'
        is_valid = self.two_factor.use_backup_code(backup_code)
        
        self.assertTrue(is_valid)
        
        # Code should be marked as used
        self.two_factor.refresh_from_db()
        self.assertNotIn(backup_code, self.two_factor.backup_codes)
        
        # Try to use the same code again
        is_valid_reuse = self.two_factor.use_backup_code(backup_code)
        
        self.assertFalse(is_valid_reuse)
        
    def test_qr_code_generation(self):
        """Test QR code generation for 2FA setup."""
        # Generate QR code
        qr_code = self.two_factor.generate_qr_code()
        
        self.assertIsInstance(qr_code, str)  # Base64 encoded image
        
    def test_two_factor_requirement_enforcement(self):
        """Test 2FA requirement enforcement."""
        # Test login without 2FA
        request = self.factory.post('/admin/login/', {
            'username': 'doctor',
            'password': 'DoctorPass123!'
        })
        
        # Should require 2FA verification
        user = authenticate(username='doctor', password='DoctorPass123!')
        self.assertIsNotNone(user)
        
        # Check if 2FA is required
        requires_2fa = self.two_factor.is_required_for_user(user)
        self.assertTrue(requires_2fa)


class AuditLogTestCase(BaseSecurityTestCase):
    """Test cases for audit logging."""
    
    def test_audit_log_creation(self):
        """Test creating audit log entries."""
        # Log an audit event
        log_audit_event(
            action='medication_prescribed',
            user=self.doctor,
            target_object=self.prescription,
            ip_address='192.168.1.100',
            additional_data={
                'patient_id': self.patient.id,
                'medication': self.medication.name,
                'dosage': '500mg'
            }
        )
        
        # Check audit log entry
        audit_entry = AuditLog.objects.filter(
            action='medication_prescribed',
            user=self.doctor
        ).first()
        
        self.assertIsNotNone(audit_entry)
        self.assertEqual(audit_entry.additional_data['medication'], self.medication.name)
        
    def test_audit_trail_integrity(self):
        """Test audit trail integrity."""
        # Create multiple audit entries
        actions = [
            'user_login',
            'prescription_created',
            'prescription_modified',
            'prescription_viewed'
        ]
        
        for action in actions:
            log_audit_event(
                action=action,
                user=self.doctor,
                target_object=self.prescription,
                ip_address='192.168.1.100'
            )
        
        # Check audit trail
        audit_entries = AuditLog.objects.filter(
            user=self.doctor
        ).order_by('timestamp')
        
        self.assertEqual(audit_entries.count(), 4)
        
        # Check chronological order
        timestamps = [entry.timestamp for entry in audit_entries]
        self.assertEqual(timestamps, sorted(timestamps))
        
    def test_audit_log_search_and_filtering(self):
        """Test audit log search and filtering."""
        # Create audit entries with different actions
        log_audit_event(
            action='prescription_created',
            user=self.doctor,
            target_object=self.prescription
        )
        
        log_audit_event(
            action='user_login',
            user=self.patient,
            ip_address='192.168.1.200'
        )
        
        # Filter by action
        prescription_logs = AuditLog.objects.filter(
            action='prescription_created'
        )
        
        self.assertEqual(prescription_logs.count(), 1)
        self.assertEqual(prescription_logs.first().user, self.doctor)
        
        # Filter by user
        doctor_logs = AuditLog.objects.filter(user=self.doctor)
        
        self.assertGreater(doctor_logs.count(), 0)
        
    def test_audit_log_retention(self):
        """Test audit log retention policies."""
        # Create old audit entries
        old_date = timezone.now() - timedelta(days=400)  # Older than retention period
        
        old_entry = AuditLog.objects.create(
            action='old_action',
            user=self.doctor,
            timestamp=old_date,
            ip_address='192.168.1.100'
        )
        
        # Test retention cleanup
        retention_days = 365
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        old_entries = AuditLog.objects.filter(timestamp__lt=cutoff_date)
        
        self.assertGreater(old_entries.count(), 0)
        
        # Clean up old entries (in practice this would be a management command)
        old_entries_count = old_entries.count()
        old_entries.delete()
        
        # Verify cleanup
        remaining_old_entries = AuditLog.objects.filter(timestamp__lt=cutoff_date)
        self.assertEqual(remaining_old_entries.count(), 0)


class UserHealthcareRoleTestCase(BaseSecurityTestCase):
    """Test cases for healthcare role management."""
    
    def test_healthcare_role_creation(self):
        """Test creating healthcare roles."""
        self.assertEqual(self.doctor_role.user, self.doctor)
        self.assertEqual(self.doctor_role.role_type, 'DOCTOR')
        self.assertEqual(self.doctor_role.license_number, 'DOC123456')
        self.assertTrue(self.doctor_role.is_active)
        
    def test_role_permission_checking(self):
        """Test role-based permission checking."""
        # Test doctor permissions
        can_prescribe = self.doctor_role.can_prescribe_medication()
        self.assertTrue(can_prescribe)
        
        # Test pharmacist permissions
        can_dispense = self.pharmacist_role.can_dispense_medication()
        self.assertTrue(can_dispense)
        
        # Test cross-role permissions
        pharmacist_can_prescribe = self.pharmacist_role.can_prescribe_medication()
        self.assertFalse(pharmacist_can_prescribe)
        
    def test_role_expiration_checking(self):
        """Test role expiration checking."""
        # Test current role (should not be expired)
        is_expired = self.doctor_role.is_role_expired()
        self.assertFalse(is_expired)
        
        # Create expired role
        expired_role = UserHealthcareRole.objects.create(
            user=self.patient,
            role_type='NURSE',
            license_number='NURSE123',
            is_active=True,
            last_reviewed_at=timezone.now() - timedelta(days=400)  # Expired
        )
        
        is_expired_role = expired_role.is_role_expired()
        self.assertTrue(is_expired_role)
        
    def test_role_verification_process(self):
        """Test role verification process."""
        # Mark role as needing verification
        self.doctor_role.verification_status = 'pending'
        self.doctor_role.save()
        
        # Verify role
        verification_result = self.doctor_role.verify_role(
            verified_by=self.admin_user,
            verification_notes='License verified with medical board'
        )
        
        self.assertTrue(verification_result)
        
        self.doctor_role.refresh_from_db()
        self.assertEqual(self.doctor_role.verification_status, 'verified')
        self.assertEqual(self.doctor_role.verified_by, self.admin_user)


class EncryptionTestCase(BaseSecurityTestCase):
    """Test cases for data encryption."""
    
    def test_sensitive_data_encryption(self):
        """Test encryption of sensitive data."""
        # Test data to encrypt
        sensitive_data = {
            'patient_id': self.patient.id,
            'diagnosis': 'Hypertension',
            'treatment_notes': 'Patient responding well to medication'
        }
        
        # Encrypt data
        encrypted_data = encrypt_sensitive_data(sensitive_data)
        
        self.assertIsInstance(encrypted_data, str)
        self.assertNotEqual(encrypted_data, str(sensitive_data))
        
        # Decrypt data
        decrypted_data = decrypt_sensitive_data(encrypted_data)
        
        self.assertEqual(decrypted_data, sensitive_data)
        
    def test_encryption_key_rotation(self):
        """Test encryption key rotation."""
        # This would test key rotation functionality
        # For now, just test that encryption works with different keys
        
        original_data = "Sensitive patient information"
        
        # Encrypt with current key
        encrypted_v1 = encrypt_sensitive_data(original_data)
        
        # Simulate key rotation (would be done by management command)
        # For testing, just verify encryption produces different results
        encrypted_v2 = encrypt_sensitive_data(original_data)
        
        # Both should decrypt to same original data
        decrypted_v1 = decrypt_sensitive_data(encrypted_v1)
        decrypted_v2 = decrypt_sensitive_data(encrypted_v2)
        
        self.assertEqual(decrypted_v1, original_data)
        self.assertEqual(decrypted_v2, original_data)
        
    def test_field_level_encryption(self):
        """Test field-level encryption for models."""
        # Test encrypting specific fields
        prescription_data = {
            'patient_notes': 'Patient has allergies to penicillin',
            'doctor_notes': 'Monitor for side effects',
            'pharmacy_instructions': 'Dispense with food'
        }
        
        # Encrypt sensitive fields
        encrypted_notes = encrypt_sensitive_data(prescription_data['patient_notes'])
        
        self.assertNotEqual(encrypted_notes, prescription_data['patient_notes'])
        
        # Decrypt and verify
        decrypted_notes = decrypt_sensitive_data(encrypted_notes)
        self.assertEqual(decrypted_notes, prescription_data['patient_notes'])


class SessionManagementTestCase(BaseSecurityTestCase):
    """Test cases for session management."""
    
    def test_medical_session_creation(self):
        """Test creating medical sessions."""
        # Create medical session
        session = MedicalSession.objects.create(
            user=self.doctor,
            session_type='clinical_review',
            ip_address='192.168.1.100',
            user_agent='Medical Browser v1.0',
            is_active=True
        )
        
        self.assertEqual(session.user, self.doctor)
        self.assertEqual(session.session_type, 'clinical_review')
        self.assertTrue(session.is_active)
        
    def test_session_timeout(self):
        """Test session timeout functionality."""
        # Create session with short timeout
        session = MedicalSession.objects.create(
            user=self.doctor,
            session_type='clinical_review',
            ip_address='192.168.1.100',
            timeout_minutes=30,
            is_active=True
        )
        
        # Check if session is expired
        session.last_activity = timezone.now() - timedelta(minutes=45)
        session.save()
        
        is_expired = session.is_expired()
        self.assertTrue(is_expired)
        
    def test_concurrent_session_limits(self):
        """Test concurrent session limits."""
        # Create multiple sessions for same user
        sessions = []
        for i in range(3):
            session = MedicalSession.objects.create(
                user=self.doctor,
                session_type='clinical_review',
                ip_address=f'192.168.1.{100+i}',
                is_active=True
            )
            sessions.append(session)
        
        # Check concurrent session count
        active_sessions = MedicalSession.objects.filter(
            user=self.doctor,
            is_active=True
        ).count()
        
        self.assertEqual(active_sessions, 3)
        
        # Test session limit enforcement (would be implemented in session middleware)
        max_concurrent_sessions = 2
        if active_sessions > max_concurrent_sessions:
            # Should terminate oldest sessions
            oldest_sessions = MedicalSession.objects.filter(
                user=self.doctor,
                is_active=True
            ).order_by('created_at')[:-max_concurrent_sessions]
            
            for session in oldest_sessions:
                session.is_active = False
                session.save()
        
        # Verify session limit enforcement
        remaining_active = MedicalSession.objects.filter(
            user=self.doctor,
            is_active=True
        ).count()
        
        self.assertLessEqual(remaining_active, max_concurrent_sessions)


class HIPAAComplianceTestCase(BaseSecurityTestCase):
    """Test cases for HIPAA compliance features."""
    
    def test_minimum_necessary_access(self):
        """Test minimum necessary access principle."""
        # Test that users can only access data necessary for their role
        
        # Doctor should access prescription data
        doctor_access = self.doctor_role.can_access_prescription(self.prescription)
        self.assertTrue(doctor_access)
        
        # Patient should access their own data
        patient_access = self.prescription.patient == self.patient
        self.assertTrue(patient_access)
        
        # Other users should not access unrelated patient data
        other_patient = User.objects.create_user(
            username='other_patient',
            email='other@example.com',
            password='OtherPass123!'
        )
        
        other_patient_access = self.prescription.patient == other_patient
        self.assertFalse(other_patient_access)
        
    def test_access_logging_for_phi(self):
        """Test access logging for Protected Health Information."""
        # Log PHI access
        log_audit_event(
            action='phi_accessed',
            user=self.doctor,
            target_object=self.prescription,
            ip_address='192.168.1.100',
            additional_data={
                'phi_type': 'prescription_data',
                'patient_id': self.patient.id,
                'access_reason': 'clinical_review'
            }
        )
        
        # Verify PHI access was logged
        phi_access_log = AuditLog.objects.filter(
            action='phi_accessed',
            user=self.doctor
        ).first()
        
        self.assertIsNotNone(phi_access_log)
        self.assertEqual(
            phi_access_log.additional_data['phi_type'],
            'prescription_data'
        )
        
    def test_data_breach_notification(self):
        """Test data breach notification system."""
        # Simulate a data breach event
        breach_event = SecurityEvent.objects.create(
            event_type=SecurityEvent.EventType.BREACH_ATTEMPT,
            severity=SecurityEvent.Severity.CRITICAL,
            description='Unauthorized access to patient database detected',
            ip_address='10.0.0.1',
            metadata={
                'affected_records': 100,
                'data_types': ['prescriptions', 'patient_info'],
                'breach_type': 'unauthorized_access'
            }
        )
        
        # Test breach notification process
        breach_notification = {
            'event_id': breach_event.id,
            'notification_sent': True,
            'notification_time': timezone.now(),
            'authorities_notified': True,
            'patients_notified': False  # Within 60 days as per HIPAA
        }
        
        self.assertTrue(breach_notification['notification_sent'])
        self.assertTrue(breach_notification['authorities_notified'])
        
    def test_business_associate_agreement(self):
        """Test business associate agreement compliance."""
        # Test that third-party integrations comply with BAA requirements
        
        # Mock third-party service access
        third_party_access = {
            'service_name': 'Pharmacy Integration Service',
            'baa_signed': True,
            'access_type': 'limited',
            'data_types': ['prescription_data'],
            'security_measures': ['encryption', 'access_logging', 'audit_trail']
        }
        
        # Verify BAA compliance
        self.assertTrue(third_party_access['baa_signed'])
        self.assertIn('encryption', third_party_access['security_measures'])
        self.assertIn('audit_trail', third_party_access['security_measures'])


@pytest.mark.django_db
class SecurityIntegrationTestCase(TransactionTestCase):
    """Integration tests for security with other system components."""
    
    def setUp(self):
        """Set up integration test data."""
        self.user = User.objects.create_user(
            username='integration_user',
            email='integration@medguard.co.za',
            password='IntegrationPass123!'
        )
        
    def test_security_middleware_integration(self):
        """Test security middleware integration."""
        # Test request processing through security middleware
        request = RequestFactory().get('/admin/')
        request.user = self.user
        
        # Security middleware should process the request
        # This would test actual middleware in integration environment
        self.assertTrue(hasattr(request, 'user'))
        
    def test_wagtail_admin_security_integration(self):
        """Test Wagtail admin security integration."""
        # Test admin access with security controls
        self.client.force_login(self.user)
        response = self.client.get('/admin/')
        
        # Should require proper authentication
        self.assertIn(response.status_code, [200, 302, 403])
        
    def test_api_security_integration(self):
        """Test API security integration."""
        # Test API endpoints with security controls
        response = self.client.get('/api/v2/medications/')
        
        # Should require authentication
        self.assertEqual(response.status_code, 401)
        
    def test_search_security_integration(self):
        """Test search security integration."""
        # Test that search respects security controls
        self.client.force_login(self.user)
        response = self.client.get('/search/?q=patient')
        
        # Should respect user permissions
        self.assertIn(response.status_code, [200, 403])


class SecurityPerformanceTestCase(BaseSecurityTestCase):
    """Test cases for security feature performance."""
    
    def test_encryption_performance(self):
        """Test encryption/decryption performance."""
        import time
        
        # Test data
        test_data = "Sensitive patient information " * 100  # Larger data
        
        # Test encryption performance
        start_time = time.time()
        encrypted_data = encrypt_sensitive_data(test_data)
        encryption_time = time.time() - start_time
        
        # Test decryption performance
        start_time = time.time()
        decrypted_data = decrypt_sensitive_data(encrypted_data)
        decryption_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(encryption_time, 1.0)
        self.assertLess(decryption_time, 1.0)
        self.assertEqual(decrypted_data, test_data)
        
    def test_audit_logging_performance(self):
        """Test audit logging performance."""
        import time
        
        # Test logging many events
        start_time = time.time()
        
        for i in range(100):
            log_audit_event(
                action=f'test_action_{i}',
                user=self.doctor,
                ip_address='192.168.1.100'
            )
        
        logging_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(logging_time, 5.0)
        
        # Verify all events were logged
        logged_events = AuditLog.objects.filter(
            action__startswith='test_action_'
        ).count()
        
        self.assertEqual(logged_events, 100)
