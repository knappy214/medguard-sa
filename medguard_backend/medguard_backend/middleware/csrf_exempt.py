"""
CSRF exemption middleware for API endpoints.

This middleware exempts API endpoints from CSRF protection in development.
"""

import re
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class CSRFExemptMiddleware(MiddlewareMixin):
    """
    Middleware to exempt API endpoints from CSRF protection.
    """
    
    def process_request(self, request):
        """Process request and exempt API endpoints from CSRF."""
        if hasattr(settings, 'CSRF_EXEMPT_URLS') and settings.CSRF_EXEMPT_URLS:
            path = request.path_info.lstrip('/')
            
            for pattern in settings.CSRF_EXEMPT_URLS:
                if re.match(pattern, path):
                    setattr(request, '_dont_enforce_csrf_checks', True)
                    break
        
        return None 