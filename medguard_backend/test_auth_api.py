#!/usr/bin/env python
"""
Test script to verify the authentication API endpoints.
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

def test_api_endpoints():
    """Test the authentication API endpoints."""
    base_url = 'http://localhost:8000'
    
    print("Testing Authentication API Endpoints...")
    print("=" * 50)
    
    # Test 1: Test endpoint
    print("\n1. Testing /api/test/ endpoint...")
    try:
        response = requests.get(f'{base_url}/api/test/')
        if response.status_code == 200:
            print("✅ Test endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Test endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Test endpoint error: {e}")
    
    # Test 2: Login endpoint
    print("\n2. Testing /api/users/auth/login/ endpoint...")
    try:
        login_data = {
            'username': 'testuser',
            'password': 'test123'
        }
        
        response = requests.post(
            f'{base_url}/api/users/auth/login/',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("✅ Login endpoint working")
            data = response.json()
            print(f"   Message: {data.get('message')}")
            print(f"   User ID: {data.get('user', {}).get('id')}")
            print(f"   Username: {data.get('user', {}).get('username')}")
            print(f"   Has access token: {'access_token' in data}")
            print(f"   Has refresh token: {'refresh_token' in data}")
            
            # Store tokens for further testing
            access_token = data.get('access_token')
            refresh_token = data.get('refresh_token')
            
            # Test 3: Validate token endpoint
            if access_token:
                print("\n3. Testing /api/users/auth/validate/ endpoint...")
                try:
                    headers = {
                        'Authorization': f'Bearer {access_token}',
                        'Content-Type': 'application/json'
                    }
                    
                    validate_response = requests.get(
                        f'{base_url}/api/users/auth/validate/',
                        headers=headers
                    )
                    
                    if validate_response.status_code == 200:
                        print("✅ Token validation working")
                        validate_data = validate_response.json()
                        print(f"   User ID: {validate_data.get('user', {}).get('id')}")
                    else:
                        print(f"❌ Token validation failed: {validate_response.status_code}")
                        print(f"   Response: {validate_response.text}")
                except Exception as e:
                    print(f"❌ Token validation error: {e}")
            
            # Test 4: Refresh token endpoint
            if refresh_token:
                print("\n4. Testing /api/users/auth/refresh/ endpoint...")
                try:
                    refresh_data = {
                        'refresh': refresh_token
                    }
                    
                    refresh_response = requests.post(
                        f'{base_url}/api/users/auth/refresh/',
                        json=refresh_data,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if refresh_response.status_code == 200:
                        print("✅ Token refresh working")
                        refresh_data = refresh_response.json()
                        print(f"   Has new access token: {'access' in refresh_data}")
                    else:
                        print(f"❌ Token refresh failed: {refresh_response.status_code}")
                        print(f"   Response: {refresh_response.text}")
                except Exception as e:
                    print(f"❌ Token refresh error: {e}")
            
            # Test 5: Logout endpoint
            if access_token:
                print("\n5. Testing /api/users/auth/logout/ endpoint...")
                try:
                    headers = {
                        'Authorization': f'Bearer {access_token}',
                        'Content-Type': 'application/json'
                    }
                    
                    logout_response = requests.post(
                        f'{base_url}/api/users/auth/logout/',
                        headers=headers
                    )
                    
                    if logout_response.status_code == 200:
                        print("✅ Logout endpoint working")
                        print(f"   Response: {logout_response.json()}")
                    else:
                        print(f"❌ Logout failed: {logout_response.status_code}")
                        print(f"   Response: {logout_response.text}")
                except Exception as e:
                    print(f"❌ Logout error: {e}")
            
        else:
            print(f"❌ Login endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Login endpoint error: {e}")

def create_test_user():
    """Create a test user if it doesn't exist."""
    print("\nCreating test user...")
    try:
        # Delete existing test user if it exists
        User.objects.filter(username='testuser').delete()
        
        # Create new test user
        user = User.objects.create_user(
            username='testuser',
            email='test@medguard-sa.com',
            password='test123',
            user_type='patient',
            is_active=True,
            first_name='Test',
            last_name='User',
            preferred_language='en'
        )
        
        print("✅ Test user created successfully")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Password: test123")
        print(f"   User Type: {user.user_type}")
        print(f"   Is Active: {user.is_active}")
        
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("MedGuard SA Authentication API Test")
    print("=" * 50)
    
    # Create test user first
    create_test_user()
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("Test completed!") 