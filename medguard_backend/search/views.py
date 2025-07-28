from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from wagtail.models import Page


def search(request):
    """
    Search view for MedGuard SA.
    
    Searches across all searchable content including pages, medications, and notifications.
    """
    search_query = request.GET.get('query', None)
    page = request.GET.get('page')
    
    # Search results
    search_results = []
    
    if search_query:
        # Search in Wagtail pages
        page_results = Page.objects.live().search(search_query)
        
        # Search in medications (if available)
        medication_results = []
        try:
            from medications.models import Medication
            medication_results = Medication.objects.filter(
                models.Q(name__icontains=search_query) |
                models.Q(generic_name__icontains=search_query) |
                models.Q(description__icontains=search_query)
            )
        except ImportError:
            pass
        
        # Search in notifications (if available)
        notification_results = []
        try:
            from notifications.models import Notification
            notification_results = Notification.objects.filter(
                models.Q(title__icontains=search_query) |
                models.Q(content__icontains=search_query),
                is_active=True
            )
        except ImportError:
            pass
        
        # Combine results
        search_results = list(page_results) + list(medication_results) + list(notification_results)
    
    # Pagination
    paginator = Paginator(search_results, 10)
    try:
        search_results = paginator.page(page)
    except PageNotAnInteger:
        search_results = paginator.page(1)
    except EmptyPage:
        search_results = paginator.page(paginator.num_pages)
    
    return TemplateResponse(request, 'search/search.html', {
        'search_query': search_query,
        'search_results': search_results,
        'page_title': _('Search Results') if search_query else _('Search'),
    }) 