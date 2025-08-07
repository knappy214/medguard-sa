"""
Views for Medication Tracker Plugin
Admin views for medication adherence tracking and management.
"""
import json
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q, Avg, Count
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import TemplateView
from wagtail.admin import messages as wagtail_messages

from .models import MedicationSchedule, MedicationLog, AdherenceReport, MedicationLogStatus
from .services import MedicationTrackerService

User = get_user_model()


class MedicationTrackerDashboardView(PermissionRequiredMixin, TemplateView):
    """Main dashboard view for medication tracking."""
    
    template_name = "wagtail_medication_tracker/dashboard.html"
    permission_required = "wagtail_medication_tracker.view_medicationschedule"
    
    def get_context_data(self, **kwargs):
        """Add context data for the dashboard."""
        context = super().get_context_data(**kwargs)
        
        # Get current user's role-based data
        if self.request.user.groups.filter(name='Healthcare Providers').exists():
            # Healthcare provider dashboard
            context.update(self._get_provider_dashboard_data())
        elif self.request.user.is_staff:
            # Admin dashboard
            context.update(self._get_admin_dashboard_data())
        else:
            # Patient dashboard
            context.update(self._get_patient_dashboard_data())
        
        return context
    
    def _get_provider_dashboard_data(self):
        """Get dashboard data for healthcare providers."""
        provider = self.request.user
        
        # Get patients with medications prescribed by this provider
        patient_schedules = MedicationSchedule.objects.filter(
            prescribed_by=provider,
            is_active=True
        ).select_related('patient')
        
        # Calculate adherence metrics
        total_patients = patient_schedules.values('patient').distinct().count()
        low_adherence_count = patient_schedules.filter(adherence_rate__lt=80).count()
        
        # Get recent activity
        recent_logs = MedicationLog.objects.filter(
            schedule__prescribed_by=provider
        ).select_related('schedule', 'schedule__patient').order_by('-created_at')[:10]
        
        # Get upcoming appointments/reviews
        schedules_needing_review = patient_schedules.filter(
            updated_at__lt=timezone.now() - timedelta(days=30)
        )[:10]
        
        return {
            'title': _("Healthcare Provider Dashboard"),
            'user_role': 'provider',
            'total_patients': total_patients,
            'total_active_schedules': patient_schedules.count(),
            'low_adherence_count': low_adherence_count,
            'recent_logs': recent_logs,
            'schedules_needing_review': schedules_needing_review,
            'adherence_alert_threshold': 80,
        }
    
    def _get_admin_dashboard_data(self):
        """Get dashboard data for administrators."""
        # System-wide metrics
        total_patients = User.objects.filter(
            medication_schedules__isnull=False
        ).distinct().count()
        
        total_schedules = MedicationSchedule.objects.filter(is_active=True).count()
        
        # Adherence statistics
        avg_adherence = MedicationSchedule.objects.filter(
            is_active=True
        ).aggregate(avg_rate=Avg('adherence_rate'))['avg_rate'] or 0
        
        low_adherence_count = MedicationSchedule.objects.filter(
            is_active=True,
            adherence_rate__lt=80
        ).count()
        
        # Recent activity
        recent_logs = MedicationLog.objects.select_related(
            'schedule', 'schedule__patient'
        ).order_by('-created_at')[:15]
        
        # System alerts
        alerts = []
        if low_adherence_count > 0:
            alerts.append({
                'type': 'warning',
                'message': _("{count} patients with low adherence").format(count=low_adherence_count)
            })
        
        return {
            'title': _("Medication Tracker Admin Dashboard"),
            'user_role': 'admin',
            'total_patients': total_patients,
            'total_schedules': total_schedules,
            'avg_adherence_rate': avg_adherence,
            'low_adherence_count': low_adherence_count,
            'recent_logs': recent_logs,
            'system_alerts': alerts,
        }
    
    def _get_patient_dashboard_data(self):
        """Get dashboard data for patients."""
        patient = self.request.user
        
        # Get patient's medication schedules
        schedules = MedicationSchedule.objects.filter(
            patient=patient,
            is_active=True
        ).select_related('prescribed_by')
        
        # Get upcoming medications
        tracker_service = MedicationTrackerService()
        upcoming_meds = tracker_service.get_upcoming_medications(patient.id, hours_ahead=24)
        
        # Get recent logs
        recent_logs = MedicationLog.objects.filter(
            schedule__patient=patient
        ).select_related('schedule').order_by('-created_at')[:10]
        
        # Calculate overall adherence
        adherence_summary = tracker_service.get_patient_adherence_summary(patient.id)
        
        return {
            'title': _("My Medications"),
            'user_role': 'patient',
            'schedules': schedules,
            'upcoming_medications': upcoming_meds,
            'recent_logs': recent_logs,
            'adherence_summary': adherence_summary,
            'total_medications': schedules.count(),
        }


