#!/usr/bin/env python
"""
Test script to debug authentication issues.
"""

import os
import sys
import django
import requests
import json

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
django.setup()

from django.contrib.auth import authenticate
from users.models import User

def test_authentication():
    """Test authentication directly."""
    print("Testing authentication...")
    
    # Test with the known user
    username = "immunothreat"
    password = "test123"
    
    # Test Django's authenticate function
    user = authenticate(username=username, password=password)
    
    if user is None:
        print("❌ Authentication failed - user is None")
        return False
    elif not user.is_active:
        print("❌ Authentication failed - user is not active")
        return False
    else:
        print(f"✅ Authentication successful for user: {user.username}")
        print(f"   User ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Is active: {user.is_active}")
        print(f"   Is staff: {user.is_staff}")
        print(f"   Is superuser: {user.is_superuser}")
        return True

def test_api_endpoint():
    """Test the API endpoint."""
    print("\nTesting API endpoint...")
    
    url = "http://localhost:8000/api/users/auth/login/"
    data = {
        "username": "immunothreat",
        "password": "test123"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ API endpoint working")
            return True
        else:
            print("❌ API endpoint failed")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_user_exists():
    """Test if the user exists in the database."""
    print("\nTesting user existence...")
    
    try:
        user = User.objects.get(username="immunothreat")
        print(f"✅ User found: {user.username}")
        print(f"   User ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Is active: {user.is_active}")
        print(f"   Has password: {bool(user.password)}")
        return True
    except User.DoesNotExist:
        print("❌ User not found")
        return False

if __name__ == "__main__":
    print("=== Authentication Debug Test ===\n")
    
    # Test 1: Check if user exists
    user_exists = test_user_exists()
    
    # Test 2: Test Django authentication
    if user_exists:
        auth_success = test_authentication()
    
    # Test 3: Test API endpoint
    api_success = test_api_endpoint()
    
    print("\n=== Summary ===")
    print(f"User exists: {'✅' if user_exists else '❌'}")
    if user_exists:
        print(f"Django auth: {'✅' if auth_success else '❌'}")
    print(f"API endpoint: {'✅' if api_success else '❌'}") 