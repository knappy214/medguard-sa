#!/usr/bin/env python3
"""
Script to clean up duplicate message IDs in .po files.
"""

import os
import re
from pathlib import Path

def clean_po_file(file_path):
    """Remove duplicate message IDs from a .po file."""
    print(f"Cleaning {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into message blocks
    blocks = re.split(r'\n(?=msgid )', content)
    
    # Keep track of seen message IDs
    seen_msgids = set()
    cleaned_blocks = []
    
    for block in blocks:
        if not block.strip():
            continue
            
        # Extract msgid
        msgid_match = re.search(r'^msgid "(.*?)"', block, re.MULTILINE | re.DOTALL)
        if not msgid_match:
            cleaned_blocks.append(block)
            continue
            
        msgid = msgid_match.group(1)
        
        # Skip if we've seen this msgid before
        if msgid in seen_msgids:
            print(f"  Removing duplicate: {msgid}")
            continue
            
        seen_msgids.add(msgid)
        cleaned_blocks.append(block)
    
    # Reconstruct the file
    cleaned_content = '\n'.join(cleaned_blocks)
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f"  Cleaned {file_path} - removed {len(blocks) - len(cleaned_blocks)} duplicates")

def main():
    """Clean all .po files in the locale directory."""
    locale_dir = Path('locale')
    
    if not locale_dir.exists():
        print("Locale directory not found!")
        return
    
    # Find all .po files
    po_files = list(locale_dir.rglob('*.po'))
    
    if not po_files:
        print("No .po files found!")
        return
    
    print(f"Found {len(po_files)} .po files to clean:")
    
    for po_file in po_files:
        clean_po_file(po_file)
    
    print("\nAll .po files cleaned!")

if __name__ == '__main__':
    main() 