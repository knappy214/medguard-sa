#!/usr/bin/env python
import os
import django
import traceback

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
django.setup()

from security.audit import log_audit_event, AuditLog
from django.test import RequestFactory

def test_audit_logging_directly():
    """Test the audit logging function directly"""
    print("Testing audit logging function directly...")
    
    try:
        # Create a mock request
        factory = RequestFactory()
        request = factory.post('/api/security/log-public/')
        request.META['HTTP_USER_AGENT'] = 'test-user-agent'
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        # Test logging a security event
        audit_log = log_audit_event(
            user=None,
            action='login_failure',
            description='Test login failure',
            severity='medium',
            request=request,
            metadata={'test': True}
        )
        
        print(f"✅ Audit log created successfully: {audit_log.id}")
        print(f"Action: {audit_log.action}")
        print(f"Description: {audit_log.description}")
        print(f"Severity: {audit_log.severity}")
        
    except Exception as e:
        print(f"❌ Error in audit logging: {e}")
        print("Full traceback:")
        traceback.print_exc()

def test_audit_log_model():
    """Test creating an audit log entry directly"""
    print("\nTesting audit log model directly...")
    
    try:
        # Test creating an audit log entry directly
        audit_log = AuditLog.objects.create(
            user=None,
            action='login_failure',
            description='Test login failure',
            severity='medium',
            object_repr='test',
            metadata={'test': True}
        )
        
        print(f"✅ Audit log created directly: {audit_log.id}")
        
    except Exception as e:
        print(f"❌ Error creating audit log directly: {e}")
        print("Full traceback:")
        traceback.print_exc()

def test_action_choices():
    """Test the action choices"""
    print("\nTesting action choices...")
    
    try:
        choices = AuditLog.ActionType.choices
        print("Available action choices:")
        for choice in choices:
            print(f"  {choice[0]}: {choice[1]}")
        
        # Test if our new choices are there
        new_choices = ['login_success', 'login_failure', 'security_event']
        for choice in new_choices:
            if choice in [c[0] for c in choices]:
                print(f"✅ {choice} is available")
            else:
                print(f"❌ {choice} is NOT available")
                
    except Exception as e:
        print(f"❌ Error testing action choices: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_action_choices()
    test_audit_log_model()
    test_audit_logging_directly() 