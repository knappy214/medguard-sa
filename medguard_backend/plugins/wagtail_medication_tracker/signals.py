"""
Django Signals for Medication Tracker Plugin
Signal handlers for medication tracking events and notifications.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .models import MedicationSchedule, MedicationLog, MedicationLogStatus
from .tasks import (
    generate_scheduled_doses_task,
    send_adherence_alert_task,
    update_adherence_metrics_task
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MedicationSchedule)
def handle_medication_schedule_created(sender, instance, created, **kwargs):
    """Handle medication schedule creation and updates."""
    if created:
        logger.info(f"New medication schedule created: {instance.id}")
        
        # Generate initial scheduled doses asynchronously
        generate_scheduled_doses_task.delay(str(instance.id))
        
        # Send notification to patient
        from medguard_backend.medguard_notifications.services import NotificationService
        
        notification_service = NotificationService()
        notification_service.send_notification(
            user=instance.patient,
            title="New Medication Schedule",
            message=f"A new medication schedule has been created for {instance.medication_name}. Please review your medication times.",
            notification_type="medication_schedule_created",
            metadata={
                'schedule_id': str(instance.id),
                'medication_name': instance.medication_name,
                'frequency': instance.frequency
            }
        )
        
        # Notify healthcare provider if different from patient
        if instance.prescribed_by and instance.prescribed_by != instance.patient:
            notification_service.send_notification(
                user=instance.prescribed_by,
                title="Medication Schedule Created",
                message=f"Medication schedule created for {instance.patient.get_full_name()}: {instance.medication_name}",
                notification_type="medication_prescribed",
                metadata={
                    'schedule_id': str(instance.id),
                    'patient_id': instance.patient.id,
                    'medication_name': instance.medication_name
                }
            )
    
    else:
        logger.info(f"Medication schedule updated: {instance.id}")
        
        # If schedule was deactivated, handle cleanup
        if not instance.is_active:
            # Cancel future scheduled doses
            future_logs = MedicationLog.objects.filter(
                schedule=instance,
                scheduled_time__gt=timezone.now(),
                status=MedicationLogStatus.MISSED
            )
            
            future_logs.delete()
            logger.info(f"Cancelled {future_logs.count()} future doses for deactivated schedule {instance.id}")


@receiver(post_save, sender=MedicationLog)
def handle_medication_log_updated(sender, instance, created, **kwargs):
    """Handle medication log creation and updates."""
    if created:
        logger.info(f"New medication log created: {instance.id}")
    else:
        logger.info(f"Medication log updated: {instance.id} - Status: {instance.status}")
        
        # If medication was taken or missed, update adherence metrics
        if instance.status in [MedicationLogStatus.TAKEN, MedicationLogStatus.MISSED]:
            update_adherence_metrics_task.delay(str(instance.schedule.id))
            
            # Check for adherence alerts
            if instance.status == MedicationLogStatus.MISSED:
                _check_adherence_alerts(instance)


@receiver(pre_save, sender=MedicationLog)
def handle_medication_log_pre_save(sender, instance, **kwargs):
    """Handle medication log before saving."""
    # Set taken_at if status is TAKEN but taken_at is not set
    if instance.status == MedicationLogStatus.TAKEN and not instance.taken_at:
        instance.taken_at = timezone.now()
    
    # Log side effects for monitoring
    if instance.side_effects:
        logger.warning(f"Side effects reported for medication log {instance.id}: {instance.side_effects}")
        
        # Send alert to healthcare provider
        if instance.schedule.prescribed_by:
            from medguard_backend.medguard_notifications.services import NotificationService
            
            notification_service = NotificationService()
            notification_service.send_notification(
                user=instance.schedule.prescribed_by,
                title="Side Effects Reported",
                message=f"Patient {instance.schedule.patient.get_full_name()} reported side effects for {instance.schedule.medication_name}: {instance.side_effects}",
                notification_type="side_effects_reported",
                metadata={
                    'log_id': str(instance.id),
                    'patient_id': instance.schedule.patient.id,
                    'medication_name': instance.schedule.medication_name,
                    'side_effects': instance.side_effects
                }
            )


def _check_adherence_alerts(medication_log):
    """Check if adherence alerts should be sent."""
    schedule = medication_log.schedule
    
    # Check recent missed doses
    recent_missed = MedicationLog.objects.filter(
        schedule=schedule,
        status=MedicationLogStatus.MISSED,
        scheduled_time__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Send alert if too many missed doses
    if recent_missed >= 3:
        send_adherence_alert_task.delay(
            str(schedule.id),
            'multiple_missed_doses',
            {
                'missed_count': recent_missed,
                'period_days': 7
            }
        )
    
    # Check overall adherence rate
    if schedule.adherence_rate < 60:
        send_adherence_alert_task.delay(
            str(schedule.id),
            'low_adherence',
            {
                'adherence_rate': schedule.adherence_rate,
                'threshold': 60
            }
        )


@receiver(post_save, sender=MedicationSchedule)
def handle_schedule_adherence_update(sender, instance, **kwargs):
    """Handle adherence rate updates for medication schedules."""
    # Send alerts for low adherence
    if instance.adherence_rate < 80:
        logger.warning(f"Low adherence detected for schedule {instance.id}: {instance.adherence_rate}%")
        
        # Send alert to patient
        from medguard_backend.medguard_notifications.services import NotificationService
        
        notification_service = NotificationService()
        notification_service.send_notification(
            user=instance.patient,
            title="Medication Adherence Alert",
            message=f"Your adherence rate for {instance.medication_name} is {instance.adherence_rate:.1f}%. Please try to take your medication as scheduled.",
            notification_type="low_adherence_alert",
            metadata={
                'schedule_id': str(instance.id),
                'medication_name': instance.medication_name,
                'adherence_rate': instance.adherence_rate
            }
        )
        
        # Send alert to healthcare provider
        if instance.prescribed_by:
            notification_service.send_notification(
                user=instance.prescribed_by,
                title="Patient Low Adherence Alert",
                message=f"Low adherence alert for {instance.patient.get_full_name()}: {instance.medication_name} ({instance.adherence_rate:.1f}%)",
                notification_type="patient_low_adherence",
                metadata={
                    'schedule_id': str(instance.id),
                    'patient_id': instance.patient.id,
                    'medication_name': instance.medication_name,
                    'adherence_rate': instance.adherence_rate
                }
            )


# Custom signal for medication reminders
from django.dispatch import Signal

medication_reminder_due = Signal()
medication_overdue = Signal()
adherence_threshold_crossed = Signal()


@receiver(medication_reminder_due)
def handle_medication_reminder_due(sender, medication_log, **kwargs):
    """Handle medication reminder notifications."""
    logger.info(f"Medication reminder due for log {medication_log.id}")
    
    # Send push notification to patient
    from medguard_backend.medguard_notifications.services import NotificationService
    
    notification_service = NotificationService()
    notification_service.send_push_notification(
        user=medication_log.schedule.patient,
        title="Medication Reminder",
        message=f"Time to take your {medication_log.schedule.medication_name} ({medication_log.schedule.dosage})",
        data={
            'type': 'medication_reminder',
            'log_id': str(medication_log.id),
            'medication_name': medication_log.schedule.medication_name,
            'dosage': medication_log.schedule.dosage,
            'scheduled_time': medication_log.scheduled_time.isoformat()
        }
    )


@receiver(medication_overdue)
def handle_medication_overdue(sender, medication_log, **kwargs):
    """Handle overdue medication notifications."""
    logger.warning(f"Medication overdue for log {medication_log.id}")
    
    # Send escalated notification
    from medguard_backend.medguard_notifications.services import NotificationService
    
    notification_service = NotificationService()
    
    # Notify patient
    notification_service.send_push_notification(
        user=medication_log.schedule.patient,
        title="Overdue Medication",
        message=f"You have missed your {medication_log.schedule.medication_name}. Please take it as soon as possible.",
        data={
            'type': 'medication_overdue',
            'log_id': str(medication_log.id),
            'medication_name': medication_log.schedule.medication_name,
            'scheduled_time': medication_log.scheduled_time.isoformat()
        }
    )
    
    # Notify healthcare provider if configured
    if medication_log.schedule.prescribed_by:
        notification_service.send_notification(
            user=medication_log.schedule.prescribed_by,
            title="Patient Medication Overdue",
            message=f"{medication_log.schedule.patient.get_full_name()} has missed their {medication_log.schedule.medication_name}",
            notification_type="patient_medication_overdue",
            metadata={
                'log_id': str(medication_log.id),
                'patient_id': medication_log.schedule.patient.id,
                'medication_name': medication_log.schedule.medication_name,
                'scheduled_time': medication_log.scheduled_time.isoformat()
            }
        )


@receiver(adherence_threshold_crossed)
def handle_adherence_threshold_crossed(sender, schedule, old_status, new_status, **kwargs):
    """Handle adherence status changes."""
    logger.info(f"Adherence status changed for schedule {schedule.id}: {old_status} -> {new_status}")
    
    from medguard_backend.medguard_notifications.services import NotificationService
    
    notification_service = NotificationService()
    
    # Send notification based on status change
    if new_status in ['poor', 'very_poor'] and old_status not in ['poor', 'very_poor']:
        # Adherence dropped to concerning level
        notification_service.send_notification(
            user=schedule.patient,
            title="Adherence Alert",
            message=f"Your medication adherence for {schedule.medication_name} has dropped to {new_status.replace('_', ' ')}. Please consult with your healthcare provider.",
            notification_type="adherence_declined",
            metadata={
                'schedule_id': str(schedule.id),
                'medication_name': schedule.medication_name,
                'old_status': old_status,
                'new_status': new_status
            }
        )
        
        # Alert healthcare provider
        if schedule.prescribed_by:
            notification_service.send_notification(
                user=schedule.prescribed_by,
                title="Patient Adherence Declined",
                message=f"Adherence for {schedule.patient.get_full_name()}'s {schedule.medication_name} has declined to {new_status.replace('_', ' ')}",
                notification_type="patient_adherence_declined",
                metadata={
                    'schedule_id': str(schedule.id),
                    'patient_id': schedule.patient.id,
                    'medication_name': schedule.medication_name,
                    'new_status': new_status
                }
            )
    
    elif new_status in ['excellent', 'good'] and old_status in ['poor', 'very_poor']:
        # Adherence improved significantly
        notification_service.send_notification(
            user=schedule.patient,
            title="Great Progress!",
            message=f"Your medication adherence for {schedule.medication_name} has improved to {new_status}. Keep up the good work!",
            notification_type="adherence_improved",
            metadata={
                'schedule_id': str(schedule.id),
                'medication_name': schedule.medication_name,
                'old_status': old_status,
                'new_status': new_status
            }
        )
