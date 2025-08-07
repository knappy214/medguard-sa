"""
Medication Tracker Services
Core services for medication adherence tracking and analytics.
"""
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import (
    MedicationSchedule, 
    MedicationLog, 
    AdherenceReport,
    MedicationLogStatus,
    AdherenceStatus
)

logger = logging.getLogger(__name__)
User = get_user_model()


class MedicationTrackerService:
    """Service for tracking medication adherence and generating insights."""
    
    def __init__(self):
        """Initialize the medication tracker service."""
        self.default_reminder_offset = getattr(
            settings, 
            'MEDICATION_REMINDER_OFFSET_MINUTES', 
            15
        )
    
    def create_medication_schedule(
        self, 
        patient_id: int, 
        medication_data: Dict,
        prescribed_by_id: Optional[int] = None
    ) -> MedicationSchedule:
        """
        Create a new medication schedule.
        
        Args:
            patient_id: ID of the patient
            medication_data: Dictionary containing medication details
            prescribed_by_id: Optional ID of prescribing healthcare provider
            
        Returns:
            Created MedicationSchedule instance
        """
        try:
            patient = User.objects.get(id=patient_id)
            prescribed_by = None
            
            if prescribed_by_id:
                prescribed_by = User.objects.get(id=prescribed_by_id)
            
            schedule = MedicationSchedule.objects.create(
                patient=patient,
                prescribed_by=prescribed_by,
                medication_name=medication_data['medication_name'],
                dosage=medication_data['dosage'],
                frequency=medication_data['frequency'],
                start_date=medication_data['start_date'],
                end_date=medication_data.get('end_date'),
                scheduled_times=medication_data.get('scheduled_times', []),
                reminder_enabled=medication_data.get('reminder_enabled', True),
                reminder_offset_minutes=medication_data.get(
                    'reminder_offset_minutes', 
                    self.default_reminder_offset
                ),
                notes=medication_data.get('notes', '')
            )
            
            # Generate initial scheduled doses
            self.generate_scheduled_doses(schedule)
            
            logger.info(f"Created medication schedule {schedule.id} for patient {patient_id}")
            return schedule
            
        except User.DoesNotExist:
            logger.error(f"Patient {patient_id} not found")
            raise ValueError(_("Patient not found"))
        
        except Exception as e:
            logger.error(f"Failed to create medication schedule: {e}")
            raise
    
    def generate_scheduled_doses(
        self, 
        schedule: MedicationSchedule,
        days_ahead: int = 30
    ) -> List[MedicationLog]:
        """
        Generate scheduled medication doses for the next N days.
        
        Args:
            schedule: MedicationSchedule instance
            days_ahead: Number of days to generate doses for
            
        Returns:
            List of created MedicationLog instances
        """
        if not schedule.scheduled_times or not schedule.is_active:
            return []
        
        created_logs = []
        current_date = max(timezone.now().date(), schedule.start_date)
        end_date = current_date + timedelta(days=days_ahead)
        
        # Don't generate beyond medication end date
        if schedule.end_date:
            end_date = min(end_date, schedule.end_date)
        
        # Generate logs for each day and time
        while current_date <= end_date:
            for time_str in schedule.scheduled_times:
                try:
                    # Parse time string (HH:MM format)
                    hour, minute = map(int, time_str.split(':'))
                    scheduled_datetime = timezone.make_aware(
                        datetime.combine(current_date, time(hour, minute))
                    )
                    
                    # Check if log already exists
                    if not MedicationLog.objects.filter(
                        schedule=schedule,
                        scheduled_time=scheduled_datetime
                    ).exists():
                        
                        log = MedicationLog.objects.create(
                            schedule=schedule,
                            scheduled_time=scheduled_datetime,
                            status=MedicationLogStatus.MISSED  # Default to missed, update when taken
                        )
                        created_logs.append(log)
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Invalid time format '{time_str}' in schedule {schedule.id}: {e}")
                    continue
            
            current_date += timedelta(days=1)
        
        logger.info(f"Generated {len(created_logs)} scheduled doses for schedule {schedule.id}")
        return created_logs
    
    def log_medication_taken(
        self, 
        log_id: str,
        taken_at: Optional[datetime] = None,
        dose_taken: Optional[str] = None,
        side_effects: Optional[str] = None,
        notes: Optional[str] = None,
        logged_by_id: Optional[int] = None,
        device_id: Optional[str] = None,
        location_data: Optional[Dict] = None
    ) -> MedicationLog:
        """
        Log that a medication dose was taken.
        
        Args:
            log_id: ID of the MedicationLog
            taken_at: When the medication was taken (defaults to now)
            dose_taken: Actual dose taken if different from scheduled
            side_effects: Any side effects experienced
            notes: Additional notes
            logged_by_id: ID of user logging the medication
            device_id: Device identifier for mobile logging
            location_data: GPS coordinates if available
            
        Returns:
            Updated MedicationLog instance
        """
        try:
            log = MedicationLog.objects.get(id=log_id)
            
            if taken_at is None:
                taken_at = timezone.now()
            
            # Determine status based on timing
            status = MedicationLogStatus.TAKEN
            if taken_at > log.scheduled_time + timedelta(hours=2):
                status = MedicationLogStatus.DELAYED
            
            # Update log
            log.taken_at = taken_at
            log.status = status
            log.dose_taken = dose_taken or ''
            log.side_effects = side_effects or ''
            log.notes = notes or ''
            log.device_id = device_id or ''
            log.location_data = location_data or {}
            
            if logged_by_id:
                log.logged_by = User.objects.get(id=logged_by_id)
            
            log.save()
            
            # Update schedule adherence rate
            self.update_schedule_adherence(log.schedule)
            
            logger.info(f"Logged medication taken for log {log_id}")
            return log
            
        except MedicationLog.DoesNotExist:
            logger.error(f"Medication log {log_id} not found")
            raise ValueError(_("Medication log not found"))
        
        except Exception as e:
            logger.error(f"Failed to log medication taken: {e}")
            raise
    
    def mark_medication_missed(
        self, 
        log_id: str,
        reason: Optional[str] = None,
        logged_by_id: Optional[int] = None
    ) -> MedicationLog:
        """
        Mark a medication dose as missed.
        
        Args:
            log_id: ID of the MedicationLog
            reason: Reason for missing the dose
            logged_by_id: ID of user logging the miss
            
        Returns:
            Updated MedicationLog instance
        """
        try:
            log = MedicationLog.objects.get(id=log_id)
            
            log.status = MedicationLogStatus.MISSED
            log.notes = reason or ''
            
            if logged_by_id:
                log.logged_by = User.objects.get(id=logged_by_id)
            
            log.save()
            
            # Update schedule adherence rate
            self.update_schedule_adherence(log.schedule)
            
            logger.info(f"Marked medication missed for log {log_id}")
            return log
            
        except MedicationLog.DoesNotExist:
            logger.error(f"Medication log {log_id} not found")
            raise ValueError(_("Medication log not found"))
        
        except Exception as e:
            logger.error(f"Failed to mark medication missed: {e}")
            raise
    
    def update_schedule_adherence(self, schedule: MedicationSchedule) -> float:
        """
        Update adherence rate for a medication schedule.
        
        Args:
            schedule: MedicationSchedule instance
            
        Returns:
            Updated adherence rate
        """
        return schedule.calculate_adherence_rate()
    
    def get_patient_adherence_summary(
        self, 
        patient_id: int,
        days: int = 30
    ) -> Dict:
        """
        Get adherence summary for a patient.
        
        Args:
            patient_id: ID of the patient
            days: Number of days to analyze
            
        Returns:
            Dictionary containing adherence summary
        """
        try:
            patient = User.objects.get(id=patient_id)
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Get active schedules
            schedules = MedicationSchedule.objects.filter(
                patient=patient,
                is_active=True
            )
            
            # Calculate overall metrics
            total_scheduled = 0
            total_taken = 0
            total_missed = 0
            
            medication_details = []
            
            for schedule in schedules:
                # Get logs for this period
                logs = MedicationLog.objects.filter(
                    schedule=schedule,
                    scheduled_time__date__range=[start_date, end_date]
                )
                
                scheduled_count = logs.count()
                taken_count = logs.filter(status=MedicationLogStatus.TAKEN).count()
                missed_count = logs.filter(status=MedicationLogStatus.MISSED).count()
                
                adherence_rate = (taken_count / scheduled_count * 100) if scheduled_count > 0 else 0
                
                medication_details.append({
                    'medication_name': schedule.medication_name,
                    'dosage': schedule.dosage,
                    'frequency': schedule.frequency,
                    'scheduled_count': scheduled_count,
                    'taken_count': taken_count,
                    'missed_count': missed_count,
                    'adherence_rate': adherence_rate,
                    'adherence_status': schedule.get_adherence_status(adherence_rate)
                })
                
                total_scheduled += scheduled_count
                total_taken += taken_count
                total_missed += missed_count
            
            overall_adherence = (total_taken / total_scheduled * 100) if total_scheduled > 0 else 0
            
            return {
                'patient_id': patient_id,
                'patient_name': patient.get_full_name(),
                'period_start': start_date,
                'period_end': end_date,
                'overall_adherence_rate': overall_adherence,
                'total_medications': len(medication_details),
                'total_scheduled': total_scheduled,
                'total_taken': total_taken,
                'total_missed': total_missed,
                'medication_details': medication_details
            }
            
        except User.DoesNotExist:
            logger.error(f"Patient {patient_id} not found")
            raise ValueError(_("Patient not found"))
        
        except Exception as e:
            logger.error(f"Failed to get patient adherence summary: {e}")
            raise
    
    def generate_adherence_report(
        self, 
        patient_id: int,
        period_days: int = 30,
        generated_by_id: Optional[int] = None
    ) -> AdherenceReport:
        """
        Generate a comprehensive adherence report.
        
        Args:
            patient_id: ID of the patient
            period_days: Number of days to analyze
            generated_by_id: ID of user generating the report
            
        Returns:
            Created AdherenceReport instance
        """
        try:
            patient = User.objects.get(id=patient_id)
            report_date = timezone.now().date()
            period_end = report_date
            period_start = period_end - timedelta(days=period_days)
            
            # Get adherence summary
            summary = self.get_patient_adherence_summary(patient_id, period_days)
            
            # Generate daily adherence data
            daily_adherence = self._calculate_daily_adherence(patient, period_start, period_end)
            
            # Generate insights and recommendations
            insights = self._generate_adherence_insights(summary, daily_adherence)
            recommendations = self._generate_adherence_recommendations(summary, insights)
            
            # Create report
            report = AdherenceReport.objects.create(
                patient=patient,
                report_date=report_date,
                period_start=period_start,
                period_end=period_end,
                overall_adherence_rate=summary['overall_adherence_rate'],
                total_medications=summary['total_medications'],
                total_scheduled_doses=summary['total_scheduled'],
                total_taken_doses=summary['total_taken'],
                total_missed_doses=summary['total_missed'],
                medication_breakdown={
                    med['medication_name']: {
                        'adherence_rate': med['adherence_rate'],
                        'scheduled': med['scheduled_count'],
                        'taken': med['taken_count'],
                        'missed': med['missed_count']
                    }
                    for med in summary['medication_details']
                },
                daily_adherence=daily_adherence,
                insights=insights,
                recommendations=recommendations,
                generated_by_id=generated_by_id
            )
            
            logger.info(f"Generated adherence report {report.id} for patient {patient_id}")
            return report
            
        except User.DoesNotExist:
            logger.error(f"Patient {patient_id} not found")
            raise ValueError(_("Patient not found"))
        
        except Exception as e:
            logger.error(f"Failed to generate adherence report: {e}")
            raise
    
    def _calculate_daily_adherence(
        self, 
        patient: User, 
        start_date: datetime.date, 
        end_date: datetime.date
    ) -> Dict:
        """Calculate day-by-day adherence data."""
        daily_data = {}
        current_date = start_date
        
        while current_date <= end_date:
            # Get logs for this day
            logs = MedicationLog.objects.filter(
                schedule__patient=patient,
                schedule__is_active=True,
                scheduled_time__date=current_date
            )
            
            scheduled = logs.count()
            taken = logs.filter(status=MedicationLogStatus.TAKEN).count()
            
            adherence_rate = (taken / scheduled * 100) if scheduled > 0 else 0
            
            daily_data[current_date.isoformat()] = {
                'scheduled': scheduled,
                'taken': taken,
                'adherence_rate': adherence_rate
            }
            
            current_date += timedelta(days=1)
        
        return daily_data
    
    def _generate_adherence_insights(
        self, 
        summary: Dict, 
        daily_adherence: Dict
    ) -> List[str]:
        """Generate AI-powered insights about adherence patterns."""
        insights = []
        
        # Overall adherence insight
        overall_rate = summary['overall_adherence_rate']
        if overall_rate >= 90:
            insights.append(_("Excellent medication adherence maintained"))
        elif overall_rate >= 80:
            insights.append(_("Good adherence with room for improvement"))
        elif overall_rate >= 60:
            insights.append(_("Moderate adherence - intervention recommended"))
        else:
            insights.append(_("Poor adherence - urgent intervention needed"))
        
        # Medication-specific insights
        for med in summary['medication_details']:
            if med['adherence_rate'] < 70:
                insights.append(
                    _("Low adherence detected for {medication} ({rate:.1f}%)").format(
                        medication=med['medication_name'],
                        rate=med['adherence_rate']
                    )
                )
        
        # Pattern analysis
        daily_rates = [day['adherence_rate'] for day in daily_adherence.values()]
        if len(daily_rates) > 7:
            recent_avg = sum(daily_rates[-7:]) / 7
            earlier_avg = sum(daily_rates[:-7]) / len(daily_rates[:-7])
            
            if recent_avg > earlier_avg + 10:
                insights.append(_("Improving adherence trend observed"))
            elif recent_avg < earlier_avg - 10:
                insights.append(_("Declining adherence trend detected"))
        
        return insights
    
    def _generate_adherence_recommendations(
        self, 
        summary: Dict, 
        insights: List[str]
    ) -> List[str]:
        """Generate personalized recommendations for improving adherence."""
        recommendations = []
        
        overall_rate = summary['overall_adherence_rate']
        
        if overall_rate < 80:
            recommendations.extend([
                _("Consider setting up medication reminders"),
                _("Use a pill organizer to track daily doses"),
                _("Schedule regular check-ins with healthcare provider")
            ])
        
        if summary['total_missed'] > summary['total_taken'] * 0.2:
            recommendations.extend([
                _("Review medication schedule with healthcare provider"),
                _("Consider simplifying medication regimen if possible")
            ])
        
        # Medication-specific recommendations
        for med in summary['medication_details']:
            if med['adherence_rate'] < 60:
                recommendations.append(
                    _("Focus on improving adherence for {medication}").format(
                        medication=med['medication_name']
                    )
                )
        
        return recommendations
    
    def get_upcoming_medications(
        self, 
        patient_id: int,
        hours_ahead: int = 24
    ) -> List[Dict]:
        """
        Get upcoming medication doses for a patient.
        
        Args:
            patient_id: ID of the patient
            hours_ahead: Number of hours to look ahead
            
        Returns:
            List of upcoming medication doses
        """
        try:
            patient = User.objects.get(id=patient_id)
            now = timezone.now()
            end_time = now + timedelta(hours=hours_ahead)
            
            upcoming_logs = MedicationLog.objects.filter(
                schedule__patient=patient,
                schedule__is_active=True,
                scheduled_time__range=[now, end_time],
                status__in=[MedicationLogStatus.MISSED]  # Only show not-yet-taken doses
            ).select_related('schedule').order_by('scheduled_time')
            
            upcoming_doses = []
            for log in upcoming_logs:
                upcoming_doses.append({
                    'log_id': str(log.id),
                    'medication_name': log.schedule.medication_name,
                    'dosage': log.schedule.dosage,
                    'scheduled_time': log.scheduled_time,
                    'time_until': log.scheduled_time - now,
                    'reminder_time': log.scheduled_time - timedelta(
                        minutes=log.schedule.reminder_offset_minutes
                    )
                })
            
            return upcoming_doses
            
        except User.DoesNotExist:
            logger.error(f"Patient {patient_id} not found")
            raise ValueError(_("Patient not found"))
        
        except Exception as e:
            logger.error(f"Failed to get upcoming medications: {e}")
            raise
