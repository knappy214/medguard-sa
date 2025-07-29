"""
Secure JWT authentication system for API access.

This module provides JWT-based authentication with enhanced security features
for HIPAA compliance and South African POPIA regulations.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Union
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.utils import datetime_from_epoch, datetime_to_epoch

User = get_user_model()
logger = logging.getLogger(__name__)


class HIPAACompliantJWTAuthentication(JWTAuthentication):
    """
    HIPAA-compliant JWT authentication with enhanced security features.
    
    This authentication class provides additional security measures:
    - Token blacklisting for logout
    - IP address validation
    - Device fingerprinting
    - Rate limiting
    - Audit logging
    """
    
    def authenticate(self, request):
        """Authenticate the request and return a two-tuple of (user, token)."""
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        
        # Additional HIPAA security checks
        self._perform_security_checks(request, validated_token)
        
        user = self.get_user(validated_token)
        
        # Log successful authentication
        self._log_authentication(request, user, validated_token)
        
        return (user, validated_token)
    
    def _perform_security_checks(self, request, token):
        """Perform additional security checks for HIPAA compliance."""
        # Check if token is blacklisted
        if self._is_token_blacklisted(token):
            raise AuthenticationFailed('Token has been revoked')
        
        # Validate IP address (if stored in token)
        if not self._validate_ip_address(request, token):
            raise AuthenticationFailed('Invalid IP address for token')
        
        # Check rate limiting
        if not self._check_rate_limit(request, token):
            raise AuthenticationFailed('Rate limit exceeded')
        
        # Validate device fingerprint
        if not self._validate_device_fingerprint(request, token):
            raise AuthenticationFailed('Invalid device fingerprint')
    
    def _is_token_blacklisted(self, token) -> bool:
        """Check if token is in blacklist."""
        token_id = token.get('jti')
        if not token_id:
            return False
        
        return cache.get(f'token_blacklist:{token_id}') is not None
    
    def _validate_ip_address(self, request, token) -> bool:
        """Validate IP address against token."""
        token_ip = token.get('ip_address')
        if not token_ip:
            return True  # No IP stored in token
        
        current_ip = self._get_client_ip(request)
        return token_ip == current_ip
    
    def _validate_device_fingerprint(self, request, token) -> bool:
        """Validate device fingerprint against token."""
        token_fingerprint = token.get('device_fingerprint')
        if not token_fingerprint:
            return True  # No fingerprint stored in token
        
        current_fingerprint = self._get_device_fingerprint(request)
        return token_fingerprint == current_fingerprint
    
    def _check_rate_limit(self, request, token) -> bool:
        """Check rate limiting for authentication attempts."""
        user_id = token.get('user_id')
        if not user_id:
            return True
        
        cache_key = f'auth_rate_limit:{user_id}'
        attempts = cache.get(cache_key, 0)
        
        if attempts >= 10:  # Max 10 attempts per minute
            return False
        
        cache.set(cache_key, attempts + 1, 60)  # 1 minute window
        return True
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_device_fingerprint(self, request) -> str:
        """Generate device fingerprint from request."""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        
        # Simple fingerprint (in production, use more sophisticated method)
        fingerprint = f"{user_agent}:{accept_language}:{accept_encoding}"
        return fingerprint
    
    def _log_authentication(self, request, user, token):
        """Log authentication event for audit purposes."""
        from security.audit import log_audit_event, AuditLog
        
        log_audit_event(
            user=user,
            action=AuditLog.ActionType.LOGIN,
            description=f"JWT authentication successful from {self._get_client_ip(request)}",
            severity=AuditLog.Severity.LOW,
            request=request,
            metadata={
                'auth_method': 'jwt',
                'token_id': token.get('jti'),
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )


class SecureTokenGenerator:
    """
    Secure token generator with HIPAA-compliant features.
    
    This class generates JWT tokens with additional security metadata
    for audit and compliance purposes.
    """
    
    def __init__(self):
        self.access_token_lifetime = api_settings.ACCESS_TOKEN_LIFETIME
        self.refresh_token_lifetime = api_settings.REFRESH_TOKEN_LIFETIME
    
    def generate_tokens(self, user, request=None) -> Dict[str, str]:
        """
        Generate access and refresh tokens for user.
        
        Args:
            user: User object
            request: Django request object (for metadata)
            
        Returns:
            Dictionary with access and refresh tokens
        """
        # Generate tokens
        access_token = AccessToken()
        refresh_token = RefreshToken()
        
        # Add user claims
        access_token['user_id'] = user.id
        access_token['username'] = user.username
        access_token['email'] = user.email
        access_token['user_type'] = user.user_type
        
        # Add security metadata
        if request:
            access_token['ip_address'] = self._get_client_ip(request)
            access_token['device_fingerprint'] = self._get_device_fingerprint(request)
            access_token['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        # Add HIPAA compliance metadata
        access_token['hipaa_compliant'] = True
        access_token['popia_compliant'] = True
        access_token['audit_enabled'] = True
        
        # Set expiration
        access_token.set_exp(lifetime=self.access_token_lifetime)
        refresh_token.set_exp(lifetime=self.refresh_token_lifetime)
        
        # Store token metadata for audit
        self._store_token_metadata(access_token, user, request)
        
        return {
            'access': str(access_token),
            'refresh': str(refresh_token),
            'token_type': 'Bearer',
            'expires_in': self.access_token_lifetime.total_seconds(),
        }
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_device_fingerprint(self, request) -> str:
        """Generate device fingerprint."""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        
        fingerprint = f"{user_agent}:{accept_language}:{accept_encoding}"
        return fingerprint
    
    def _store_token_metadata(self, token, user, request):
        """Store token metadata for audit purposes."""
        token_id = token.get('jti')
        if not token_id:
            return
        
        metadata = {
            'user_id': user.id,
            'username': user.username,
            'created_at': timezone.now().isoformat(),
            'expires_at': datetime_from_epoch(token.get('exp')).isoformat(),
            'ip_address': self._get_client_ip(request) if request else None,
            'user_agent': request.META.get('HTTP_USER_AGENT', '') if request else None,
        }
        
        # Store in cache for quick access
        cache.set(f'token_metadata:{token_id}', metadata, timeout=3600)  # 1 hour


class TokenBlacklistManager:
    """
    Token blacklist manager for secure logout.
    
    This class manages token blacklisting to ensure secure logout
    and prevent token reuse after logout.
    """
    
    def blacklist_token(self, token_string: str, user=None) -> bool:
        """
        Blacklist a token.
        
        Args:
            token_string: JWT token string
            user: User who owns the token
            
        Returns:
            True if token was blacklisted successfully
        """
        try:
            token = AccessToken(token_string)
            token_id = token.get('jti')
            
            if not token_id:
                return False
            
            # Add to blacklist cache
            cache.set(f'token_blacklist:{token_id}', True, timeout=3600)  # 1 hour
            
            # Log blacklist event
            if user:
                from security.audit import log_audit_event, AuditLog
                log_audit_event(
                    user=user,
                    action=AuditLog.ActionType.LOGOUT,
                    description=f"Token blacklisted: {token_id}",
                    severity=AuditLog.Severity.LOW,
                    metadata={'token_id': token_id, 'action': 'blacklist'}
                )
            
            return True
            
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Failed to blacklist invalid token: {str(e)}")
            return False
    
    def is_blacklisted(self, token_string: str) -> bool:
        """
        Check if token is blacklisted.
        
        Args:
            token_string: JWT token string
            
        Returns:
            True if token is blacklisted
        """
        try:
            token = AccessToken(token_string)
            token_id = token.get('jti')
            
            if not token_id:
                return False
            
            return cache.get(f'token_blacklist:{token_id}') is not None
            
        except (InvalidToken, TokenError):
            return True  # Invalid tokens are considered blacklisted
    
    def clear_expired_blacklist(self):
        """Clear expired tokens from blacklist."""
        # This would be implemented with a periodic task
        # For now, we rely on cache expiration
        pass


class JWTRateLimiter:
    """
    Rate limiter for JWT authentication attempts.
    
    This class provides rate limiting to prevent brute force attacks
    on authentication endpoints.
    """
    
    def __init__(self):
        self.max_attempts = 10
        self.window_seconds = 60
    
    def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if request is within rate limits.
        
        Args:
            identifier: Unique identifier (user ID, IP, etc.)
            
        Returns:
            True if request is allowed
        """
        cache_key = f'jwt_rate_limit:{identifier}'
        attempts = cache.get(cache_key, 0)
        
        if attempts >= self.max_attempts:
            return False
        
        cache.set(cache_key, attempts + 1, self.window_seconds)
        return True
    
    def reset_rate_limit(self, identifier: str):
        """Reset rate limit for identifier."""
        cache_key = f'jwt_rate_limit:{identifier}'
        cache.delete(cache_key)


