"""
Views for Emergency Access Plugin
"""
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from .models import EmergencyAccess


class EmergencyDashboardView(PermissionRequiredMixin, TemplateView):
    """Emergency access dashboard."""
    
    template_name = "wagtail_emergency_access/dashboard.html"
    permission_required = "wagtail_emergency_access.view_emergencyaccess"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Recent emergency accesses
        recent_accesses = EmergencyAccess.objects.order_by('-accessed_at')[:10]
        pending_reviews = EmergencyAccess.objects.filter(requires_review=True, reviewed_by__isnull=True).count()
        
        context.update({
            'title': _("Emergency Access Dashboard"),
            'recent_accesses': recent_accesses,
            'pending_reviews': pending_reviews,
        })
        
        return context
