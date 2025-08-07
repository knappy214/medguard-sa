"""
Views for HIPAA Compliance Plugin
Admin views for HIPAA compliance monitoring and reporting.
"""
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import timedelta

from .models import PHIAccessLog, BreachIncident, ComplianceAssessment


class HIPAADashboardView(PermissionRequiredMixin, TemplateView):
    """Main dashboard for HIPAA compliance monitoring."""
    
    template_name = "wagtail_hipaa_compliance/dashboard.html"
    permission_required = "wagtail_hipaa_compliance.view_breachincident"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Breach incident statistics
        total_incidents = BreachIncident.objects.count()
        open_incidents = BreachIncident.objects.filter(status='open').count()
        critical_incidents = BreachIncident.objects.filter(severity='critical').count()
        
        # PHI access statistics
        today = timezone.now().date()
        phi_accesses_today = PHIAccessLog.objects.filter(accessed_at__date=today).count()
        unauthorized_accesses = PHIAccessLog.objects.filter(is_authorized=False).count()
        
        # Compliance assessments
        recent_assessments = ComplianceAssessment.objects.order_by('-start_date')[:5]
        
        context.update({
            'title': _("HIPAA Compliance Dashboard"),
            'total_incidents': total_incidents,
            'open_incidents': open_incidents,
            'critical_incidents': critical_incidents,
            'phi_accesses_today': phi_accesses_today,
            'unauthorized_accesses': unauthorized_accesses,
            'recent_assessments': recent_assessments,
        })
        
        return context


class BreachReportingView(PermissionRequiredMixin, TemplateView):
    """View for breach incident reporting."""
    
    template_name = "wagtail_hipaa_compliance/breach_reporting.html"
    permission_required = "wagtail_hipaa_compliance.add_breachincident"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update({
            'title': _("Breach Incident Reporting"),
        })
        
        return context


class ComplianceReportView(PermissionRequiredMixin, TemplateView):
    """View for compliance reporting."""
    
    template_name = "wagtail_hipaa_compliance/compliance_report.html"
    permission_required = "wagtail_hipaa_compliance.generate_compliance_reports"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Generate compliance metrics
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        metrics = {
            'phi_accesses_30_days': PHIAccessLog.objects.filter(
                accessed_at__gte=thirty_days_ago
            ).count(),
            'unauthorized_accesses_30_days': PHIAccessLog.objects.filter(
                accessed_at__gte=thirty_days_ago,
                is_authorized=False
            ).count(),
            'breach_incidents_30_days': BreachIncident.objects.filter(
                discovered_at__gte=thirty_days_ago
            ).count(),
        }
        
        context.update({
            'title': _("Compliance Report"),
            'metrics': metrics,
        })
        
        return context
