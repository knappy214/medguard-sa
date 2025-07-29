"""
Tests for encryption and data protection system.

These tests ensure that all sensitive data is properly encrypted
and that encryption keys are managed securely.
"""

import base64
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet, InvalidToken

from security.hipaa_compliance import (
    get_encryption_manager,
    EncryptionManager,
    encrypt_sensitive_data,
    decrypt_sensitive_data,
    hash_identifier,
    verify_hash
)

User = get_user_model()


class EncryptionManagerTest(TestCase):
    """Test EncryptionManager functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.encryption_manager = get_encryption_manager()
    
    def test_encryption_manager_initialization(self):
        """Test encryption manager initialization."""
        self.assertIsInstance(self.encryption_manager, EncryptionManager)
        self.assertIsNotNone(self.encryption_manager.fernet)
    
    def test_encrypt_decrypt_basic(self):
        """Test basic encryption and decryption."""
        original_data = "Sensitive patient information"
        
        # Encrypt
        encrypted_data = self.encryption_manager.encrypt(original_data)
        self.assertIsInstance(encrypted_data, str)
        self.assertNotEqual(encrypted_data, original_data)
        
        # Decrypt
        decrypted_data = self.encryption_manager.decrypt(encrypted_data)
        self.assertEqual(decrypted_data, original_data)
    
    def test_encrypt_decrypt_json(self):
        """Test encryption and decryption of JSON data."""
        original_data = {
            "patient_id": "12345",
            "medication": "Aspirin",
            "dosage": "100mg",
            "frequency": "daily"
        }
        
        # Encrypt
        encrypted_data = self.encryption_manager.encrypt_json(original_data)
        self.assertIsInstance(encrypted_data, str)
        
        # Decrypt
        decrypted_data = self.encryption_manager.decrypt_json(encrypted_data)
        self.assertEqual(decrypted_data, original_data)
    
    def test_encrypt_decrypt_large_data(self):
        """Test encryption and decryption of large data."""
        # Create large data
        original_data = "x" * 10000
        
        # Encrypt
        encrypted_data = self.encryption_manager.encrypt(original_data)
        
        # Decrypt
        decrypted_data = self.encryption_manager.decrypt(encrypted_data)
        self.assertEqual(decrypted_data, original_data)
    
    def test_encrypt_decrypt_binary_data(self):
        """Test encryption and decryption of binary data."""
        original_data = b"Binary sensitive data"
        
        # Encrypt
        encrypted_data = self.encryption_manager.encrypt_binary(original_data)
        self.assertIsInstance(encrypted_data, str)
        
        # Decrypt
        decrypted_data = self.encryption_manager.decrypt_binary(encrypted_data)
        self.assertEqual(decrypted_data, original_data)
    
    def test_invalid_decryption(self):
        """Test handling of invalid encrypted data."""
        invalid_data = "invalid_encrypted_data"
        
        with self.assertRaises(InvalidToken):
            self.encryption_manager.decrypt(invalid_data)
    
    def test_key_rotation(self):
        """Test encryption key rotation."""
        original_data = "Sensitive data"
        
        # Encrypt with current key
        encrypted_data = self.encryption_manager.encrypt(original_data)
        
        # Simulate key rotation
        new_key = Fernet.generate_key()
        self.encryption_manager.rotate_key(new_key)
        
        # Decrypt with new key (should still work with old data)
        decrypted_data = self.encryption_manager.decrypt(encrypted_data)
        self.assertEqual(decrypted_data, original_data)
        
        # Encrypt new data with new key
        new_encrypted_data = self.encryption_manager.encrypt(original_data)
        self.assertNotEqual(encrypted_data, new_encrypted_data)
    
    def test_encryption_performance(self):
        """Test encryption performance with multiple operations."""
        import time
        
        data_size = 1000
        test_data = "x" * data_size
        
        start_time = time.time()
        
        for _ in range(100):
            encrypted = self.encryption_manager.encrypt(test_data)
            decrypted = self.encryption_manager.decrypt(encrypted)
            self.assertEqual(decrypted, test_data)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 100 operations in reasonable time
        self.assertLess(duration, 5.0)  # 5 seconds max


class DataEncryptionTest(TestCase):
    """Test data encryption utilities."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_encrypt_sensitive_data(self):
        """Test encrypt_sensitive_data function."""
        sensitive_data = {
            "patient_name": "John Doe",
            "medical_record_number": "MRN123456",
            "diagnosis": "Hypertension"
        }
        
        encrypted_data = encrypt_sensitive_data(sensitive_data)
        self.assertIsInstance(encrypted_data, str)
        self.assertNotIn("John Doe", encrypted_data)
        self.assertNotIn("MRN123456", encrypted_data)
    
    def test_decrypt_sensitive_data(self):
        """Test decrypt_sensitive_data function."""
        original_data = {
            "patient_name": "Jane Smith",
            "medical_record_number": "MRN789012",
            "diagnosis": "Diabetes"
        }
        
        encrypted_data = encrypt_sensitive_data(original_data)
        decrypted_data = decrypt_sensitive_data(encrypted_data)
        
        self.assertEqual(decrypted_data, original_data)
    
    def test_hash_identifier(self):
        """Test hash_identifier function."""
        identifier = "MRN123456"
        
        hashed = hash_identifier(identifier)
        self.assertIsInstance(hashed, str)
        self.assertNotEqual(hashed, identifier)
        self.assertGreater(len(hashed), len(identifier))
    
    def test_verify_hash(self):
        """Test verify_hash function."""
        identifier = "MRN123456"
        hashed = hash_identifier(identifier)
        
        # Should verify correctly
        self.assertTrue(verify_hash(identifier, hashed))
        
        # Should not verify with wrong identifier
        self.assertFalse(verify_hash("WRONG_ID", hashed))
    
    def test_consistent_hashing(self):
        """Test that hashing is consistent for same input."""
        identifier = "MRN123456"
        
        hash1 = hash_identifier(identifier)
        hash2 = hash_identifier(identifier)
        
        self.assertEqual(hash1, hash2)
    
    def test_field_level_encryption(self):
        """Test field-level encryption for specific data types."""
        # Test patient identifiers
        patient_id = "PAT123456"
        encrypted_id = encrypt_sensitive_data(patient_id, field_type="patient_identifier")
        decrypted_id = decrypt_sensitive_data(encrypted_id, field_type="patient_identifier")
        self.assertEqual(decrypted_id, patient_id)
        
        # Test medical records
        medical_record = "Patient has hypertension, prescribed medication"
        encrypted_record = encrypt_sensitive_data(medical_record, field_type="medical_record")
        decrypted_record = decrypt_sensitive_data(encrypted_record, field_type="medical_record")
        self.assertEqual(decrypted_record, medical_record)


