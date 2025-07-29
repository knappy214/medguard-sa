"""
Utility functions for the notification system.

This module contains helper functions for language-specific content,
notification formatting, and i18n support.
"""

from typing import Dict, Any, Optional
from django.utils.translation import gettext_lazy as _, activate, deactivate
from django.contrib.auth import get_user_model

User = get_user_model()


def get_user_language(user: User) -> str:
    """
    Get the user's preferred language.
    
    Args:
        user: User object
        
    Returns:
        Language code (en, af) or 'en' as default
    """
    user_language = getattr(user, 'language', 'en')
    if not user_language or user_language not in ['en', 'af']:
        user_language = 'en'
    return user_language


def get_localized_notification_content(
    notification_type: str,
    user_language: str,
    **kwargs
) -> Dict[str, str]:
    """
    Get localized notification content based on type and language.
    
    Args:
        notification_type: Type of notification (medication_reminder, stock_alert, etc.)
        user_language: User's language preference
        **kwargs: Additional context variables
        
    Returns:
        Dict containing localized title and content
    """
    # Activate the user's language
    activate(user_language)
    
    try:
        if notification_type == 'medication_reminder':
            medication_name = kwargs.get('medication_name', '')
            dosage = kwargs.get('dosage', '')
            instructions = kwargs.get('instructions', '')
            
            if user_language == 'af':
                title = _('Medikasie Herinnering')
                content = _('Tyd om jou medikasie te neem: {medication_name}').format(
                    medication_name=medication_name
                )
                if dosage:
                    content += f"\n{_('Dosis')}: {dosage}"
                if instructions:
                    content += f"\n{_('Instruksies')}: {instructions}"
            else:
                title = _('Medication Reminder')
                content = _('Time to take your medication: {medication_name}').format(
                    medication_name=medication_name
                )
                if dosage:
                    content += f"\n{_('Dosage')}: {dosage}"
                if instructions:
                    content += f"\n{_('Instructions')}: {instructions}"
        
        elif notification_type == 'low_stock_alert':
            medication_name = kwargs.get('medication_name', '')
            current_stock = kwargs.get('current_stock', 0)
            threshold = kwargs.get('threshold', 0)
            
            if user_language == 'af':
                title = _('Lae Voorraad Waarskuwing: {medication_name}').format(
                    medication_name=medication_name
                )
                content = _('Huidige voorraad: {current} eenhede. Drempel: {threshold} eenhede.').format(
                    current=current_stock,
                    threshold=threshold
                )
            else:
                title = _('Low Stock Alert: {medication_name}').format(
                    medication_name=medication_name
                )
                content = _('Current stock: {current} units. Threshold: {threshold} units.').format(
                    current=current_stock,
                    threshold=threshold
                )
        
        elif notification_type == 'expiring_medication':
            medication_name = kwargs.get('medication_name', '')
            days_until_expiry = kwargs.get('days_until_expiry', 0)
            expiry_date = kwargs.get('expiry_date', '')
            
            if user_language == 'af':
                title = _('Medikasie Verval Binnekort: {medication_name}').format(
                    medication_name=medication_name
                )
                content = _('Hierdie medikasie verval binne {days} dae op {date}.').format(
                    days=days_until_expiry,
                    date=expiry_date
                )
            else:
                title = _('Medication Expiring Soon: {medication_name}').format(
                    medication_name=medication_name
                )
                content = _('This medication expires in {days} days on {date}.').format(
                    days=days_until_expiry,
                    date=expiry_date
                )
        
        elif notification_type == 'system_maintenance':
            maintenance_time = kwargs.get('maintenance_time', '')
            
            if user_language == 'af':
                title = _('Stelsel Onderhoud')
                content = _('Geskeduleerde onderhoud vanaand om {time}.').format(
                    time=maintenance_time
                )
            else:
                title = _('System Maintenance')
                content = _('Scheduled maintenance tonight at {time}.').format(
                    time=maintenance_time
                )
        
        else:
            # Default fallback
            if user_language == 'af':
                title = _('Kennisgewing')
                content = _('Jy het \'n nuwe kennisgewing ontvang.')
            else:
                title = _('Notification')
                content = _('You have received a new notification.')
        
        return {
            'title': title,
            'content': content
        }
    
    finally:
        # Deactivate the language
        deactivate()


