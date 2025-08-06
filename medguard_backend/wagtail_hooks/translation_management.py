"""
Wagtail 7.0.2 Enhanced Page Translation Management

This module provides enhanced page translation functionality with content synchronization,
translation memory, and workflow management for MedGuard SA.
"""

from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.views.pages.listing import PageListingTable
from wagtail.models import Page, Locale
from wagtail.admin.ui.tables import Column, DateColumn
from wagtail.admin.views.pages import get_page_permissions_for_user
from wagtail.admin.views.pages.listing import get_page_listing_context
from wagtail.admin.views.pages.listing import get_page_listing_context_for_locale
from wagtail.admin.views.pages.listing import get_page_listing_context_for_translation
from wagtail.admin.views.pages.listing import get_page_listing_context_for_sync


class TranslationManagementMixin:
    """Mixin for enhanced translation management functionality."""
    
    def get_translation_status(self):
        """Get the translation status of the page."""
        if not hasattr(self, 'locale'):
            return 'not_translatable'
        
        # Check if page has translations
        translations = self.get_translations()
        if not translations.exists():
            return 'not_translated'
        
        # Check translation completeness
        source_fields = self.get_translatable_fields()
        for translation in translations:
            if not self.is_translation_complete(translation, source_fields):
                return 'incomplete'
        
        return 'complete'
    
    def is_translation_complete(self, translation, source_fields):
        """Check if translation is complete for all fields."""
        for field in source_fields:
            source_value = getattr(self, field, None)
            translation_value = getattr(translation, field, None)
            
            if source_value and not translation_value:
                return False
        
        return True
    
    def get_translatable_fields(self):
        """Get list of translatable fields."""
        return [
            'title',
            'seo_title',
            'search_description',
            'content',
            'body',
        ]
    
    def sync_content_structure(self, target_locale):
        """Sync content structure to target locale."""
        if not hasattr(self, 'locale'):
            return False
        
        # Create translation if it doesn't exist
        translation, created = self.get_or_create_translation(target_locale)
        
        if created:
            # Copy structure and metadata
            self.copy_structure_to_translation(translation)
        
        return translation
    
    def copy_structure_to_translation(self, translation):
        """Copy page structure to translation."""
        # Copy basic metadata
        translation.slug = self.slug
        translation.show_in_menus = self.show_in_menus
        translation.show_in_menus_default = self.show_in_menus_default
        
        # Copy content structure (without text content)
        if hasattr(self, 'content'):
            translation.content = self.content
        
        translation.save()


@hooks.register('register_page_listing_buttons')
def page_listing_buttons(page, page_perms, is_parent=False, context=None):
    """Add translation management buttons to page listing."""
    if not page_perms.can_edit():
        return []
    
    buttons = []
    
    # Add translation status indicator
    if hasattr(page, 'get_translation_status'):
        status = page.get_translation_status()
        buttons.append({
            'label': _('Translation Status'),
            'url': '#',
            'classname': f'translation-status-{status}',
            'title': _(f'Translation status: {status}'),
        })
    
    # Add sync content button
    if hasattr(page, 'sync_content_structure'):
        buttons.append({
            'label': _('Sync Content'),
            'url': f'/admin/pages/{page.id}/sync-content/',
            'classname': 'button button-small',
            'title': _('Sync content structure to translations'),
        })
    
    return buttons


@hooks.register('register_page_listing_more_buttons')
def page_listing_more_buttons(page, page_perms, is_parent=False, context=None):
    """Add more translation management buttons."""
    if not page_perms.can_edit():
        return []
    
    buttons = []
    
    # Add translation workflow buttons
    if hasattr(page, 'get_translation_status'):
        status = page.get_translation_status()
        if status == 'incomplete':
            buttons.append({
                'label': _('Complete Translation'),
                'url': f'/admin/pages/{page.id}/complete-translation/',
                'classname': 'button button-small',
            })
    
    return buttons


class TranslationStatusColumn(Column):
    """Custom column for translation status."""
    
    def __init__(self, *args, **kwargs):
        super().__init__('translation_status', _('Translation Status'), *args, **kwargs)
    
    def get_cell_value(self, page):
        if hasattr(page, 'get_translation_status'):
            return page.get_translation_status()
        return 'not_translatable'


@hooks.register('register_page_listing_table')
def register_translation_columns(table):
    """Register translation-related columns."""
    table.add_column(TranslationStatusColumn())


@hooks.register('register_page_listing_buttons')
def register_translation_workflow_buttons(page, page_perms, is_parent=False, context=None):
    """Register translation workflow buttons."""
    if not page_perms.can_edit():
        return []
    
    buttons = []
    
    # Add translation approval buttons
    if hasattr(page, 'get_translation_status'):
        status = page.get_translation_status()
        if status == 'complete':
            buttons.append({
                'label': _('Approve Translation'),
                'url': f'/admin/pages/{page.id}/approve-translation/',
                'classname': 'button button-small button-primary',
            })
    
    return buttons 