class PatientAdherenceView(PermissionRequiredMixin, TemplateView):
    """View for displaying patient adherence details."""
    
    template_name = "wagtail_medication_tracker/patient_adherence.html"
    permission_required = "wagtail_medication_tracker.view_medicationschedule"
    
    def get_context_data(self, **kwargs):
        """Add context data for patient adherence view."""
        context = super().get_context_data(**kwargs)
        
        patient_id = kwargs.get('patient_id')
        patient = get_object_or_404(User, id=patient_id)
        
        # Check permissions
        if not self._can_view_patient_data(patient):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        
        # Get adherence data
        tracker_service = MedicationTrackerService()
        
        # Different time periods
        periods = [7, 30, 90]
        adherence_data = {}
        
        for period in periods:
            adherence_data[f'{period}_days'] = tracker_service.get_patient_adherence_summary(
                patient_id, period
            )
        
        # Get detailed schedule information
        schedules = MedicationSchedule.objects.filter(
            patient=patient,
            is_active=True
        ).select_related('prescribed_by')
        
        # Get recent reports
        recent_reports = AdherenceReport.objects.filter(
            patient=patient
        ).order_by('-report_date')[:5]
        
        context.update({
            'patient': patient,
            'adherence_data': adherence_data,
            'schedules': schedules,
            'recent_reports': recent_reports,
        })
        
        return context
    
    def _can_view_patient_data(self, patient):
        """Check if current user can view this patient's data."""
        user = self.request.user
        
        # Admins can view all data
        if user.is_staff:
            return True
        
        # Patients can view their own data
        if user == patient:
            return True
        
        # Healthcare providers can view their patients' data
        if user.groups.filter(name='Healthcare Providers').exists():
            return MedicationSchedule.objects.filter(
                patient=patient,
                prescribed_by=user
            ).exists()
        
        return False


class MedicationLogView(PermissionRequiredMixin, View):
    """View for logging medication doses."""
    
    permission_required = "wagtail_medication_tracker.add_medicationlog"
    
    def get(self, request, log_id=None):
        """Display medication logging form."""
        if log_id:
            log = get_object_or_404(MedicationLog, id=log_id)
            
            # Check permissions
            if not self._can_modify_log(log):
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
            
            context = {
                'title': _("Log Medication Dose"),
                'log': log,
                'schedule': log.schedule,
            }
        else:
            # Show form to select medication to log
            if request.user.is_staff:
                # Staff can log for any active schedule
                schedules = MedicationSchedule.objects.filter(is_active=True)
            else:
                # Patients can only log their own medications
                schedules = MedicationSchedule.objects.filter(
                    patient=request.user,
                    is_active=True
                )
            
            context = {
                'title': _("Select Medication to Log"),
                'schedules': schedules,
            }
        
        return render(request, 'wagtail_medication_tracker/log_medication.html', context)
    
    def post(self, request, log_id=None):
        """Handle medication logging submission."""
        if log_id:
            # Update existing log
            log = get_object_or_404(MedicationLog, id=log_id)
            
            if not self._can_modify_log(log):
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
            
            tracker_service = MedicationTrackerService()
            
            # Get form data
            action = request.POST.get('action')
            taken_at_str = request.POST.get('taken_at')
            dose_taken = request.POST.get('dose_taken')
            side_effects = request.POST.get('side_effects')
            notes = request.POST.get('notes')
            
            try:
                if action == 'taken':
                    # Parse taken_at time
                    taken_at = None
                    if taken_at_str:
                        taken_at = datetime.fromisoformat(taken_at_str.replace('Z', '+00:00'))
                    
                    tracker_service.log_medication_taken(
                        log_id=str(log.id),
                        taken_at=taken_at,
                        dose_taken=dose_taken,
                        side_effects=side_effects,
                        notes=notes,
                        logged_by_id=request.user.id
                    )
                    
                    wagtail_messages.success(
                        request, 
                        _("Medication dose logged successfully")
                    )
                
                elif action == 'missed':
                    reason = request.POST.get('reason', notes)
                    
                    tracker_service.mark_medication_missed(
                        log_id=str(log.id),
                        reason=reason,
                        logged_by_id=request.user.id
                    )
                    
                    wagtail_messages.success(
                        request, 
                        _("Medication marked as missed")
                    )
                
                # Redirect based on user role
                if request.user.is_staff:
                    return redirect('medication_tracker_dashboard')
                else:
                    return redirect('patient_adherence', patient_id=request.user.id)
                
            except Exception as e:
                wagtail_messages.error(
                    request, 
                    _("Error logging medication: {}").format(str(e))
                )
                return self.get(request, log_id)
        
        else:
            # Create new log entry - redirect to specific log
            schedule_id = request.POST.get('schedule_id')
            if schedule_id:
                schedule = get_object_or_404(MedicationSchedule, id=schedule_id)
                
                # Find next scheduled dose
                next_log = MedicationLog.objects.filter(
                    schedule=schedule,
                    scheduled_time__gte=timezone.now(),
                    status=MedicationLogStatus.MISSED
                ).order_by('scheduled_time').first()
                
                if next_log:
                    return redirect('medication_log', log_id=next_log.id)
                else:
                    wagtail_messages.warning(
                        request,
                        _("No upcoming doses found for this medication")
                    )
            
            return self.get(request)
    
    def _can_modify_log(self, log):
        """Check if current user can modify this log."""
        user = self.request.user
        
        # Admins can modify all logs
        if user.is_staff:
            return True
        
        # Patients can modify their own logs
        if user == log.schedule.patient:
            return True
        
        # Healthcare providers can modify logs for their prescribed medications
        if user.groups.filter(name='Healthcare Providers').exists():
            return log.schedule.prescribed_by == user
        
        return False


