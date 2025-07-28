"""
Settings package for MedGuard SA backend.

This package contains settings for different environments:
- base.py: Common settings shared across all environments
- development.py: Development-specific settings
- production.py: Production-specific settings
- local.py: Local development overrides (not in version control)
"""

from .base import * 