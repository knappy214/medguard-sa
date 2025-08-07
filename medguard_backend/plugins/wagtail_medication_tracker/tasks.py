"""
Celery Tasks for Medication Tracker Plugin
Background tasks for medication tracking, reminders, and analytics.
"""
import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q

from .models import MedicationSchedule, MedicationLog, MedicationLogStatus, AdherenceReport
from .services import MedicationTrackerService
from .signals import medication_reminder_due, medication_overdue, adherence_threshold_crossed

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def generate_scheduled_doses_task(self, schedule_id, days_ahead=30):
    """
    Generate scheduled medication doses for a medication schedule.
    
    Args:
        schedule_id: ID of the MedicationSchedule
        days_ahead: Number of days to generate doses for
    """
    try:
        schedule = MedicationSchedule.objects.get(id=schedule_id)
        logger.info(f"Generating scheduled doses for schedule {schedule_id}")
        
        tracker_service = MedicationTrackerService()
        created_logs = tracker_service.generate_scheduled_doses(schedule, days_ahead)
        
        logger.info(f"Generated {len(created_logs)} scheduled doses for schedule {schedule_id}")
        
        return {
            'success': True,
            'schedule_id': schedule_id,
            'created_count': len(created_logs)
        }
        
    except MedicationSchedule.DoesNotExist:
        logger.error(f"Medication schedule {schedule_id} not found")
        return {'success': False, 'error': 'Schedule not found'}
    
    except Exception as exc:
        logger.error(f"Failed to generate scheduled doses: {exc}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying dose generation for schedule {schedule_id}")
            raise self.retry(countdown=60, exc=exc)
        
        return {'success': False, 'error': str(exc)}