class AdherenceReportView(PermissionRequiredMixin, TemplateView):
    """View for displaying adherence reports."""
    
    template_name = "wagtail_medication_tracker/adherence_report.html"
    permission_required = "wagtail_medication_tracker.view_adherencereport"
    
    def get_context_data(self, **kwargs):
        """Add context data for adherence report view."""
        context = super().get_context_data(**kwargs)
        
        report_id = kwargs.get('report_id')
        report = get_object_or_404(AdherenceReport, id=report_id)
        
        # Check permissions
        if not self._can_view_report(report):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        
        context.update({
            'report': report,
            'patient': report.patient,
        })
        
        return context
    
    def post(self, request, report_id=None):
        """Handle report generation requests."""
        if not report_id:
            # Generate new report
            patient_id = request.POST.get('patient_id')
            period_days = int(request.POST.get('period_days', 30))
            
            if not patient_id:
                wagtail_messages.error(request, _("Patient ID is required"))
                return redirect('medication_tracker_dashboard')
            
            try:
                tracker_service = MedicationTrackerService()
                report = tracker_service.generate_adherence_report(
                    patient_id=int(patient_id),
                    period_days=period_days,
                    generated_by_id=request.user.id
                )
                
                wagtail_messages.success(
                    request,
                    _("Adherence report generated successfully")
                )
                
                return redirect('adherence_report', report_id=report.id)
                
            except Exception as e:
                wagtail_messages.error(
                    request,
                    _("Error generating report: {}").format(str(e))
                )
                return redirect('medication_tracker_dashboard')
        
        return redirect('adherence_report', report_id=report_id)
    
    def _can_view_report(self, report):
        """Check if current user can view this report."""
        user = self.request.user
        
        # Admins can view all reports
        if user.is_staff:
            return True
        
        # Patients can view their own reports
        if user == report.patient:
            return True
        
        # Healthcare providers can view reports for their patients
        if user.groups.filter(name='Healthcare Providers').exists():
            return MedicationSchedule.objects.filter(
                patient=report.patient,
                prescribed_by=user
            ).exists()
        
        return False


