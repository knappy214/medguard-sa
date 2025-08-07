"""
Views for Healthcare Analytics Plugin
"""
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from .models import AnalyticsReport, Dashboard


class AnalyticsDashboardView(PermissionRequiredMixin, TemplateView):
    """Healthcare analytics dashboard."""
    
    template_name = "wagtail_healthcare_analytics/dashboard.html"
    permission_required = "wagtail_healthcare_analytics.view_analyticsreport"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Recent reports
        recent_reports = AnalyticsReport.objects.order_by('-generated_at')[:10]
        
        # Available dashboards
        dashboards = Dashboard.objects.filter(
            models.Q(is_public=True) | 
            models.Q(created_by=self.request.user) |
            models.Q(allowed_users=self.request.user)
        ).distinct()
        
        context.update({
            'title': _("Healthcare Analytics Dashboard"),
            'recent_reports': recent_reports,
            'dashboards': dashboards,
        })
        
        return context
