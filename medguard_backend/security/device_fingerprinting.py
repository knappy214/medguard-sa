"""
Device fingerprinting utilities for enhanced security validation.

This module provides utilities for generating and validating device fingerprints
to enhance security and detect potential unauthorized access.
"""

import hashlib
import json
import logging
from typing import Dict, Optional, Any
from django.http import HttpRequest
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class DeviceFingerprinter:
    """
    Device fingerprinting utility for security validation.
    
    This class provides methods to generate and validate device fingerprints
    based on various request characteristics.
    """
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 hour cache for device fingerprints
    
    def generate_fingerprint(self, request: HttpRequest) -> str:
        """
        Generate a device fingerprint from request data.
        
        Args:
            request: The HTTP request object
            
        Returns:
            A unique device fingerprint string
        """
        try:
            # Get basic request information
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = self._get_client_ip(request)
            
            # Get additional headers that can help identify the device
            accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
            accept = request.META.get('HTTP_ACCEPT', '')
            
            # Get custom device fingerprint if provided
            custom_fingerprint = request.META.get('HTTP_X_DEVICE_FINGERPRINT', '')
            
            # Create fingerprint data
            fingerprint_data = {
                'user_agent': user_agent,
                'ip_address': ip_address,
                'accept_language': accept_language,
                'accept_encoding': accept_encoding,
                'accept': accept,
                'custom_fingerprint': custom_fingerprint,
                'timestamp': timezone.now().isoformat()
            }
            
            # Generate hash from fingerprint data
            fingerprint_json = json.dumps(fingerprint_data, sort_keys=True)
            fingerprint_hash = hashlib.sha256(fingerprint_json.encode()).hexdigest()
            
            return fingerprint_hash
            
        except Exception as e:
            logger.error(f"Error generating device fingerprint: {str(e)}")
            # Fallback to basic fingerprint
            return self._generate_basic_fingerprint(request)
    
    def _generate_basic_fingerprint(self, request: HttpRequest) -> str:
        """
        Generate a basic device fingerprint as fallback.
        
        Args:
            request: The HTTP request object
            
        Returns:
            A basic device fingerprint string
        """
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = self._get_client_ip(request)
        
        # Simple hash of user agent and IP
        basic_data = f"{ip_address}:{user_agent}"
        return hashlib.md5(basic_data.encode()).hexdigest()
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Get the client IP address from the request.
        
        Args:
            request: The HTTP request object
            
        Returns:
            The client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        return ip
    
    def validate_fingerprint(self, request: HttpRequest, stored_fingerprint: str) -> bool:
        """
        Validate a device fingerprint against the current request.
        
        Args:
            request: The HTTP request object
            stored_fingerprint: The stored device fingerprint to validate against
            
        Returns:
            True if the fingerprint is valid, False otherwise
        """
        try:
            current_fingerprint = self.generate_fingerprint(request)
            return current_fingerprint == stored_fingerprint
            
        except Exception as e:
            logger.error(f"Error validating device fingerprint: {str(e)}")
            return False
    
    def store_fingerprint(self, user_id: int, fingerprint: str) -> bool:
        """
        Store a device fingerprint in cache.
        
        Args:
            user_id: The user ID
            fingerprint: The device fingerprint
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            cache_key = f"device_fingerprint:{user_id}"
            cache.set(cache_key, fingerprint, self.cache_timeout)
            return True
            
        except Exception as e:
            logger.error(f"Error storing device fingerprint: {str(e)}")
            return False
    
    def get_stored_fingerprint(self, user_id: int) -> Optional[str]:
        """
        Get a stored device fingerprint from cache.
        
        Args:
            user_id: The user ID
            
        Returns:
            The stored device fingerprint or None if not found
        """
        try:
            cache_key = f"device_fingerprint:{user_id}"
            return cache.get(cache_key)
            
        except Exception as e:
            logger.error(f"Error retrieving device fingerprint: {str(e)}")
            return None
    
    def clear_fingerprint(self, user_id: int) -> bool:
        """
        Clear a stored device fingerprint from cache.
        
        Args:
            user_id: The user ID
            
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            cache_key = f"device_fingerprint:{user_id}"
            cache.delete(cache_key)
            return True
            
        except Exception as e:
            logger.error(f"Error clearing device fingerprint: {str(e)}")
            return False
    
    def analyze_fingerprint_risk(self, request: HttpRequest, user_id: int) -> Dict[str, Any]:
        """
        Analyze the risk level of a device fingerprint.
        
        Args:
            request: The HTTP request object
            user_id: The user ID
            
        Returns:
            Dictionary containing risk analysis results
        """
        try:
            current_fingerprint = self.generate_fingerprint(request)
            stored_fingerprint = self.get_stored_fingerprint(user_id)
            
            risk_analysis = {
                'risk_level': 'low',
                'risk_score': 0,
                'risk_factors': [],
                'fingerprint_match': False,
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100]
            }
            
            # Check if fingerprint matches stored fingerprint
            if stored_fingerprint:
                fingerprint_match = current_fingerprint == stored_fingerprint
                risk_analysis['fingerprint_match'] = fingerprint_match
                
                if not fingerprint_match:
                    risk_analysis['risk_level'] = 'high'
                    risk_analysis['risk_score'] = 80
                    risk_analysis['risk_factors'].append('device_fingerprint_mismatch')
            
            # Check for suspicious IP patterns
            ip_address = self._get_client_ip(request)
            if self._is_suspicious_ip(ip_address):
                risk_analysis['risk_score'] += 20
                risk_analysis['risk_factors'].append('suspicious_ip_address')
            
            # Check for missing or suspicious user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            if not user_agent or self._is_suspicious_user_agent(user_agent):
                risk_analysis['risk_score'] += 15
                risk_analysis['risk_factors'].append('suspicious_user_agent')
            
            # Update risk level based on score
            if risk_analysis['risk_score'] >= 50:
                risk_analysis['risk_level'] = 'high'
            elif risk_analysis['risk_score'] >= 20:
                risk_analysis['risk_level'] = 'medium'
            
            return risk_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing fingerprint risk: {str(e)}")
            return {
                'risk_level': 'unknown',
                'risk_score': 0,
                'risk_factors': ['analysis_error'],
                'fingerprint_match': False
            }
    
    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """
        Check if an IP address is suspicious.
        
        Args:
            ip_address: The IP address to check
            
        Returns:
            True if suspicious, False otherwise
        """
        # Add logic to detect suspicious IP addresses
        # This could include checking against known malicious IP lists
        # For now, we'll use a simple heuristic
        
        if not ip_address:
            return True
        
        # Check for localhost or private IP ranges
        if ip_address in ['127.0.0.1', 'localhost']:
            return True
        
        # Check for private IP ranges
        if ip_address.startswith(('10.', '172.16.', '192.168.')):
            return False  # Private IPs are generally safe
        
        # Add more sophisticated checks here
        return False
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """
        Check if a user agent string is suspicious.
        
        Args:
            user_agent: The user agent string to check
            
        Returns:
            True if suspicious, False otherwise
        """
        if not user_agent:
            return True
        
        # Check for common bot user agents
        bot_indicators = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'python', 'java', 'perl', 'ruby', 'php'
        ]
        
        user_agent_lower = user_agent.lower()
        for indicator in bot_indicators:
            if indicator in user_agent_lower:
                return True
        
        # Check for very short user agents
        if len(user_agent) < 10:
            return True
        
        return False


# Global instance
device_fingerprinter = DeviceFingerprinter()


def get_device_fingerprint(request: HttpRequest) -> str:
    """
    Get device fingerprint for a request.
    
    Args:
        request: The HTTP request object
        
    Returns:
        The device fingerprint string
    """
    return device_fingerprinter.generate_fingerprint(request)


def validate_device_fingerprint(request: HttpRequest, stored_fingerprint: str) -> bool:
    """
    Validate device fingerprint for a request.
    
    Args:
        request: The HTTP request object
        stored_fingerprint: The stored device fingerprint
        
    Returns:
        True if valid, False otherwise
    """
    return device_fingerprinter.validate_fingerprint(request, stored_fingerprint)


def analyze_device_risk(request: HttpRequest, user_id: int) -> Dict[str, Any]:
    """
    Analyze device risk for a request.
    
    Args:
        request: The HTTP request object
        user_id: The user ID
        
    Returns:
        Risk analysis dictionary
    """
    return device_fingerprinter.analyze_fingerprint_risk(request, user_id) 