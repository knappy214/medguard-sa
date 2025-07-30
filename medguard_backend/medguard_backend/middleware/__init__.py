"""
Middleware package for MedGuard backend.

This package contains custom middleware components for:
- Mobile optimization
- Performance monitoring
- Security enhancements
- Caching strategies
"""

from .mobile import MobileOptimizationMiddleware, MobileCachingMiddleware

__all__ = [
    'MobileOptimizationMiddleware',
    'MobileCachingMiddleware',
] 