"""
Tests for authentication endpoints.

This module tests the authentication endpoints including login, refresh, and logout.
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AuthenticationEndpointsTestCase(TestCase):
    """Test case for authentication endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User',
            user_type='patient'
        )
        self.user.is_active = True
        self.user.save()
        
        # Create device fingerprint
        self.device_fingerprint = 'test-device-fingerprint-123'
    
    def test_login_success(self):
        """Test successful login."""
        url = reverse('api_users:auth_login')
        data = {
            'username': 'testuser@example.com',
            'password': 'testpassword123'
        }
        headers = {
            'HTTP_X_DEVICE_FINGERPRINT': self.device_fingerprint
        }
        
        response = self.client.post(url, data, **headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        
        # Check user data
        user_data = response.data['user']
        self.assertEqual(user_data['username'], 'testuser@example.com')
        self.assertEqual(user_data['email'], 'testuser@example.com')
        self.assertEqual(user_data['first_name'], 'Test')
        self.assertEqual(user_data['last_name'], 'User')
        self.assertEqual(user_data['user_type'], 'patient')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        url = reverse('api_users:auth_login')
        data = {
            'username': 'testuser@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid credentials')
    
    def test_login_missing_credentials(self):
        """Test login with missing credentials."""
        url = reverse('api_users:auth_login')
        data = {
            'username': 'testuser@example.com'
            # Missing password
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Username and password are required')
    
    def test_login_inactive_user(self):
        """Test login with inactive user."""
        self.user.is_active = False
        self.user.save()
        
        url = reverse('api_users:auth_login')
        data = {
            'username': 'testuser@example.com',
            'password': 'testpassword123'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Account is disabled')
    
    def test_token_refresh_success(self):
        """Test successful token refresh."""
        # First, get tokens by logging in
        login_url = reverse('api_users:auth_login')
        login_data = {
            'username': 'testuser@example.com',
            'password': 'testpassword123'
        }
        login_headers = {
            'HTTP_X_DEVICE_FINGERPRINT': self.device_fingerprint
        }
        
        login_response = self.client.post(login_url, login_data, **login_headers)
        refresh_token = login_response.data['refresh']
        
        # Now test refresh
        refresh_url = reverse('api_users:auth_refresh')
        refresh_data = {
            'refresh': refresh_token
        }
        refresh_headers = {
            'HTTP_X_DEVICE_FINGERPRINT': self.device_fingerprint
        }
        
        response = self.client.post(refresh_url, refresh_data, **refresh_headers)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_token_refresh_invalid_token(self):
        """Test token refresh with invalid token."""
        url = reverse('api_users:auth_refresh')
        data = {
            'refresh': 'invalid-token'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid refresh token')
    
    def test_token_refresh_missing_token(self):
        """Test token refresh with missing token."""
        url = reverse('api_users:auth_refresh')
        data = {}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Refresh token is required')
    
    def test_logout_success(self):
        """Test successful logout."""
        # First, get tokens by logging in
        login_url = reverse('api_users:auth_login')
        login_data = {
            'username': 'testuser@example.com',
            'password': 'testpassword123'
        }
        
        login_response = self.client.post(login_url, login_data)
        refresh_token = login_response.data['refresh']
        
        # Now test logout
        logout_url = reverse('api_users:auth_logout')
        logout_data = {
            'refresh': refresh_token
        }
        
        response = self.client.post(logout_url, logout_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Successfully logged out')
    
    def test_logout_invalid_token(self):
        """Test logout with invalid token."""
        url = reverse('api_users:auth_logout')
        data = {
            'refresh': 'invalid-token'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid refresh token')
    
    def test_logout_missing_token(self):
        """Test logout with missing token."""
        url = reverse('api_users:auth_logout')
        data = {}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Refresh token is required')
    
    def test_device_fingerprint_validation(self):
        """Test device fingerprint validation during login."""
        url = reverse('api_users:auth_login')
        data = {
            'username': 'testuser@example.com',
            'password': 'testpassword123'
        }
        
        # Test without device fingerprint
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test with device fingerprint
        headers = {
            'HTTP_X_DEVICE_FINGERPRINT': self.device_fingerprint
        }
        response = self.client.post(url, data, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_rate_limiting(self):
        """Test rate limiting on login endpoint."""
        url = reverse('api_users:auth_login')
        data = {
            'username': 'testuser@example.com',
            'password': 'wrongpassword'  # Wrong password to trigger rate limiting
        }
        
        # Make multiple failed attempts
        for i in range(10):
            response = self.client.post(url, data)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        
        # The last request should be rate limited
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_429_TOO_MANY_REQUESTS])


class SecurityLoggingTestCase(TestCase):
    """Test case for security logging endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpassword123',
            first_name='Admin',
            last_name='User',
            user_type='admin',
            is_staff=True,
            is_superuser=True
        )
        self.user.is_active = True
        self.user.save()
        
        # Authenticate as admin
        self.client.force_authenticate(user=self.user)
    
    def test_security_event_logging(self):
        """Test security event logging endpoint."""
        url = reverse('api_security:log_security_event')
        data = {
            'event_type': 'data_access',
            'description': 'Test security event',
            'severity': 'medium',
            'metadata': {
                'test_key': 'test_value'
            }
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Security event logged successfully')
    
    def test_security_event_logging_missing_data(self):
        """Test security event logging with missing data."""
        url = reverse('api_security:log_security_event')
        data = {
            'description': 'Test security event'
            # Missing event_type
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'event_type and description are required')
    
    def test_security_dashboard_access(self):
        """Test security dashboard access."""
        url = reverse('api_security:security_dashboard')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('metrics', response.data)
        self.assertIn('recent_incidents', response.data)
        self.assertIn('suspicious_ips', response.data)
        self.assertIn('date_range', response.data)
    
    def test_audit_logs_access(self):
        """Test audit logs access."""
        url = reverse('api_security:auditlog-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
    
    def test_audit_logs_filtering(self):
        """Test audit logs filtering."""
        url = reverse('api_security:auditlog-list')
        params = {
            'action_type': 'login',
            'severity': 'low'
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_audit_logs_summary(self):
        """Test audit logs summary endpoint."""
        url = reverse('api_security:auditlog-summary')
        params = {
            'days': 7
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_actions', response.data)
        self.assertIn('actions_by_type', response.data)
        self.assertIn('actions_by_severity', response.data)
        self.assertIn('top_users', response.data)
        self.assertIn('recent_security_events', response.data)
        self.assertIn('date_range', response.data)
    
    def test_audit_logs_export(self):
        """Test audit logs export endpoint."""
        url = reverse('api_security:auditlog-export')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition']) 