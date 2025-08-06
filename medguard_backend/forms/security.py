"""
File upload security configuration for MedGuard SA forms.

This module provides security utilities for handling file uploads
in the Wagtail 7.0.2 form pages, including virus scanning,
file type validation, and encryption.
"""

import os
import hashlib
import mimetypes
import magic
from typing import List, Dict, Tuple, Optional
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

# File type security configuration
ALLOWED_FILE_TYPES = {
    'prescription': {
        'extensions': ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp'],
        'mime_types': [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/tiff',
            'image/bmp'
        ],
        'max_size': 10 * 1024 * 1024,  # 10MB
        'description': _('Prescription documents and images')
    },
    'medical_record': {
        'extensions': ['.pdf', '.doc', '.docx', '.txt'],
        'mime_types': [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ],
        'max_size': 20 * 1024 * 1024,  # 20MB
        'description': _('Medical records and documents')
    },
    'id_document': {
        'extensions': ['.pdf', '.jpg', '.jpeg', '.png'],
        'mime_types': [
            'application/pdf',
            'image/jpeg',
            'image/png'
        ],
        'max_size': 5 * 1024 * 1024,  # 5MB
        'description': _('Identity documents')
    },
    'transfer_document': {
        'extensions': ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'],
        'mime_types': [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'image/jpeg',
            'image/png'
        ],
        'max_size': 15 * 1024 * 1024,  # 15MB
        'description': _('Medication transfer documents')
    }
}

# Dangerous file extensions to block
DANGEROUS_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
    '.msi', '.dmg', '.app', '.sh', '.py', '.php', '.asp', '.aspx', '.jsp',
    '.pl', '.cgi', '.htaccess', '.htpasswd'
}

# MIME types that should be blocked
DANGEROUS_MIME_TYPES = {
    'application/x-executable',
    'application/x-msdownload',
    'application/x-msi',
    'application/x-dosexec',
    'application/x-msdos-program',
    'application/x-msi-installer',
    'application/x-apple-diskimage',
    'text/x-python',
    'text/x-php',
    'text/x-asp',
    'text/x-jsp'
}


