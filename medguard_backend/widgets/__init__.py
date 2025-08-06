"""
Wagtail 7.0.2 Widgets for MedGuard SA.

This package contains modern interactive widgets for the MedGuard SA medication management system.
All widgets use Wagtail 7.0.2's enhanced JavaScript integration and accessibility features.
"""

from .wagtail_widgets import (
    MedicationDosageCalculatorWidget,
    PrescriptionOCRWidget,
    MedicationInteractionCheckerWidget,
    StockLevelIndicatorWidget,
    MedicationScheduleWidget,
    PharmacyLocatorWidget,
    PrescriptionHistoryTimelineWidget,
    MedicationAdherenceTrackerWidget,
    NotificationPreferenceWidget,
)

__all__ = [
    'MedicationDosageCalculatorWidget',
    'PrescriptionOCRWidget',
    'MedicationInteractionCheckerWidget',
    'StockLevelIndicatorWidget',
    'MedicationScheduleWidget',
    'PharmacyLocatorWidget',
    'PrescriptionHistoryTimelineWidget',
    'MedicationAdherenceTrackerWidget',
    'NotificationPreferenceWidget',
] 