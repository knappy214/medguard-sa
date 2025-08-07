"""
Django Signals for Pharmacy Locator Plugin
Signal handlers for pharmacy and inventory events.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Pharmacy, MedicationInventory, PharmacyReview
from .tasks import (
    update_pharmacy_ratings_task,
    sync_inventory_with_external_system_task,
    send_low_stock_alert_task
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Pharmacy)
def handle_pharmacy_created_or_updated(sender, instance, created, **kwargs):
    """Handle pharmacy creation and updates."""
    if created:
        logger.info(f"New pharmacy created: {instance.name} in {instance.city}")
        
        # Send welcome notification to pharmacy
        from medguard_backend.medguard_notifications.services import NotificationService
        
        notification_service = NotificationService()
        
        # If there's a verified_by user, notify them
        if instance.verified_by:
            notification_service.send_notification(
                user=instance.verified_by,
                title="Pharmacy Added Successfully",
                message=f"Pharmacy '{instance.name}' has been added to the system and is now available for patients.",
                notification_type="pharmacy_added",
                metadata={
                    'pharmacy_id': str(instance.id),
                    'pharmacy_name': instance.name,
                    'city': instance.city
                }
            )
        
        # Initialize default inventory if needed
        # This could trigger a task to sync with external pharmacy systems
        if instance.api_endpoint:
            sync_inventory_with_external_system_task.delay(str(instance.id))
    
    else:
        logger.info(f"Pharmacy updated: {instance.name}")
        
        # If status changed to inactive, handle cleanup
        if instance.status != 'active':
            logger.info(f"Pharmacy {instance.name} status changed to {instance.status}")
            
            # Could trigger notifications to patients with medications at this pharmacy
            from .tasks import notify_patients_pharmacy_status_change_task
            notify_patients_pharmacy_status_change_task.delay(str(instance.id), instance.status)


@receiver(post_save, sender=MedicationInventory)
def handle_inventory_updated(sender, instance, created, **kwargs):
    """Handle medication inventory updates."""
    if created:
        logger.info(f"New inventory item created: {instance.medication_name} at {instance.pharmacy.name}")
    else:
        logger.info(f"Inventory updated: {instance.medication_name} at {instance.pharmacy.name}")
        
        # Check for low stock
        if instance.is_low_stock and instance.status == 'in_stock':
            logger.warning(f"Low stock alert: {instance.medication_name} at {instance.pharmacy.name}")
            send_low_stock_alert_task.delay(str(instance.id))
        
        # Check for out of stock
        if instance.quantity_available == 0 and instance.status == 'in_stock':
            logger.warning(f"Out of stock: {instance.medication_name} at {instance.pharmacy.name}")
            instance.status = 'out_of_stock'
            instance.save(update_fields=['status'])
    
    # Sync with external system if enabled
    if instance.sync_enabled and instance.pharmacy.api_endpoint:
        sync_inventory_with_external_system_task.delay(
            str(instance.pharmacy.id),
            inventory_items=[str(instance.id)]
        )


@receiver(pre_save, sender=MedicationInventory)
def handle_inventory_pre_save(sender, instance, **kwargs):
    """Handle inventory before saving."""
    # Auto-update status based on quantity
    if instance.quantity_available == 0:
        instance.status = 'out_of_stock'
    elif instance.is_low_stock:
        instance.status = 'low_stock'
    elif instance.quantity_available > 0 and instance.status in ['out_of_stock', 'low_stock']:
        instance.status = 'in_stock'
    
    # Check expiry date
    if instance.expiry_date and instance.is_expired:
        logger.warning(f"Expired medication detected: {instance.medication_name} at {instance.pharmacy.name}")
        # Could trigger automatic status change or alert


@receiver(post_save, sender=PharmacyReview)
def handle_pharmacy_review_created(sender, instance, created, **kwargs):
    """Handle new pharmacy reviews."""
    if created:
        logger.info(f"New review created for {instance.pharmacy.name}: {instance.rating}/5")
        
        # Update pharmacy ratings asynchronously
        update_pharmacy_ratings_task.delay(str(instance.pharmacy.id))
        
        # Send notification for low ratings
        if instance.rating <= 2:
            logger.warning(f"Low rating received for {instance.pharmacy.name}: {instance.rating}/5")
            
            from medguard_backend.medguard_notifications.services import NotificationService
            
            notification_service = NotificationService()
            
            # Notify pharmacy managers (if we have that relationship)
            # For now, we'll notify the user who verified the pharmacy
            if instance.pharmacy.verified_by:
                notification_service.send_notification(
                    user=instance.pharmacy.verified_by,
                    title="Low Rating Alert",
                    message=f"Pharmacy '{instance.pharmacy.name}' received a {instance.rating}-star review. Please review and address any concerns.",
                    notification_type="pharmacy_low_rating",
                    metadata={
                        'pharmacy_id': str(instance.pharmacy.id),
                        'review_id': str(instance.id),
                        'rating': instance.rating,
                        'reviewer': instance.reviewer.get_full_name()
                    }
                )
        
        # Send thank you notification for high ratings
        elif instance.rating >= 4:
            from medguard_backend.medguard_notifications.services import NotificationService
            
            notification_service = NotificationService()
            notification_service.send_notification(
                user=instance.reviewer,
                title="Thank You for Your Review",
                message=f"Thank you for reviewing {instance.pharmacy.name}. Your feedback helps other patients find quality pharmacy services.",
                notification_type="review_thank_you",
                metadata={
                    'pharmacy_id': str(instance.pharmacy.id),
                    'review_id': str(instance.id),
                    'rating': instance.rating
                }
            )


# Custom signals for pharmacy locator
from django.dispatch import Signal

pharmacy_inventory_low = Signal()
pharmacy_status_changed = Signal()
medication_reserved = Signal()
medication_reservation_expired = Signal()


@receiver(pharmacy_inventory_low)
def handle_pharmacy_inventory_low(sender, inventory_item, **kwargs):
    """Handle low inventory alerts."""
    logger.warning(f"Low inventory signal received for {inventory_item.medication_name}")
    
    from medguard_backend.medguard_notifications.services import NotificationService
    
    notification_service = NotificationService()
    
    # Notify pharmacy staff
    if inventory_item.pharmacy.verified_by:
        notification_service.send_notification(
            user=inventory_item.pharmacy.verified_by,
            title="Low Stock Alert",
            message=f"Low stock alert for {inventory_item.medication_name} at {inventory_item.pharmacy.name}. Current quantity: {inventory_item.quantity_available}",
            notification_type="pharmacy_low_stock",
            metadata={
                'pharmacy_id': str(inventory_item.pharmacy.id),
                'inventory_id': str(inventory_item.id),
                'medication_name': inventory_item.medication_name,
                'current_quantity': inventory_item.quantity_available,
                'reorder_level': inventory_item.reorder_level
            }
        )


@receiver(pharmacy_status_changed)
def handle_pharmacy_status_changed(sender, pharmacy, old_status, new_status, **kwargs):
    """Handle pharmacy status changes."""
    logger.info(f"Pharmacy status changed: {pharmacy.name} from {old_status} to {new_status}")
    
    from medguard_backend.medguard_notifications.services import NotificationService
    
    notification_service = NotificationService()
    
    # Notify relevant users about status changes
    if new_status in ['temporarily_closed', 'permanently_closed']:
        # Find patients who have medications at this pharmacy
        from medguard_backend.plugins.wagtail_medication_tracker.models import MedicationSchedule
        
        affected_patients = MedicationSchedule.objects.filter(
            # This would require a relationship between schedules and pharmacies
            # For now, we'll skip this part
        ).values_list('patient', flat=True).distinct()
        
        for patient_id in affected_patients:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                patient = User.objects.get(id=patient_id)
                
                notification_service.send_notification(
                    user=patient,
                    title="Pharmacy Status Update",
                    message=f"Your pharmacy {pharmacy.name} is now {new_status.replace('_', ' ')}. Please find an alternative pharmacy for your medications.",
                    notification_type="pharmacy_status_change",
                    metadata={
                        'pharmacy_id': str(pharmacy.id),
                        'pharmacy_name': pharmacy.name,
                        'old_status': old_status,
                        'new_status': new_status
                    }
                )
            except User.DoesNotExist:
                continue


@receiver(medication_reserved)
def handle_medication_reserved(sender, reservation_data, **kwargs):
    """Handle medication reservation events."""
    logger.info(f"Medication reserved: {reservation_data['medication_name']} at {reservation_data['pharmacy_name']}")
    
    from medguard_backend.medguard_notifications.services import NotificationService
    
    notification_service = NotificationService()
    
    # Send confirmation to user
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=reservation_data['user_id'])
        
        notification_service.send_notification(
            user=user,
            title="Medication Reserved",
            message=f"Your medication {reservation_data['medication_name']} has been reserved at {reservation_data['pharmacy_name']}. Please pick it up within 24 hours.",
            notification_type="medication_reserved",
            metadata=reservation_data
        )
    except User.DoesNotExist:
        logger.error(f"User {reservation_data['user_id']} not found for medication reservation")


@receiver(medication_reservation_expired)
def handle_medication_reservation_expired(sender, reservation_data, **kwargs):
    """Handle expired medication reservations."""
    logger.info(f"Medication reservation expired: {reservation_data['medication_name']}")
    
    # Release reserved quantity back to available inventory
    try:
        inventory = MedicationInventory.objects.get(id=reservation_data['inventory_id'])
        inventory.quantity_reserved -= reservation_data['quantity_reserved']
        inventory.save(update_fields=['quantity_reserved'])
        
        logger.info(f"Released {reservation_data['quantity_reserved']} units back to inventory")
        
    except MedicationInventory.DoesNotExist:
        logger.error(f"Inventory {reservation_data['inventory_id']} not found for reservation expiry")
    
    # Notify user about expiry
    from medguard_backend.medguard_notifications.services import NotificationService
    
    notification_service = NotificationService()
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=reservation_data['user_id'])
        
        notification_service.send_notification(
            user=user,
            title="Medication Reservation Expired",
            message=f"Your reservation for {reservation_data['medication_name']} at {reservation_data['pharmacy_name']} has expired. Please make a new reservation if still needed.",
            notification_type="reservation_expired",
            metadata=reservation_data
        )
    except User.DoesNotExist:
        logger.error(f"User {reservation_data['user_id']} not found for reservation expiry notification")


# Geographic search optimization signals
@receiver(post_save, sender=Pharmacy)
def update_geographic_indexes(sender, instance, **kwargs):
    """Update geographic search indexes when pharmacy location changes."""
    if instance.location:
        logger.info(f"Updating geographic indexes for pharmacy {instance.name}")
        # This could trigger background tasks to update spatial indexes
        # or cache geographic data for faster searches


# Integration signals
@receiver(post_save, sender=Pharmacy)
def sync_with_external_systems(sender, instance, created, **kwargs):
    """Sync pharmacy data with external systems."""
    if instance.api_endpoint and instance.external_id:
        logger.info(f"Syncing pharmacy {instance.name} with external systems")
        
        # Queue sync task
        from .tasks import sync_pharmacy_with_external_system_task
        sync_pharmacy_with_external_system_task.delay(str(instance.id))


# Analytics and reporting signals
@receiver(post_save, sender=PharmacyReview)
def update_pharmacy_analytics(sender, instance, created, **kwargs):
    """Update pharmacy analytics when reviews are created."""
    if created:
        # Update cached analytics data
        from .tasks import update_pharmacy_analytics_task
        update_pharmacy_analytics_task.delay(str(instance.pharmacy.id))