class FileUploadSecurity:
    """
    Security handler for file uploads in MedGuard SA forms.
    
    Provides validation, virus scanning, and encryption for uploaded files.
    """
    
    def __init__(self, document_type: str = 'prescription'):
        """
        Initialize the file upload security handler.
        
        Args:
            document_type: Type of document being uploaded
        """
        self.document_type = document_type
        self.config = ALLOWED_FILE_TYPES.get(document_type, ALLOWED_FILE_TYPES['prescription'])
        
    def validate_file(self, uploaded_file: UploadedFile) -> Tuple[bool, List[str]]:
        """
        Validate an uploaded file for security and compliance.
        
        Args:
            uploaded_file: The uploaded file to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check file size
        if uploaded_file.size > self.config['max_size']:
            errors.append(
                _('File size exceeds maximum allowed size of {max_size}MB').format(
                    max_size=self.config['max_size'] // (1024 * 1024)
                )
            )
        
        # Check file extension
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if file_extension in DANGEROUS_EXTENSIONS:
            errors.append(_('File type is not allowed for security reasons'))
        elif file_extension not in self.config['extensions']:
            errors.append(
                _('File extension {extension} is not allowed. Allowed extensions: {allowed}').format(
                    extension=file_extension,
                    allowed=', '.join(self.config['extensions'])
                )
            )
        
        # Check MIME type
        try:
            # Read a small portion of the file to determine MIME type
            uploaded_file.seek(0)
            file_content = uploaded_file.read(2048)
            uploaded_file.seek(0)
            
            detected_mime = magic.from_buffer(file_content, mime=True)
            
            if detected_mime in DANGEROUS_MIME_TYPES:
                errors.append(_('File type is not allowed for security reasons'))
            elif detected_mime not in self.config['mime_types']:
                errors.append(
                    _('File type {mime_type} is not allowed. Allowed types: {allowed}').format(
                        mime_type=detected_mime,
                        allowed=', '.join(self.config['mime_types'])
                    )
                )
        except Exception as e:
            logger.warning(f"Could not determine MIME type for {uploaded_file.name}: {e}")
            errors.append(_('Could not verify file type. Please ensure the file is valid.'))
        
        # Check for malicious content patterns
        if self._contains_malicious_patterns(file_content):
            errors.append(_('File contains potentially malicious content'))
        
        return len(errors) == 0, errors
    
    def _contains_malicious_patterns(self, file_content: bytes) -> bool:
        """
        Check for malicious patterns in file content.
        
        Args:
            file_content: The file content to check
            
        Returns:
            True if malicious patterns are found
        """
        # Convert to string for pattern matching
        content_str = file_content.decode('utf-8', errors='ignore').lower()
        
        # Suspicious patterns
        suspicious_patterns = [
            'javascript:',
            'vbscript:',
            'data:text/html',
            'data:application/x-javascript',
            'eval(',
            'document.write(',
            'window.open(',
            'onload=',
            'onerror=',
            'onclick=',
            '<script',
            '<?php',
            '<%',
            'exec(',
            'system(',
            'shell_exec(',
            'passthru('
        ]
        
        return any(pattern in content_str for pattern in suspicious_patterns)
    
    def scan_for_viruses(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Scan a file for viruses using available antivirus software.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            Tuple of (is_clean, virus_name_if_found)
        """
        try:
            # Check if ClamAV is available
            if hasattr(settings, 'CLAMAV_ENABLED') and settings.CLAMAV_ENABLED:
                return self._scan_with_clamav(file_path)
            
            # Check if Windows Defender is available
            if os.name == 'nt':
                return self._scan_with_windows_defender(file_path)
            
            # For development/testing, assume clean
            logger.info(f"Virus scanning not available for {file_path}")
            return True, None
            
        except Exception as e:
            logger.error(f"Virus scanning failed for {file_path}: {e}")
            return False, str(e)
    
    def _scan_with_clamav(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Scan file using ClamAV antivirus.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            Tuple of (is_clean, virus_name_if_found)
        """
        try:
            import clamd
            
            # Connect to ClamAV daemon
            cd = clamd.ClamdUnixSocket()
            
            # Scan the file
            scan_result = cd.scan(file_path)
            
            if scan_result[file_path][0] == 'OK':
                return True, None
            else:
                return False, scan_result[file_path][1]
                
        except ImportError:
            logger.warning("ClamAV Python library not available")
            return True, None
        except Exception as e:
            logger.error(f"ClamAV scan failed: {e}")
            return False, str(e)
    
    def _scan_with_windows_defender(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Scan file using Windows Defender.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            Tuple of (is_clean, virus_name_if_found)
        """
        try:
            import subprocess
            
            # Run Windows Defender scan
            result = subprocess.run([
                'powershell',
                '-Command',
                f'Start-MpScan -ScanPath "{file_path}" -ScanType QuickScan'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, None
            else:
                return False, "Windows Defender scan failed"
                
        except Exception as e:
            logger.error(f"Windows Defender scan failed: {e}")
            return False, str(e)
    
    def encrypt_file(self, file_path: str) -> str:
        """
        Encrypt a file for secure storage.
        
        Args:
            file_path: Path to the file to encrypt
            
        Returns:
            Path to the encrypted file
        """
        try:
            from cryptography.fernet import Fernet
            
            # Generate or get encryption key
            key = getattr(settings, 'FILE_ENCRYPTION_KEY', None)
            if not key:
                key = Fernet.generate_key()
                logger.warning("No encryption key configured, using generated key")
            
            fernet = Fernet(key)
            
            # Read and encrypt file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            encrypted_data = fernet.encrypt(file_data)
            
            # Write encrypted file
            encrypted_path = f"{file_path}.encrypted"
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            
            return encrypted_path
            
        except ImportError:
            logger.warning("Cryptography library not available, skipping encryption")
            return file_path
        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            return file_path
    
    def generate_file_hash(self, file_path: str) -> str:
        """
        Generate SHA-256 hash of a file for integrity verification.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash of the file
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to prevent path traversal and other security issues.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        import re
        
        # Remove path traversal attempts
        filename = os.path.basename(filename)
        
        # Remove or replace dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        # Ensure filename is not empty
        if not filename.strip():
            filename = 'uploaded_file'
        
        return filename


def validate_uploaded_file(uploaded_file: UploadedFile, document_type: str = 'prescription') -> Tuple[bool, List[str]]:
    """
    Convenience function to validate an uploaded file.
    
    Args:
        uploaded_file: The uploaded file to validate
        document_type: Type of document being uploaded
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    security = FileUploadSecurity(document_type)
    return security.validate_file(uploaded_file)


def process_uploaded_file(uploaded_file: UploadedFile, document_type: str = 'prescription') -> Dict[str, any]:
    """
    Process an uploaded file with full security validation.
    
    Args:
        uploaded_file: The uploaded file to process
        document_type: Type of document being uploaded
        
    Returns:
        Dictionary containing processing results
    """
    security = FileUploadSecurity(document_type)
    
    # Validate file
    is_valid, errors = security.validate_file(uploaded_file)
    
    if not is_valid:
        return {
            'success': False,
            'errors': errors,
            'file_path': None,
            'file_hash': None,
            'encrypted_path': None
        }
    
    # Save file temporarily
    temp_path = f"/tmp/{security.sanitize_filename(uploaded_file.name)}"
    with open(temp_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    
    # Generate file hash
    file_hash = security.generate_file_hash(temp_path)
    
    # Scan for viruses
    is_clean, virus_info = security.scan_for_viruses(temp_path)
    
    if not is_clean:
        os.remove(temp_path)
        return {
            'success': False,
            'errors': [f"Virus detected: {virus_info}"],
            'file_path': None,
            'file_hash': None,
            'encrypted_path': None
        }
    
    # Encrypt file
    encrypted_path = security.encrypt_file(temp_path)
    
    return {
        'success': True,
        'errors': [],
        'file_path': temp_path,
        'file_hash': file_hash,
        'encrypted_path': encrypted_path,
        'original_name': uploaded_file.name,
        'file_size': uploaded_file.size,
        'mime_type': uploaded_file.content_type
    } 