# Global instances
_token_generator = None
_blacklist_manager = None
_rate_limiter = None


def get_token_generator() -> SecureTokenGenerator:
    """Get global token generator instance."""
    global _token_generator
    if _token_generator is None:
        _token_generator = SecureTokenGenerator()
    return _token_generator


def get_blacklist_manager() -> TokenBlacklistManager:
    """Get global blacklist manager instance."""
    global _blacklist_manager
    if _blacklist_manager is None:
        _blacklist_manager = TokenBlacklistManager()
    return _blacklist_manager


def get_rate_limiter() -> JWTRateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = JWTRateLimiter()
    return _rate_limiter


def generate_secure_tokens(user, request=None) -> Dict[str, str]:
    """
    Generate secure JWT tokens for user.
    
    Args:
        user: User object
        request: Django request object
        
    Returns:
        Dictionary with tokens
    """
    generator = get_token_generator()
    return generator.generate_tokens(user, request)


def blacklist_token(token_string: str, user=None) -> bool:
    """
    Blacklist a JWT token.
    
    Args:
        token_string: JWT token string
        user: User who owns the token
        
    Returns:
        True if token was blacklisted successfully
    """
    manager = get_blacklist_manager()
    return manager.blacklist_token(token_string, user)


def check_jwt_rate_limit(identifier: str) -> bool:
    """
    Check JWT rate limit.
    
    Args:
        identifier: Unique identifier
        
    Returns:
        True if request is allowed
    """
    limiter = get_rate_limiter()
    return limiter.check_rate_limit(identifier) 