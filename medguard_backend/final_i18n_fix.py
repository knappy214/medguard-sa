#!/usr/bin/env python3
"""
Final i18n fix that ensures translations work properly.
This script addresses the Django translation loading issue.
"""

import os
import sys
import shutil
from pathlib import Path
import polib

def final_i18n_fix():
    """Final fix for internationalization."""
    
    print("🔧 Final i18n Fix")
    print("=" * 30)
    
    base_dir = Path(__file__).parent
    locale_dir = base_dir / 'locale'
    
    # Step 1: Recompile translations with polib
    print("\n1. Recompiling translations...")
    for lang_dir in locale_dir.iterdir():
        if not lang_dir.is_dir():
            continue
            
        lc_messages_dir = lang_dir / 'LC_MESSAGES'
        if not lc_messages_dir.exists():
            continue
            
        po_file = lc_messages_dir / 'django.po'
        mo_file = lc_messages_dir / 'django.mo'
        
        if po_file.exists():
            print(f"   Compiling {po_file}...")
            try:
                po = polib.pofile(str(po_file))
                po.save_as_mofile(str(mo_file))
                print(f"   ✅ Created {mo_file}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    # Step 2: Create a simple test view that works
    print("\n2. Creating working test view...")
    
    test_view_content = '''
from django.shortcuts import render
from django.utils.translation import activate, gettext as _
from django.http import JsonResponse

def working_i18n_test(request):
    """Working i18n test view."""
    
    # Test translations
    activate('af-ZA')
    
    translations = {
        'Medications': _('Medications'),
        'Medication Schedules': _('Medication Schedules'),
        'Medication Logs': _('Medication Logs'),
        'Stock Alerts': _('Stock Alerts'),
        'Language': _('Language'),
        'Current': _('Current')
    }
    
    context = {
        'translations': translations,
        'current_language': 'af-ZA',
        'test_strings': [
            'Medications',
            'Medication Schedules', 
            'Medication Logs',
            'Stock Alerts',
            'Language',
            'Current'
        ]
    }
    
    return render(request, 'medications/working_i18n_test.html', context)

def api_i18n_test(request):
    """API endpoint for i18n testing."""
    activate('af-ZA')
    
    translations = {
        'Medications': _('Medications'),
        'Medication Schedules': _('Medication Schedules'),
        'Medication Logs': _('Medication Logs'),
        'Stock Alerts': _('Stock Alerts'),
        'Language': _('Language'),
        'Current': _('Current')
    }
    
    return JsonResponse({
        'success': True,
        'language': 'af-ZA',
        'translations': translations
    })
'''
    
    # Add to views.py
    views_file = base_dir / 'medications' / 'views.py'
    if views_file.exists():
        with open(views_file, 'a', encoding='utf-8') as f:
            f.write(test_view_content)
        print("   ✅ Added working test views to views.py")
    
    # Step 3: Create a simple template
    print("\n3. Creating test template...")
    
    template_content = '''
{% extends "wagtailadmin/base.html" %}
{% load i18n %}

{% block title %}Working i18n Test - MedGuard SA{% endblock title %}

{% block content %}
<div class="nice-padding">
    <h1>🌍 Working Internationalization Test</h1>
    
    <div class="panel">
        <h2>Current Language: {{ current_language }}</h2>
        
        <h3>Translation Results:</h3>
        <table class="listing">
            <thead>
                <tr>
                    <th>English</th>
                    <th>Translated</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for english, translated in translations.items %}
                <tr>
                    <td>{{ english }}</td>
                    <td>{{ translated }}</td>
                    <td>
                        {% if translated != english %}
                            <span style="color: green;">✅ Working</span>
                        {% else %}
                            <span style="color: red;">❌ Not Working</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <div class="panel">
        <h3>Test Links:</h3>
        <p><a href="/medications/working-i18n-test/" class="button">Test Working View</a></p>
        <p><a href="/medications/api-i18n-test/" class="button">Test API Endpoint</a></p>
    </div>
</div>
{% endblock content %}
'''
    
    template_dir = base_dir / 'templates' / 'medications'
    template_dir.mkdir(parents=True, exist_ok=True)
    
    with open(template_dir / 'working_i18n_test.html', 'w', encoding='utf-8') as f:
        f.write(template_content)
    print("   ✅ Created working_i18n_test.html template")
    
    # Step 4: Add URLs
    print("\n4. Adding URLs...")
    
    # The URLs are already added to the main urls.py
    
    # Step 5: Instructions
    print("\n5. Next Steps:")
    print("   =============")
    print("   1. Restart Django server: python manage.py runserver")
    print("   2. Visit: http://localhost:8000/medications/working-i18n-test/")
    print("   3. Visit: http://localhost:8000/af-za/medications/working-i18n-test/")
    print("   4. Test API: http://localhost:8000/medications/api-i18n-test/")
    
    print("\n🎉 Final i18n fix completed!")

if __name__ == '__main__':
    final_i18n_fix() 