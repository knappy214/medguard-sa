#!/usr/bin/env python3
"""
Simple script to compile .po files to .mo files without requiring GNU gettext.
This is a basic implementation that handles simple translation files.
"""

import os
import struct
import re
from pathlib import Path

def parse_po_file(po_file_path):
    """Parse a .po file and extract msgid/msgstr pairs."""
    translations = {}
    current_msgid = None
    current_msgstr = None
    
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into entries
    entries = content.split('\n\n')
    
    for entry in entries:
        if not entry.strip():
            continue
            
        # Extract msgid
        msgid_match = re.search(r'msgid\s+"(.*?)"', entry, re.DOTALL)
        if msgid_match:
            current_msgid = msgid_match.group(1)
            
        # Extract msgstr
        msgstr_match = re.search(r'msgstr\s+"(.*?)"', entry, re.DOTALL)
        if msgstr_match:
            current_msgstr = msgstr_match.group(1)
            
        if current_msgid is not None and current_msgstr is not None:
            translations[current_msgid] = current_msgstr
            current_msgid = None
            current_msgstr = None
    
    return translations

def create_mo_file(translations, mo_file_path):
    """Create a .mo file from translations."""
    # MO file format: https://www.gnu.org/software/gettext/manual/html_node/MO-Files.html
    
    # Sort keys for consistent ordering
    keys = sorted(translations.keys())
    values = [translations[key] for key in keys]
    
    # Calculate offsets
    key_count = len(keys)
    value_count = len(values)
    
    # Header: magic number + revision + count + offset_originals + offset_translations + offset_hash + offset_hash_size
    header_size = 7 * 4  # 7 uint32 values
    key_offset = header_size
    value_offset = key_offset + key_count * 8  # 8 bytes per key entry (length + offset)
    
    # Create the MO file content
    mo_content = bytearray()
    
    # Magic number (0x950412de for little-endian)
    mo_content.extend(struct.pack('<I', 0x950412de))
    # Revision (0)
    mo_content.extend(struct.pack('<I', 0))
    # Count
    mo_content.extend(struct.pack('<I', key_count))
    # Offset to original strings
    mo_content.extend(struct.pack('<I', key_offset))
    # Offset to translated strings
    mo_content.extend(struct.pack('<I', value_offset))
    # Offset to hash table (0 for now)
    mo_content.extend(struct.pack('<I', 0))
    # Size of hash table (0 for now)
    mo_content.extend(struct.pack('<I', 0))
    
    # Calculate string offsets
    string_offset = value_offset + value_count * 8
    
    # Add key entries
    for key in keys:
        mo_content.extend(struct.pack('<I', len(key)))
        mo_content.extend(struct.pack('<I', string_offset))
        string_offset += len(key) + 1  # +1 for null terminator
    
    # Add value entries
    for value in values:
        mo_content.extend(struct.pack('<I', len(value)))
        mo_content.extend(struct.pack('<I', string_offset))
        string_offset += len(value) + 1  # +1 for null terminator
    
    # Add strings
    for key in keys:
        mo_content.extend(key.encode('utf-8'))
        mo_content.append(0)  # null terminator
    
    for value in values:
        mo_content.extend(value.encode('utf-8'))
        mo_content.append(0)  # null terminator
    
    # Write the MO file
    with open(mo_file_path, 'wb') as f:
        f.write(mo_content)

def compile_translations():
    """Compile all .po files in the locale directory."""
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
                translations = parse_po_file(po_file)
                create_mo_file(translations, mo_file)
                print(f"Created {mo_file}")
            except Exception as e:
                print(f"Error compiling {po_file}: {e}")
        else:
            print(f"No .po file found in {lc_messages_dir}")

if __name__ == '__main__':
    compile_translations() 