def format_medication_reminder_content(
    medication_name: str,
    user_language: str,
    dosage: Optional[str] = None,
    instructions: Optional[str] = None,
    timing: Optional[str] = None
) -> str:
    """
    Format medication reminder content in the user's language.
    
    Args:
        medication_name: Name of the medication
        user_language: User's language preference
        dosage: Dosage information
        instructions: Special instructions
        timing: When to take the medication
        
    Returns:
        Formatted content string
    """
    activate(user_language)
    
    try:
        if user_language == 'af':
            content = _('Tyd om jou medikasie te neem: {medication_name}').format(
                medication_name=medication_name
            )
            
            if timing:
                timing_map = {
                    'morning': _('oggend'),
                    'afternoon': _('middag'),
                    'evening': _('aand'),
                    'night': _('nag')
                }
                timing_text = timing_map.get(timing, timing)
                content += f"\n{_('Neem')} {timing_text}"
            
            if dosage:
                content += f"\n{_('Dosis')}: {dosage}"
            
            if instructions:
                content += f"\n{_('Instruksies')}: {instructions}"
        else:
            content = _('Time to take your medication: {medication_name}').format(
                medication_name=medication_name
            )
            
            if timing:
                timing_map = {
                    'morning': _('morning'),
                    'afternoon': _('afternoon'),
                    'evening': _('evening'),
                    'night': _('night')
                }
                timing_text = timing_map.get(timing, timing)
                content += f"\n{_('Take')} {timing_text}"
            
            if dosage:
                content += f"\n{_('Dosage')}: {dosage}"
            
            if instructions:
                content += f"\n{_('Instructions')}: {instructions}"
        
        return content
    
    finally:
        deactivate()


def get_priority_label(priority: str, user_language: str) -> str:
    """
    Get localized priority label.
    
    Args:
        priority: Priority level (low, medium, high, critical)
        user_language: User's language preference
        
    Returns:
        Localized priority label
    """
    activate(user_language)
    
    try:
        priority_map = {
            'low': _('Low'),
            'medium': _('Medium'),
            'high': _('High'),
            'critical': _('Critical')
        }
        
        if user_language == 'af':
            priority_map = {
                'low': _('Laag'),
                'medium': _('Medium'),
                'high': _('Hoog'),
                'critical': _('Kritiek')
            }
        
        return priority_map.get(priority, priority)
    
    finally:
        deactivate()


def get_notification_type_label(notification_type: str, user_language: str) -> str:
    """
    Get localized notification type label.
    
    Args:
        notification_type: Type of notification
        user_language: User's language preference
        
    Returns:
        Localized notification type label
    """
    activate(user_language)
    
    try:
        type_map = {
            'system': _('System Notification'),
            'medication': _('Medication Alert'),
            'stock': _('Stock Alert'),
            'maintenance': _('Maintenance Notice'),
            'security': _('Security Alert'),
            'general': _('General Announcement')
        }
        
        if user_language == 'af':
            type_map = {
                'system': _('Stelsel Kennisgewing'),
                'medication': _('Medikasie Waarskuwing'),
                'stock': _('Voorraad Waarskuwing'),
                'maintenance': _('Onderhoud Kennisgewing'),
                'security': _('Sekuriteit Waarskuwing'),
                'general': _('Algemene Aankondiging')
            }
        
        return type_map.get(notification_type, notification_type)
    
    finally:
        deactivate()


def format_time_preference(time_preference: str, user_language: str) -> str:
    """
    Format time preference in user's language.
    
    Args:
        time_preference: Time preference (immediate, morning, afternoon, evening, custom)
        user_language: User's language preference
        
    Returns:
        Localized time preference string
    """
    activate(user_language)
    
    try:
        if user_language == 'af':
            time_map = {
                'immediate': _('Onmiddellik'),
                'morning': _('Oggend (08:00)'),
                'afternoon': _('Middag (14:00)'),
                'evening': _('Aand (20:00)'),
                'custom': _('Aangepaste Tyd')
            }
        else:
            time_map = {
                'immediate': _('Immediate'),
                'morning': _('Morning (8:00 AM)'),
                'afternoon': _('Afternoon (2:00 PM)'),
                'evening': _('Evening (8:00 PM)'),
                'custom': _('Custom Time')
            }
        
        return time_map.get(time_preference, time_preference)
    
    finally:
        deactivate() 