"""
Views for the home app.
"""

from django.shortcuts import render
from django.utils.translation import gettext as _


def i18n_test_view(request):
    """
    Test view to demonstrate internationalization functionality.
    """
    context = {
        'page_title': _('MedGuard SA - Internationalization Test'),
        'current_language': request.LANGUAGE_CODE,
    }
    return render(request, 'i18n_test.html', context) 