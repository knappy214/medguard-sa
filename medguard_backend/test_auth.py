#!/usr/bin/env python
"""
Test script for authentication functionality.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
django.setup()

from django.contrib.auth import authenticate
from users.models import User

def test_authentication():
    """Test user authentication."""
    print("Testing authentication...")
    
    # Get the first user
    user = User.objects.first()
    if not user:
        print("No users found in database")
        return
    
    print(f"Testing with user: {user.username}")
    print(f"User is active: {user.is_active}")
    print(f"User has password: {bool(user.password)}")
    
    # Try to authenticate with a test password
    test_password = "test123"
    authenticated_user = authenticate(username=user.username, password=test_password)
    
    if authenticated_user:
        print(f"Authentication successful for {authenticated_user.username}")
    else:
        print("Authentication failed")
        
        # Try to create a new password for the user
        print("Setting new password...")
        user.set_password(test_password)
        user.save()
        print("Password set successfully")
        
        # Try authentication again
        authenticated_user = authenticate(username=user.username, password=test_password)
        if authenticated_user:
            print(f"Authentication successful after password reset for {authenticated_user.username}")
        else:
            print("Authentication still failed after password reset")

if __name__ == "__main__":
    test_authentication() 