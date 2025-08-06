"""
MedGuard Performance Optimizations Package.

This package contains comprehensive performance optimizations for the MedGuard
healthcare application using Wagtail 7.0.2's enhanced features.

Main modules:
- wagtail_optimizations: Wagtail 7.0.2 specific optimizations
"""

from .wagtail_optimizations import (
    PageQueryOptimizer,
    OptimizedImageRenditionCache,
    StreamFieldOptimizer,
    PageTreeCache,
    AdminQueryOptimizer,
    SearchQueryOptimizer,
    TemplateFragmentCache,
    DatabaseQueryPrefetcher,
    SitemapOptimizer,
    AsyncViewOptimizer,
    PerformanceMonitor
)

__version__ = '1.0.0'
__author__ = 'MedGuard SA Development Team'

__all__ = [
    'PageQueryOptimizer',
    'OptimizedImageRenditionCache',
    'StreamFieldOptimizer',
    'PageTreeCache',
    'AdminQueryOptimizer',
    'SearchQueryOptimizer',
    'TemplateFragmentCache',
    'DatabaseQueryPrefetcher',
    'SitemapOptimizer',
    'AsyncViewOptimizer',
    'PerformanceMonitor'
] 