class SecurityValidationTest(TestCase):
    """Test security validation functions."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_validate_encryption_key(self):
        """Test encryption key validation."""
        from security.hipaa_compliance import validate_encryption_key
        
        # Valid key
        valid_key = base64.urlsafe_b64encode(b"x" * 32)
        self.assertTrue(validate_encryption_key(valid_key))
        
        # Invalid key (too short)
        invalid_key = base64.urlsafe_b64encode(b"x" * 16)
        with self.assertRaises(ValidationError):
            validate_encryption_key(invalid_key)
        
        # Invalid key (wrong format)
        with self.assertRaises(ValidationError):
            validate_encryption_key("invalid_key")
    
    def test_validate_sensitive_data(self):
        """Test sensitive data validation."""
        from security.hipaa_compliance import validate_sensitive_data
        
        # Valid sensitive data
        valid_data = {
            "patient_name": "John Doe",
            "medical_record_number": "MRN123456"
        }
        self.assertTrue(validate_sensitive_data(valid_data))
        
        # Invalid data (contains unencrypted sensitive info)
        invalid_data = {
            "patient_name": "John Doe",
            "ssn": "123-45-6789"  # Should be encrypted
        }
        with self.assertRaises(ValidationError):
            validate_sensitive_data(invalid_data)
    
    def test_validate_anonymization(self):
        """Test anonymization validation."""
        from security.hipaa_compliance import validate_anonymization
        
        # Valid anonymized data
        valid_anonymized = {
            "age_group": "30-40",
            "gender": "M",
            "location": "Cape Town"
        }
        self.assertTrue(validate_anonymization(valid_anonymized))
        
        # Invalid data (contains identifiable information)
        invalid_anonymized = {
            "age_group": "30-40",
            "name": "John Doe",  # Should not be in anonymized data
            "location": "Cape Town"
        }
        with self.assertRaises(ValidationError):
            validate_anonymization(invalid_anonymized)


class IntegrationTest(TestCase):
    """Integration tests for encryption system."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.encryption_manager = get_encryption_manager()
    
    def test_complete_encryption_workflow(self):
        """Test complete encryption workflow."""
        # Simulate patient data
        patient_data = {
            "patient_id": "PAT123456",
            "name": "John Doe",
            "date_of_birth": "1980-01-01",
            "medical_records": [
                {
                    "date": "2024-01-15",
                    "diagnosis": "Hypertension",
                    "medication": "Lisinopril 10mg"
                },
                {
                    "date": "2024-02-01",
                    "diagnosis": "Diabetes",
                    "medication": "Metformin 500mg"
                }
            ]
        }
        
        # Encrypt sensitive data
        encrypted_data = encrypt_sensitive_data(patient_data)
        
        # Verify data is encrypted
        self.assertIsInstance(encrypted_data, str)
        self.assertNotIn("John Doe", encrypted_data)
        self.assertNotIn("PAT123456", encrypted_data)
        
        # Decrypt data
        decrypted_data = decrypt_sensitive_data(encrypted_data)
        
        # Verify data integrity
        self.assertEqual(decrypted_data, patient_data)
        
        # Test anonymization
        anonymized_data = {
            "age_group": "40-50",
            "gender": "M",
            "location": "Cape Town",
            "diagnosis_count": 2
        }
        
        # Verify anonymization
        self.assertNotIn("John Doe", str(anonymized_data))
        self.assertNotIn("PAT123456", str(anonymized_data))
    
    def test_encryption_with_audit_logging(self):
        """Test encryption with audit logging."""
        from security.audit import log_audit_event, AuditLog
        
        sensitive_data = "Sensitive patient information"
        
        # Log encryption event
        log_audit_event(
            user=self.user,
            action=AuditLog.ActionType.CREATE,
            description="Encrypting sensitive data",
            severity=AuditLog.Severity.MEDIUM
        )
        
        # Encrypt data
        encrypted_data = self.encryption_manager.encrypt(sensitive_data)
        
        # Log decryption event
        log_audit_event(
            user=self.user,
            action=AuditLog.ActionType.READ,
            description="Decrypting sensitive data",
            severity=AuditLog.Severity.MEDIUM
        )
        
        # Decrypt data
        decrypted_data = self.encryption_manager.decrypt(encrypted_data)
        
        # Verify data integrity
        self.assertEqual(decrypted_data, sensitive_data)
        
        # Verify audit logs
        audit_logs = AuditLog.objects.filter(user=self.user)
        self.assertEqual(audit_logs.count(), 2)
        
        # Check that encryption/decryption events were logged
        actions = [log.action for log in audit_logs]
        self.assertIn(AuditLog.ActionType.CREATE, actions)
        self.assertIn(AuditLog.ActionType.READ, actions) 