@shared_task
def send_medication_reminders():
    """
    Send medication reminders for upcoming doses.
    Runs every 15 minutes to check for due reminders.
    """
    try:
        now = timezone.now()
        reminder_window_start = now
        reminder_window_end = now + timedelta(minutes=15)
        
        logger.info("Checking for medication reminders...")
        
        # Get active schedules with reminders enabled
        active_schedules = MedicationSchedule.objects.filter(
            is_active=True,
            reminder_enabled=True
        )
        
        reminder_count = 0
        
        for schedule in active_schedules:
            # Calculate reminder times for upcoming doses
            upcoming_logs = MedicationLog.objects.filter(
                schedule=schedule,
                status=MedicationLogStatus.MISSED,  # Not yet taken
                scheduled_time__gte=now,
                scheduled_time__lte=now + timedelta(hours=24)
            )
            
            for log in upcoming_logs:
                reminder_time = log.scheduled_time - timedelta(
                    minutes=schedule.reminder_offset_minutes
                )
                
                # Check if reminder is due within the current window
                if reminder_window_start <= reminder_time <= reminder_window_end:
                    # Send reminder signal
                    medication_reminder_due.send(
                        sender=send_medication_reminders,
                        medication_log=log
                    )
                    reminder_count += 1
                    
                    logger.info(f"Sent reminder for log {log.id}")
        
        logger.info(f"Sent {reminder_count} medication reminders")
        
        return {
            'success': True,
            'reminders_sent': reminder_count
        }
        
    except Exception as e:
        logger.error(f"Failed to send medication reminders: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def check_overdue_medications():
    """
    Check for overdue medications and send alerts.
    Runs every hour to check for missed doses.
    """
    try:
        now = timezone.now()
        overdue_threshold = now - timedelta(hours=2)  # 2 hours overdue
        
        logger.info("Checking for overdue medications...")
        
        # Find overdue medication logs
        overdue_logs = MedicationLog.objects.filter(
            status=MedicationLogStatus.MISSED,
            scheduled_time__lt=overdue_threshold,
            scheduled_time__gte=now - timedelta(days=1)  # Only check last 24 hours
        ).select_related('schedule', 'schedule__patient')
        
        overdue_count = 0
        
        for log in overdue_logs:
            # Send overdue signal
            medication_overdue.send(
                sender=check_overdue_medications,
                medication_log=log
            )
            overdue_count += 1
            
            logger.warning(f"Medication overdue for log {log.id}")
        
        logger.info(f"Found {overdue_count} overdue medications")
        
        return {
            'success': True,
            'overdue_count': overdue_count
        }
        
    except Exception as e:
        logger.error(f"Failed to check overdue medications: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True, max_retries=3)
def update_adherence_metrics_task(self, schedule_id):
    """
    Update adherence metrics for a medication schedule.
    
    Args:
        schedule_id: ID of the MedicationSchedule
    """
    try:
        schedule = MedicationSchedule.objects.get(id=schedule_id)
        old_status = schedule.adherence_status
        
        logger.info(f"Updating adherence metrics for schedule {schedule_id}")
        
        # Calculate new adherence rate
        new_rate = schedule.calculate_adherence_rate()
        new_status = schedule.adherence_status
        
        # Check if status changed significantly
        if old_status != new_status:
            adherence_threshold_crossed.send(
                sender=update_adherence_metrics_task,
                schedule=schedule,
                old_status=old_status,
                new_status=new_status
            )
        
        logger.info(f"Updated adherence for schedule {schedule_id}: {new_rate:.1f}% ({new_status})")
        
        return {
            'success': True,
            'schedule_id': schedule_id,
            'adherence_rate': new_rate,
            'status': new_status
        }
        
    except MedicationSchedule.DoesNotExist:
        logger.error(f"Medication schedule {schedule_id} not found")
        return {'success': False, 'error': 'Schedule not found'}
    
    except Exception as exc:
        logger.error(f"Failed to update adherence metrics: {exc}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying adherence update for schedule {schedule_id}")
            raise self.retry(countdown=60, exc=exc)
        
        return {'success': False, 'error': str(exc)}


@shared_task(bind=True, max_retries=3)
def send_adherence_alert_task(self, schedule_id, alert_type, metadata=None):
    """
    Send adherence alert for a medication schedule.
    
    Args:
        schedule_id: ID of the MedicationSchedule
        alert_type: Type of alert ('low_adherence', 'multiple_missed_doses', etc.)
        metadata: Additional alert metadata
    """
    try:
        schedule = MedicationSchedule.objects.get(id=schedule_id)
        metadata = metadata or {}
        
        logger.info(f"Sending adherence alert for schedule {schedule_id}: {alert_type}")
        
        from medguard_backend.medguard_notifications.services import NotificationService
        
        notification_service = NotificationService()
        
        # Customize alert based on type
        if alert_type == 'low_adherence':
            title = "Low Medication Adherence"
            message = f"Your adherence rate for {schedule.medication_name} is {schedule.adherence_rate:.1f}%. Please consult with your healthcare provider."
        
        elif alert_type == 'multiple_missed_doses':
            missed_count = metadata.get('missed_count', 0)
            period_days = metadata.get('period_days', 7)
            title = "Multiple Missed Doses"
            message = f"You have missed {missed_count} doses of {schedule.medication_name} in the last {period_days} days."
        
        else:
            title = "Medication Adherence Alert"
            message = f"There is an issue with your medication adherence for {schedule.medication_name}."
        
        # Send notification to patient
        notification_service.send_notification(
            user=schedule.patient,
            title=title,
            message=message,
            notification_type=f"adherence_alert_{alert_type}",
            metadata={
                'schedule_id': schedule_id,
                'medication_name': schedule.medication_name,
                'alert_type': alert_type,
                **metadata
            }
        )
        
        # Send notification to healthcare provider if applicable
        if schedule.prescribed_by:
            provider_message = f"Adherence alert for {schedule.patient.get_full_name()}: {message}"
            
            notification_service.send_notification(
                user=schedule.prescribed_by,
                title=f"Patient {title}",
                message=provider_message,
                notification_type=f"patient_adherence_alert_{alert_type}",
                metadata={
                    'schedule_id': schedule_id,
                    'patient_id': schedule.patient.id,
                    'medication_name': schedule.medication_name,
                    'alert_type': alert_type,
                    **metadata
                }
            )
        
        logger.info(f"Sent adherence alert for schedule {schedule_id}")
        
        return {
            'success': True,
            'schedule_id': schedule_id,
            'alert_type': alert_type
        }
        
    except MedicationSchedule.DoesNotExist:
        logger.error(f"Medication schedule {schedule_id} not found")
        return {'success': False, 'error': 'Schedule not found'}
    
    except Exception as exc:
        logger.error(f"Failed to send adherence alert: {exc}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying adherence alert for schedule {schedule_id}")
            raise self.retry(countdown=60, exc=exc)
        
        return {'success': False, 'error': str(exc)}


@shared_task
def generate_daily_adherence_reports():
    """
    Generate daily adherence reports for all active patients.
    Runs daily at midnight.
    """
    try:
        logger.info("Generating daily adherence reports...")
        
        # Get all patients with active medication schedules
        patients_with_schedules = User.objects.filter(
            medication_schedules__is_active=True
        ).distinct()
        
        tracker_service = MedicationTrackerService()
        reports_generated = 0
        
        for patient in patients_with_schedules:
            try:
                # Generate 7-day adherence report
                report = tracker_service.generate_adherence_report(
                    patient_id=patient.id,
                    period_days=7,
                    generated_by_id=None  # System generated
                )
                
                reports_generated += 1
                logger.info(f"Generated adherence report for patient {patient.id}")
                
            except Exception as e:
                logger.error(f"Failed to generate report for patient {patient.id}: {e}")
                continue
        
        logger.info(f"Generated {reports_generated} daily adherence reports")
        
        return {
            'success': True,
            'reports_generated': reports_generated
        }
        
    except Exception as e:
        logger.error(f"Failed to generate daily adherence reports: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def cleanup_old_medication_logs(days_old=365):
    """
    Clean up old medication logs for data retention compliance.
    
    Args:
        days_old: Number of days after which to archive/delete logs
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        logger.info(f"Cleaning up medication logs older than {days_old} days...")
        
        # Find old logs
        old_logs = MedicationLog.objects.filter(
            scheduled_time__lt=cutoff_date
        )
        
        count = old_logs.count()
        
        # Archive or delete based on retention policy
        for log in old_logs:
            # Log the cleanup action
            logger.info(f"Archiving medication log {log.id} from {log.scheduled_time}")
            
            # Add cleanup metadata
            if not hasattr(log, 'cleanup_metadata'):
                log.cleanup_metadata = {}
            
            log.cleanup_metadata.update({
                'archived_at': timezone.now().isoformat(),
                'reason': f'Automatic cleanup after {days_old} days'
            })
            
            # In a real implementation, you might move to archive storage
            # For now, we'll just mark them
            log.save(update_fields=['cleanup_metadata'] if hasattr(log, 'cleanup_metadata') else [])
        
        logger.info(f"Cleanup completed: processed {count} old medication logs")
        
        return {
            'success': True,
            'processed_count': count
        }
        
    except Exception as e:
        logger.error(f"Medication log cleanup failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def analyze_medication_patterns():
    """
    Analyze medication adherence patterns and generate insights.
    Runs weekly to identify trends and patterns.
    """
    try:
        logger.info("Analyzing medication adherence patterns...")
        
        # Get active schedules
        active_schedules = MedicationSchedule.objects.filter(
            is_active=True
        ).select_related('patient')
        
        insights = {
            'total_schedules': active_schedules.count(),
            'high_adherence_count': 0,
            'low_adherence_count': 0,
            'patterns': []
        }
        
        # Analyze patterns
        for schedule in active_schedules:
            if schedule.adherence_rate >= 90:
                insights['high_adherence_count'] += 1
            elif schedule.adherence_rate < 70:
                insights['low_adherence_count'] += 1
                
                # Analyze missed dose patterns
                recent_logs = MedicationLog.objects.filter(
                    schedule=schedule,
                    scheduled_time__gte=timezone.now() - timedelta(days=30)
                ).order_by('scheduled_time')
                
                # Check for patterns (e.g., consistently missing morning doses)
                missed_by_time = {}
                for log in recent_logs:
                    if log.status == MedicationLogStatus.MISSED:
                        hour = log.scheduled_time.hour
                        missed_by_time[hour] = missed_by_time.get(hour, 0) + 1
                
                if missed_by_time:
                    most_missed_hour = max(missed_by_time, key=missed_by_time.get)
                    insights['patterns'].append({
                        'patient_id': schedule.patient.id,
                        'medication': schedule.medication_name,
                        'pattern': f'Most missed doses at {most_missed_hour}:00',
                        'frequency': missed_by_time[most_missed_hour]
                    })
        
        # Calculate overall system metrics
        if insights['total_schedules'] > 0:
            insights['high_adherence_percentage'] = (
                insights['high_adherence_count'] / insights['total_schedules'] * 100
            )
            insights['low_adherence_percentage'] = (
                insights['low_adherence_count'] / insights['total_schedules'] * 100
            )
        
        logger.info(f"Pattern analysis completed: {len(insights['patterns'])} patterns identified")
        
        return {
            'success': True,
            'insights': insights
        }
        
    except Exception as e:
        logger.error(f"Pattern analysis failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def sync_medication_schedules_with_external_systems():
    """
    Sync medication schedules with external healthcare systems.
    Placeholder for integration with EHR systems, pharmacy systems, etc.
    """
    try:
        logger.info("Syncing medication schedules with external systems...")
        
        # Get schedules that need syncing
        schedules_to_sync = MedicationSchedule.objects.filter(
            is_active=True,
            # Add criteria for schedules that need external sync
        )
        
        sync_count = 0
        
        for schedule in schedules_to_sync:
            try:
                # Placeholder for external system integration
                # This would typically involve API calls to:
                # - Electronic Health Records (EHR)
                # - Pharmacy management systems
                # - Insurance systems
                # - Clinical decision support systems
                
                logger.info(f"Synced schedule {schedule.id} with external systems")
                sync_count += 1
                
            except Exception as e:
                logger.error(f"Failed to sync schedule {schedule.id}: {e}")
                continue
        
        logger.info(f"Synced {sync_count} medication schedules")
        
        return {
            'success': True,
            'synced_count': sync_count
        }
        
    except Exception as e:
        logger.error(f"External system sync failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }
