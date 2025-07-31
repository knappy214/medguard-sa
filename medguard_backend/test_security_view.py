import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
django.setup()

from django.test import RequestFactory
from security.views import log_security_event_public_view
from django.http import JsonResponse

def test_security_view():
    print("Testing security view directly...")
    
    # Create a test request
    factory = RequestFactory()
    
    # Test data matching what frontend sends
    test_data = {
        "eventType": "LOGIN_FAILURE",
        "timestamp": "2025-01-31T10:00:00Z",
        "deviceId": "test-device-123",
        "userId": None,
        "userAgent": "test-user-agent",
        "ipAddress": "127.0.0.1",
        "data": {"reason": "test failure"}
    }
    
    # Create request
    request = factory.post(
        '/api/security/log-public/',
        data=json.dumps(test_data),
        content_type='application/json',
        HTTP_X_DEVICE_ID='test-device-123'
    )
    
    try:
        # Call the view directly
        response = log_security_event_public_view(request)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        
        if response.status_code == 200:
            print("✅ Security view is working!")
        else:
            print(f"❌ Security view failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception in security view: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_security_view() 