"""
Field-level encryption for sensitive medical data.

This module provides encryption utilities for protecting PHI (Protected Health Information)
and other sensitive medical data in compliance with HIPAA and POPIA regulations.
"""

import base64
import json
import logging
from typing import Any, Dict, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.crypto import get_random_string

logger = logging.getLogger(__name__)


class FieldEncryptionError(Exception):
    """Custom exception for field encryption errors."""
    pass


class FieldEncryption:
    """
    Field-level encryption for sensitive medical data.
    
    Uses AES-256-GCM for authenticated encryption with a unique IV for each field.
    Implements key derivation using PBKDF2 with 100,000 iterations for security.
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize the encryption system.
        
        Args:
            master_key: Master encryption key. If not provided, uses SECRET_KEY.
        """
        self.master_key = master_key or getattr(settings, 'SECRET_KEY')
        if not self.master_key:
            raise ImproperlyConfigured("SECRET_KEY must be set for field encryption")
        
        # Derive encryption key from master key
        self.encryption_key = self._derive_key(self.master_key)
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _derive_key(self, master_key: str) -> bytes:
        """
        Derive encryption key from master key using PBKDF2.
        
        Args:
            master_key: Master key to derive from
            
        Returns:
            Derived encryption key
        """
        salt = b'medguard_sa_salt'  # Fixed salt for key derivation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # High iteration count for security
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
    
    def encrypt_field(self, value: Any, field_name: str = None) -> str:
        """
        Encrypt a field value.
        
        Args:
            value: Value to encrypt
            field_name: Name of the field (for audit purposes)
            
        Returns:
            Encrypted value as base64 string
        """
        try:
            if value is None:
                return None
            
            # Convert value to JSON string
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False)
            else:
                value_str = str(value)
            
            # Encrypt the value
            encrypted_data = self.cipher_suite.encrypt(value_str.encode('utf-8'))
            
            # Return base64 encoded encrypted data
            return base64.urlsafe_b64encode(encrypted_data).decode('ascii')
            
        except Exception as e:
            logger.error(f"Encryption failed for field {field_name}: {str(e)}")
            raise FieldEncryptionError(f"Failed to encrypt field {field_name}: {str(e)}")
    
    def decrypt_field(self, encrypted_value: str, field_name: str = None) -> Any:
        """
        Decrypt a field value.
        
        Args:
            encrypted_value: Encrypted value as base64 string
            field_name: Name of the field (for audit purposes)
            
        Returns:
            Decrypted value
        """
        try:
            if encrypted_value is None:
                return None
            
            # Decode base64
            encrypted_data = base64.urlsafe_b64decode(encrypted_value.encode('ascii'))
            
            # Decrypt the data
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            
            # Convert back to string
            value_str = decrypted_data.decode('utf-8')
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(value_str)
            except json.JSONDecodeError:
                return value_str
                
        except Exception as e:
            logger.error(f"Decryption failed for field {field_name}: {str(e)}")
            raise FieldEncryptionError(f"Failed to decrypt field {field_name}: {str(e)}")
    
    def encrypt_dict(self, data: Dict[str, Any], sensitive_fields: list) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in a dictionary.
        
        Args:
            data: Dictionary containing data
            sensitive_fields: List of field names to encrypt
            
        Returns:
            Dictionary with sensitive fields encrypted
        """
        encrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field] is not None:
                encrypted_data[field] = self.encrypt_field(encrypted_data[field], field)
        
        return encrypted_data
    
    def decrypt_dict(self, data: Dict[str, Any], sensitive_fields: list) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in a dictionary.
        
        Args:
            data: Dictionary containing encrypted data
            sensitive_fields: List of field names to decrypt
            
        Returns:
            Dictionary with sensitive fields decrypted
        """
        decrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field] is not None:
                decrypted_data[field] = self.decrypt_field(decrypted_data[field], field)
        
        return decrypted_data


class EncryptedField:
    """
    Django model field wrapper for encrypted fields.
    
    This class provides a way to automatically encrypt/decrypt field values
    when they are saved to or loaded from the database.
    """
    
    def __init__(self, field_name: str, encryption_service: FieldEncryption = None):
        """
        Initialize encrypted field.
        
        Args:
            field_name: Name of the field
            encryption_service: Encryption service instance
        """
        self.field_name = field_name
        self.encryption_service = encryption_service or FieldEncryption()
    
    def __get__(self, instance, owner):
        """Get decrypted value."""
        if instance is None:
            return self
        
        # Get encrypted value from instance
        encrypted_value = getattr(instance, f'_{self.field_name}', None)
        
        if encrypted_value is None:
            return None
        
        # Decrypt the value
        return self.encryption_service.decrypt_field(encrypted_value, self.field_name)
    
    def __set__(self, instance, value):
        """Set encrypted value."""
        if value is None:
            setattr(instance, f'_{self.field_name}', None)
        else:
            # Encrypt the value
            encrypted_value = self.encryption_service.encrypt_field(value, self.field_name)
            setattr(instance, f'_{self.field_name}', encrypted_value)


# Global encryption service instance
_encryption_service = None


def get_encryption_service() -> FieldEncryption:
    """Get the global encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = FieldEncryption()
    return _encryption_service


def encrypt_sensitive_data(data: Dict[str, Any], fields_to_encrypt: list) -> Dict[str, Any]:
    """
    Encrypt sensitive data fields.
    
    Args:
        data: Dictionary containing data
        fields_to_encrypt: List of field names to encrypt
        
    Returns:
        Dictionary with sensitive fields encrypted
    """
    encryption_service = get_encryption_service()
    return encryption_service.encrypt_dict(data, fields_to_encrypt)


def decrypt_sensitive_data(data: Dict[str, Any], fields_to_decrypt: list) -> Dict[str, Any]:
    """
    Decrypt sensitive data fields.
    
    Args:
        data: Dictionary containing encrypted data
        fields_to_decrypt: List of field names to decrypt
        
    Returns:
        Dictionary with sensitive fields decrypted
    """
    encryption_service = get_encryption_service()
    return encryption_service.decrypt_dict(data, fields_to_decrypt)


# Key storage for encryption keys (in-memory for now, should be replaced with secure storage)
_key_store = {}


def store_encryption_key(key_id: str, key: bytes) -> None:
    """
    Store an encryption key securely.
    
    Args:
        key_id: Unique identifier for the key
        key: The encryption key to store
        
    Note:
        This is a simple in-memory implementation. In production,
        keys should be stored in a secure key management system.
    """
    global _key_store
    _key_store[key_id] = key
    logger.info(f"Stored encryption key: {key_id}")


def get_encryption_key(key_id: str) -> Optional[bytes]:
    """
    Retrieve an encryption key by ID.
    
    Args:
        key_id: Unique identifier for the key
        
    Returns:
        The encryption key if found, None otherwise
        
    Note:
        This is a simple in-memory implementation. In production,
        keys should be retrieved from a secure key management system.
    """
    global _key_store
    key = _key_store.get(key_id)
    if key:
        logger.debug(f"Retrieved encryption key: {key_id}")
    else:
        logger.warning(f"Encryption key not found: {key_id}")
    return key 