class MedicationReminderView(PermissionRequiredMixin, TemplateView):
    """View for managing medication reminders."""
    
    template_name = "wagtail_medication_tracker/reminders.html"
    permission_required = "wagtail_medication_tracker.manage_medication_reminders"
    
    def get_context_data(self, **kwargs):
        """Add context data for reminders view."""
        context = super().get_context_data(**kwargs)
        
        # Get upcoming reminders
        now = timezone.now()
        upcoming_reminders = []
        
        # Get active schedules with reminders enabled
        schedules = MedicationSchedule.objects.filter(
            is_active=True,
            reminder_enabled=True
        ).select_related('patient')
        
        for schedule in schedules:
            # Get next few doses
            upcoming_logs = MedicationLog.objects.filter(
                schedule=schedule,
                scheduled_time__gte=now,
                status=MedicationLogStatus.MISSED
            ).order_by('scheduled_time')[:3]
            
            for log in upcoming_logs:
                reminder_time = log.scheduled_time - timedelta(
                    minutes=schedule.reminder_offset_minutes
                )
                
                upcoming_reminders.append({
                    'log': log,
                    'schedule': schedule,
                    'reminder_time': reminder_time,
                    'time_until_reminder': reminder_time - now,
                })
        
        # Sort by reminder time
        upcoming_reminders.sort(key=lambda x: x['reminder_time'])
        
        context.update({
            'upcoming_reminders': upcoming_reminders[:20],  # Limit for performance
            'total_active_schedules': schedules.count(),
        })
        
        return context


class MedicationTrackerAPIView(PermissionRequiredMixin, View):
    """API endpoint for mobile and external integrations."""
    
    permission_required = "wagtail_medication_tracker.view_medicationschedule"
    
    def get(self, request):
        """Handle API GET requests."""
        endpoint = request.GET.get('endpoint')
        
        if endpoint == 'upcoming_medications':
            return self._get_upcoming_medications(request)
        elif endpoint == 'adherence_summary':
            return self._get_adherence_summary(request)
        elif endpoint == 'medication_schedules':
            return self._get_medication_schedules(request)
        else:
            return JsonResponse({'error': 'Invalid endpoint'}, status=400)
    
    def post(self, request):
        """Handle API POST requests."""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'log_medication':
                return self._log_medication_api(request, data)
            elif action == 'mark_missed':
                return self._mark_missed_api(request, data)
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    def _get_upcoming_medications(self, request):
        """Get upcoming medications for API."""
        patient_id = request.GET.get('patient_id', request.user.id)
        hours_ahead = int(request.GET.get('hours_ahead', 24))
        
        try:
            tracker_service = MedicationTrackerService()
            upcoming_meds = tracker_service.get_upcoming_medications(
                patient_id, hours_ahead
            )
            
            # Serialize for JSON response
            serialized_meds = []
            for med in upcoming_meds:
                serialized_meds.append({
                    'log_id': med['log_id'],
                    'medication_name': med['medication_name'],
                    'dosage': med['dosage'],
                    'scheduled_time': med['scheduled_time'].isoformat(),
                    'time_until_seconds': int(med['time_until'].total_seconds()),
                })
            
            return JsonResponse({
                'success': True,
                'upcoming_medications': serialized_meds
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _get_adherence_summary(self, request):
        """Get adherence summary for API."""
        patient_id = request.GET.get('patient_id', request.user.id)
        days = int(request.GET.get('days', 30))
        
        try:
            tracker_service = MedicationTrackerService()
            summary = tracker_service.get_patient_adherence_summary(patient_id, days)
            
            return JsonResponse({
                'success': True,
                'adherence_summary': summary
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _log_medication_api(self, request, data):
        """Log medication via API."""
        try:
            log_id = data.get('log_id')
            taken_at_str = data.get('taken_at')
            
            taken_at = None
            if taken_at_str:
                taken_at = datetime.fromisoformat(taken_at_str.replace('Z', '+00:00'))
            
            tracker_service = MedicationTrackerService()
            log = tracker_service.log_medication_taken(
                log_id=log_id,
                taken_at=taken_at,
                dose_taken=data.get('dose_taken'),
                side_effects=data.get('side_effects'),
                notes=data.get('notes'),
                logged_by_id=request.user.id,
                device_id=data.get('device_id'),
                location_data=data.get('location_data')
            )
            
            return JsonResponse({
                'success': True,
                'log_id': str(log.id),
                'status': log.status
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _mark_missed_api(self, request, data):
        """Mark medication missed via API."""
        try:
            log_id = data.get('log_id')
            reason = data.get('reason')
            
            tracker_service = MedicationTrackerService()
            log = tracker_service.mark_medication_missed(
                log_id=log_id,
                reason=reason,
                logged_by_id=request.user.id
            )
            
            return JsonResponse({
                'success': True,
                'log_id': str(log.id),
                'status': log.status
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
