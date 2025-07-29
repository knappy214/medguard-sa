from django.db import models
from django.utils.translation import gettext_lazy as _

from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.search import index


class HomePage(Page):
    """
    Home page model for MedGuard SA.
    
    This is the main landing page of the website.
    """
    
    # Page content
    hero_title = models.CharField(
        max_length=200,
        verbose_name=_('Hero Title'),
        help_text=_('Main title displayed in the hero section'),
        default=_('Welcome to MedGuard SA')
    )
    
    hero_subtitle = models.CharField(
        max_length=500,
        verbose_name=_('Hero Subtitle'),
        help_text=_('Subtitle displayed below the hero title'),
        blank=True
    )
    
    hero_content = RichTextField(
        verbose_name=_('Hero Content'),
        help_text=_('Rich text content for the hero section'),
        blank=True
    )
    
    # Main content sections
    main_content = RichTextField(
        verbose_name=_('Main Content'),
        help_text=_('Main content area of the homepage'),
        blank=True
    )
    
    # Call to action
    cta_title = models.CharField(
        max_length=200,
        verbose_name=_('Call to Action Title'),
        help_text=_('Title for the call to action section'),
        blank=True
    )
    
    cta_content = RichTextField(
        verbose_name=_('Call to Action Content'),
        help_text=_('Content for the call to action section'),
        blank=True
    )
    
    # SEO and metadata
    meta_description = models.CharField(
        max_length=160,
        verbose_name=_('Meta Description'),
        help_text=_('Description for search engines (max 160 characters)'),
        blank=True
    )
    
    # Page configuration
    parent_page_types = ['wagtailcore.Page']
    subpage_types = [
        'medications.MedicationIndexPage',
        # 'medguard_notifications.NotificationIndexPage',  # Temporarily disabled
    ]
    
    # Search configuration
    search_fields = Page.search_fields + [
        index.SearchField('hero_title'),
        index.SearchField('hero_subtitle'),
        index.SearchField('hero_content'),
        index.SearchField('main_content'),
        index.SearchField('cta_title'),
        index.SearchField('cta_content'),
    ]
    
    # Admin panels
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('hero_title'),
            FieldPanel('hero_subtitle'),
            FieldPanel('hero_content'),
        ], heading=_('Hero Section')),
        FieldPanel('main_content'),
        MultiFieldPanel([
            FieldPanel('cta_title'),
            FieldPanel('cta_content'),
        ], heading=_('Call to Action')),
    ]
    
    promote_panels = Page.promote_panels + [
        FieldPanel('meta_description'),
    ]
    
    class Meta:
        verbose_name = _('Home Page')
        verbose_name_plural = _('Home Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Add extra context to the template."""
        context = super().get_context(request, *args, **kwargs)
        
        # Add recent medications (if any)
        try:
            from medications.models import Medication
            context['recent_medications'] = Medication.objects.all()[:5]
        except ImportError:
            context['recent_medications'] = []
        
        # Add recent notifications (if any)
        try:
            from medguard_notifications.models import Notification
            context['recent_notifications'] = Notification.objects.filter(
                is_active=True
            )[:5]
        except ImportError:
            context['recent_notifications'] = []
        
        return context 