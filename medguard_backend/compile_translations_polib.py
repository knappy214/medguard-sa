#!/usr/bin/env python3
"""
Improved script to compile .po files to .mo files using polib.
This should work better than the custom implementation.
"""

import os
import polib
from pathlib import Path

def compile_translations():
    """Compile all .po files in the locale directory using polib."""
    base_dir = Path(__file__).parent
    locale_dir = base_dir / 'locale'
    
    if not locale_dir.exists():
        print(f"Locale directory not found: {locale_dir}")
        return
    
    for lang_dir in locale_dir.iterdir():
        if not lang_dir.is_dir():
            continue
            
        lc_messages_dir = lang_dir / 'LC_MESSAGES'
        if not lc_messages_dir.exists():
            continue
            
        po_file = lc_messages_dir / 'django.po'
        mo_file = lc_messages_dir / 'django.mo'
        
        if po_file.exists():
            print(f"Compiling {po_file}...")
            try:
                # Load the .po file
                po = polib.pofile(str(po_file))
                
                # Save as .mo file
                po.save_as_mofile(str(mo_file))
                print(f"Created {mo_file}")
                
                # Verify some translations
                print(f"  Found {len(po)} translation entries")
                for entry in po[:3]:  # Show first 3 entries
                    if entry.msgstr:
                        print(f"    '{entry.msgid}' -> '{entry.msgstr}'")
                    else:
                        print(f"    '{entry.msgid}' -> (untranslated)")
                        
            except Exception as e:
                print(f"Error compiling {po_file}: {e}")
        else:
            print(f"No .po file found in {lc_messages_dir}")

if __name__ == '__main__':
    compile_translations() 