"""
Django Signals for Drug Interactions Plugin
Signal handlers for interaction and allergy events.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import DrugInteraction, InteractionCheck, DrugAllergy

logger = logging.getLogger(__name__)


@receiver(post_save, sender=DrugInteraction)
def handle_interaction_created(sender, instance, created, **kwargs):
    """Handle drug interaction creation."""
    if created:
        logger.info(f"New drug interaction created: {instance.drug_name_1} + {instance.drug_name_2}")


@receiver(post_save, sender=InteractionCheck)
def handle_interaction_check_completed(sender, instance, created, **kwargs):
    """Handle completed interaction checks."""
    if created and (instance.major_interactions > 0 or instance.contraindicated_interactions > 0):
        logger.warning(f"Critical interactions found in check {instance.id}")


@receiver(post_save, sender=DrugAllergy)
def handle_allergy_added(sender, instance, created, **kwargs):
    """Handle drug allergy creation."""
    if created:
        logger.info(f"Drug allergy added: {instance.drug_name} for patient {instance.patient.id}")


@receiver(pre_save, sender=DrugAllergy)
def validate_allergy_before_save(sender, instance, **kwargs):
    """Validate drug allergy before saving."""
    if instance.severity in ['severe', 'life_threatening']:
        logger.warning(f"Severe allergy being recorded: {instance.drug_name} for patient {instance.patient.id}")
