#!/usr/bin/env python
"""
Validate translation files for MedGuard SA notification system.

This script checks the .po files for syntax errors and validates
that all notification system translations are present.
"""

import os
import re
import sys
from pathlib import Path

def validate_po_file(file_path):
    """Validate a .po file for syntax errors."""
    print(f"🔍 Validating {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for basic .po file structure
        if 'msgid ""' not in content:
            print(f"❌ {file_path}: Missing required msgid header")
            return False
        
        # Check for proper msgid/msgstr pairs
        msgid_pattern = r'^msgid\s+"([^"]*)"'
        msgstr_pattern = r'^msgstr\s+"([^"]*)"'
        
        lines = content.split('\n')
        msgid_count = 0
        msgstr_count = 0
        
        for line in lines:
            if re.match(msgid_pattern, line):
                msgid_count += 1
            elif re.match(msgstr_pattern, line):
                msgstr_count += 1
        
        if msgid_count != msgstr_count:
            print(f"❌ {file_path}: Mismatched msgid/msgstr pairs ({msgid_count} msgid, {msgstr_count} msgstr)")
            return False
        
        # Check for notification system translations
        notification_translations = [
            'Medication Reminder',
            'Low Stock Alert',
            'System Notification',
            'Medication Alert',
            'Stock Alert',
            'Maintenance Notice',
            'Security Alert',
            'General Announcement',
            'View in Dashboard',
            'This notification was sent by',
            'If you have any questions, please contact our support team.',
            'All rights reserved.',
            'Please acknowledge this notification by logging into your account.',
            'MedGuard SA notification'
        ]
        
        afrikaans_translations = [
            'Medikasie Herinnering',
            'Lae Voorraad Waarskuwing',
            'Stelsel Kennisgewing',
            'Medikasie Waarskuwing',
            'Voorraad Waarskuwing',
            'Onderhoud Kennisgewing',
            'Sekuriteit Waarskuwing',
            'Algemene Aankondiging',
            'Bekyk in Dashboard',
            'Hierdie kennisgewing is gestuur deur',
            'As jy enige vrae het, kontak asseblief ons ondersteuningspan.',
            'Alle regte voorbehou.',
            'Kennisgewing moet erken word deur in te teken op jou rekening.',
            'MedGuard SA kennisgewing'
        ]
        
        missing_translations = []
        
        # Check based on locale
        if 'af' in str(file_path):
            # Afrikaans file
            for translation in afrikaans_translations:
                if translation not in content:
                    missing_translations.append(translation)
        else:
            # English file
            for translation in notification_translations:
                if translation not in content:
                    missing_translations.append(translation)
        
        if missing_translations:
            print(f"⚠️  {file_path}: Missing translations: {missing_translations[:3]}...")
            return False
        
        print(f"✅ {file_path}: Valid")
        return True
        
    except Exception as e:
        print(f"❌ {file_path}: Error reading file - {str(e)}")
        return False

def main():
    """Main validation function."""
    print("🚀 Validating MedGuard SA Notification System Translations")
    print("=" * 60)
    
    # Get the locale directory
    locale_dir = Path(__file__).parent / 'locale'
    
    if not locale_dir.exists():
        print(f"❌ Locale directory not found: {locale_dir}")
        return False
    
    # Find all .po files
    po_files = list(locale_dir.rglob('*.po'))
    
    if not po_files:
        print(f"❌ No .po files found in {locale_dir}")
        return False
    
    print(f"📁 Found {len(po_files)} .po files")
    
    valid_count = 0
    total_count = len(po_files)
    
    for po_file in po_files:
        if validate_po_file(po_file):
            valid_count += 1
    
    print("\n" + "=" * 60)
    print("📊 Translation Validation Results")
    print("=" * 60)
    
    print(f"✅ Valid files: {valid_count}/{total_count}")
    print(f"❌ Invalid files: {total_count - valid_count}/{total_count}")
    
    if valid_count == total_count:
        print("\n🎉 All translation files are valid!")
        print("\nThe notification system translations have been successfully added to:")
        for po_file in po_files:
            print(f"  - {po_file}")
        
        print("\n📝 Next steps:")
        print("1. Install GNU gettext tools to compile the translations")
        print("2. Run: python manage.py compilemessages")
        print("3. Restart your Django application")
        
        return True
    else:
        print(f"\n❌ {total_count - valid_count} translation files have issues")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 