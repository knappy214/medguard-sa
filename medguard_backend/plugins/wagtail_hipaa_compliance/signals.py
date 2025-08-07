"""
Django Signals for HIPAA Compliance Plugin
Signal handlers for compliance monitoring and audit logging.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import PHIAccessLog, BreachIncident

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PHIAccessLog)
def handle_phi_access_logged(sender, instance, created, **kwargs):
    """Handle PHI access logging for compliance monitoring."""
    if created:
        logger.info(f"PHI access logged: {instance.user.get_full_name()} accessed {instance.patient.get_full_name()}'s {instance.resource_type}")
        
        # Check for potential unauthorized access patterns
        if not instance.is_authorized:
            logger.warning(f"Unauthorized PHI access detected: {instance.id}")


@receiver(post_save, sender=BreachIncident)
def handle_breach_incident_created(sender, instance, created, **kwargs):
    """Handle breach incident creation and notifications."""
    if created:
        logger.critical(f"Breach incident reported: {instance.incident_title} (Severity: {instance.severity})")
        
        # Trigger immediate notifications for critical incidents
        if instance.severity == 'critical':
            from .tasks import send_critical_breach_alert
            send_critical_breach_alert.delay(str(instance.id))
