# -*- coding: utf-8 -*-
"""
MedGuard SA - Wagtail 7.0.2 Maintenance Module
==============================================

This module provides comprehensive maintenance tools specifically designed for
Wagtail 7.0.2 healthcare applications, ensuring optimal performance, security,
and compliance with healthcare regulations.

Author: MedGuard SA Development Team
License: Proprietary
"""

# Lazy imports to avoid Django app loading issues
def get_maintenance_classes():
    """Get all maintenance classes with lazy loading."""
    from .wagtail_maintenance import (
        HealthcareContentAuditor,
        MedicalLinkChecker,
        MedicationImageCleaner,
        HealthcareSearchIndexManager,
        PageTreeOptimizer
    )
    
    from .wagtail_maintenance_extended import (
        HealthcareBackupVerifier,
        HealthcareLogRotator,
        HealthcareCacheWarmer,
        SecurityUpdateChecker,
        HealthcareHealthChecker,
        MaintenanceTaskRunner
    )
    
    return {
        'HealthcareContentAuditor': HealthcareContentAuditor,
        'MedicalLinkChecker': MedicalLinkChecker,
        'MedicationImageCleaner': MedicationImageCleaner,
        'HealthcareSearchIndexManager': HealthcareSearchIndexManager,
        'PageTreeOptimizer': PageTreeOptimizer,
        'HealthcareBackupVerifier': HealthcareBackupVerifier,
        'HealthcareLogRotator': HealthcareLogRotator,
        'HealthcareCacheWarmer': HealthcareCacheWarmer,
        'SecurityUpdateChecker': SecurityUpdateChecker,
        'HealthcareHealthChecker': HealthcareHealthChecker,
        'MaintenanceTaskRunner': MaintenanceTaskRunner,
    }

# Make classes available at module level for backward compatibility
def __getattr__(name):
    """Dynamic attribute access for maintenance classes."""
    classes = get_maintenance_classes()
    if name in classes:
        return classes[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'HealthcareContentAuditor',
    'MedicalLinkChecker',
    'MedicationImageCleaner',
    'HealthcareSearchIndexManager',
    'PageTreeOptimizer',
    'HealthcareBackupVerifier',
    'HealthcareLogRotator',
    'HealthcareCacheWarmer',
    'SecurityUpdateChecker',
    'HealthcareHealthChecker',
    'MaintenanceTaskRunner',
    'get_maintenance_classes',
]

__version__ = '1.0.0'
