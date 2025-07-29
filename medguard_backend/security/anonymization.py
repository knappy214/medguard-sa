"""
Data anonymization system for reporting and research compliance.

This module provides data anonymization utilities for HIPAA and POPIA compliance,
enabling safe data sharing for research and reporting purposes.
"""

import hashlib
import logging
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()
logger = logging.getLogger(__name__)


class DataAnonymizer:
    """
    Data anonymizer for medical data compliance.
    
    This class provides methods to anonymize sensitive medical data
    while preserving data utility for research and reporting.
    """
    
    def __init__(self):
        self.salt = getattr(settings, 'ANONYMIZATION_SALT', 'medguard_sa_salt')
        self.hash_algorithm = 'sha256'
    
    def anonymize_patient_data(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize patient data for research purposes.
        
        Args:
            patient_data: Dictionary containing patient data
            
        Returns:
            Anonymized patient data
        """
        anonymized_data = patient_data.copy()
        
        # Direct identifiers (remove completely)
        direct_identifiers = [
            'first_name', 'last_name', 'email', 'phone_number',
            'medical_record_number', 'emergency_contact_name',
            'emergency_contact_phone', 'primary_healthcare_provider',
            'healthcare_provider_phone'
        ]
        
        for identifier in direct_identifiers:
            if identifier in anonymized_data:
                del anonymized_data[identifier]
        
        # Quasi-identifiers (generalize or hash)
        if 'date_of_birth' in anonymized_data:
            anonymized_data['date_of_birth'] = self._generalize_date(
                anonymized_data['date_of_birth']
            )
        
        if 'gender' in anonymized_data:
            anonymized_data['gender'] = self._generalize_gender(
                anonymized_data['gender']
            )
        
        # Add anonymization metadata
        anonymized_data['_anonymized'] = True
        anonymized_data['_anonymized_at'] = timezone.now().isoformat()
        anonymized_data['_anonymization_method'] = 'k_anonymity'
        
        return anonymized_data
    
    def anonymize_medication_data(self, medication_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize medication data for research purposes.
        
        Args:
            medication_data: Dictionary containing medication data
            
        Returns:
            Anonymized medication data
        """
        anonymized_data = medication_data.copy()
        
        # Remove direct identifiers
        direct_identifiers = [
            'patient_id', 'user_id', 'prescribed_by', 'manufacturer'
        ]
        
        for identifier in direct_identifiers:
            if identifier in anonymized_data:
                del anonymized_data[identifier]
        
        # Generalize medication information
        if 'name' in anonymized_data:
            anonymized_data['name'] = self._generalize_medication_name(
                anonymized_data['name']
            )
        
        if 'strength' in anonymized_data:
            anonymized_data['strength'] = self._generalize_strength(
                anonymized_data['strength']
            )
        
        # Add anonymization metadata
        anonymized_data['_anonymized'] = True
        anonymized_data['_anonymized_at'] = timezone.now().isoformat()
        
        return anonymized_data
    
    def _generalize_date(self, date_value: Union[str, datetime]) -> str:
        """
        Generalize date to year range for k-anonymity.
        
        Args:
            date_value: Date to generalize
            
        Returns:
            Generalized date (year range)
        """
        if isinstance(date_value, str):
            try:
                date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except ValueError:
                return 'unknown'
        
        if isinstance(date_value, datetime):
            year = date_value.year
            # Group into 5-year ranges
            year_range_start = (year // 5) * 5
            year_range_end = year_range_start + 4
            return f"{year_range_start}-{year_range_end}"
        
        return 'unknown'
    
    def _generalize_gender(self, gender: str) -> str:
        """
        Generalize gender for privacy.
        
        Args:
            gender: Gender value
            
        Returns:
            Generalized gender
        """
        if gender in ['male', 'female']:
            return gender
        else:
            return 'other'
    
    def _generalize_medication_name(self, name: str) -> str:
        """
        Generalize medication name for privacy.
        
        Args:
            name: Medication name
            
        Returns:
            Generalized medication name
        """
        # Remove brand names, keep generic categories
        generic_categories = [
            'antibiotic', 'painkiller', 'antidepressant', 'antihistamine',
            'antihypertensive', 'diabetic', 'cardiac', 'respiratory'
        ]
        
        name_lower = name.lower()
        for category in generic_categories:
            if category in name_lower:
                return category
        
        return 'medication'
    
    def _generalize_strength(self, strength: str) -> str:
        """
        Generalize medication strength.
        
        Args:
            strength: Strength value
            
        Returns:
            Generalized strength
        """
        try:
            # Extract numeric value
            import re
            numbers = re.findall(r'\d+', strength)
            if numbers:
                value = int(numbers[0])
                if value < 10:
                    return 'low'
                elif value < 50:
                    return 'medium'
                else:
                    return 'high'
        except (ValueError, IndexError):
            pass
        
        return 'unknown'
    
    def hash_identifier(self, identifier: str, salt: str = None) -> str:
        """
        Hash an identifier with salt for consistent anonymization.
        
        Args:
            identifier: Identifier to hash
            salt: Salt for hashing (optional)
            
        Returns:
            Hashed identifier
        """
        if not identifier:
            return ''
        
        salt = salt or self.salt
        hash_obj = hashlib.new(self.hash_algorithm)
        hash_obj.update(f"{salt}:{identifier}".encode('utf-8'))
        return hash_obj.hexdigest()[:16]  # Return first 16 characters
    
    def generate_pseudonym(self, identifier: str) -> str:
        """
        Generate a pseudonym for an identifier.
        
        Args:
            identifier: Original identifier
            
        Returns:
            Pseudonym
        """
        hash_value = self.hash_identifier(identifier)
        return f"PSEUDO_{hash_value.upper()}"


class AnonymizedDataset(models.Model):
    """
    Model for storing anonymized datasets.
    
    This model tracks anonymized datasets for research and reporting,
    ensuring compliance with data retention and access policies.
    """
    
    # Dataset types
    class DatasetType(models.TextChoices):
        PATIENT_DATA = 'patient_data', _('Patient Data')
        MEDICATION_DATA = 'medication_data', _('Medication Data')
        AUDIT_DATA = 'audit_data', _('Audit Data')
        RESEARCH_DATA = 'research_data', _('Research Data')
        REPORTING_DATA = 'reporting_data', _('Reporting Data')
    
    # Anonymization methods
    class AnonymizationMethod(models.TextChoices):
        K_ANONYMITY = 'k_anonymity', _('K-Anonymity')
        L_DIVERSITY = 'l_diversity', _('L-Diversity')
        T_CLOSENESS = 't_closeness', _('T-Closeness')
        DIFFERENTIAL_PRIVACY = 'differential_privacy', _('Differential Privacy')
        HASHING = 'hashing', _('Hashing')
        GENERALIZATION = 'generalization', _('Generalization')
    
    # Status choices
    class Status(models.TextChoices):
        CREATED = 'created', _('Created')
        PROCESSING = 'processing', _('Processing')
        COMPLETED = 'completed', _('Completed')
        EXPIRED = 'expired', _('Expired')
        DELETED = 'deleted', _('Deleted')
    
    # Basic information
    name = models.CharField(
        max_length=200,
        help_text=_('Name of the anonymized dataset')
    )
    
    description = models.TextField(
        blank=True,
        help_text=_('Description of the dataset and its purpose')
    )
    
    dataset_type = models.CharField(
        max_length=20,
        choices=DatasetType.choices,
        help_text=_('Type of dataset')
    )
    
    anonymization_method = models.CharField(
        max_length=30,
        choices=AnonymizationMethod.choices,
        default=AnonymizationMethod.K_ANONYMITY,
        help_text=_('Method used for anonymization')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
        help_text=_('Current status of the dataset')
    )
    
    # Data information
    original_record_count = models.PositiveIntegerField(
        help_text=_('Number of records in original dataset')
    )
    
    anonymized_record_count = models.PositiveIntegerField(
        help_text=_('Number of records in anonymized dataset')
    )
    
    # Access control
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_datasets',
        help_text=_('User who created the dataset')
    )
    
    authorized_users = models.ManyToManyField(
        User,
        related_name='authorized_datasets',
        blank=True,
        help_text=_('Users authorized to access this dataset')
    )
    
    # Retention and expiration
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When the dataset was created')
    )
    
    expires_at = models.DateTimeField(
        help_text=_('When the dataset expires and should be deleted')
    )
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the dataset was deleted')
    )
    
    # Compliance information
    hipaa_compliant = models.BooleanField(
        default=True,
        help_text=_('Whether the dataset is HIPAA compliant')
    )
    
    popia_compliant = models.BooleanField(
        default=True,
        help_text=_('Whether the dataset is POPIA compliant')
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional metadata about the dataset')
    )
    
    # File storage
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text=_('Path to the anonymized dataset file')
    )
    
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Size of the dataset file in bytes')
    )
    
    class Meta:
        verbose_name = _('Anonymized Dataset')
        verbose_name_plural = _('Anonymized Datasets')
        db_table = 'security_anonymized_datasets'
        indexes = [
            models.Index(fields=['dataset_type', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['created_by']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_dataset_type_display()})"
    
    @property
    def is_expired(self) -> bool:
        """Check if dataset has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def days_until_expiry(self) -> int:
        """Calculate days until dataset expires."""
        if self.is_expired:
            return 0
        return (self.expires_at - timezone.now()).days
    
    def can_access(self, user: User) -> bool:
        """Check if user can access this dataset."""
        if user.is_superuser:
            return True
        
        if user == self.created_by:
            return True
        
        return user in self.authorized_users.all()
    
    def mark_deleted(self):
        """Mark dataset as deleted."""
        self.status = self.Status.DELETED
        self.deleted_at = timezone.now()
        self.save()


class DatasetAccessLog(models.Model):
    """
    Audit log for dataset access.
    
    This model tracks all access to anonymized datasets
    for compliance and security purposes.
    """
    
    # Access types
    class AccessType(models.TextChoices):
        VIEW = 'view', _('View')
        DOWNLOAD = 'download', _('Download')
        EXPORT = 'export', _('Export')
        DELETE = 'delete', _('Delete')
    
    dataset = models.ForeignKey(
        AnonymizedDataset,
        on_delete=models.CASCADE,
        related_name='access_logs',
        help_text=_('Dataset that was accessed')
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dataset_access_logs',
        help_text=_('User who accessed the dataset')
    )
    
    access_type = models.CharField(
        max_length=20,
        choices=AccessType.choices,
        help_text=_('Type of access')
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_('IP address of the access')
    )
    
    user_agent = models.TextField(
        blank=True,
        help_text=_('User agent string')
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When the access occurred')
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional metadata about the access')
    )
    
    class Meta:
        verbose_name = _('Dataset Access Log')
        verbose_name_plural = _('Dataset Access Logs')
        db_table = 'security_dataset_access_logs'
        indexes = [
            models.Index(fields=['dataset', 'user']),
            models.Index(fields=['access_type', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.access_type} - {self.dataset} ({self.timestamp})"


class AnonymizationService:
    """
    Service for managing data anonymization.
    
    This class provides high-level methods for creating and managing
    anonymized datasets for research and reporting.
    """
    
    def __init__(self):
        self.anonymizer = DataAnonymizer()
    
    def create_anonymized_dataset(
        self,
        name: str,
        dataset_type: str,
        data: List[Dict[str, Any]],
        created_by: User,
        expires_in_days: int = 365,
        authorized_users: List[User] = None,
        anonymization_method: str = 'k_anonymity'
    ) -> AnonymizedDataset:
        """
        Create an anonymized dataset.
        
        Args:
            name: Name of the dataset
            dataset_type: Type of dataset
            data: Original data to anonymize
            created_by: User creating the dataset
            expires_in_days: Days until dataset expires
            authorized_users: Users authorized to access dataset
            anonymization_method: Method for anonymization
            
        Returns:
            Created AnonymizedDataset instance
        """
        # Check permissions
        if not self._can_create_dataset(created_by, dataset_type):
            raise PermissionError("User not authorized to create datasets")
        
        # Anonymize data
        anonymized_data = []
        for record in data:
            if dataset_type == AnonymizedDataset.DatasetType.PATIENT_DATA:
                anonymized_record = self.anonymizer.anonymize_patient_data(record)
            elif dataset_type == AnonymizedDataset.DatasetType.MEDICATION_DATA:
                anonymized_record = self.anonymizer.anonymize_medication_data(record)
            else:
                anonymized_record = record  # No anonymization for other types
            
            anonymized_data.append(anonymized_record)
        
        # Create dataset record
        dataset = AnonymizedDataset.objects.create(
            name=name,
            dataset_type=dataset_type,
            anonymization_method=anonymization_method,
            original_record_count=len(data),
            anonymized_record_count=len(anonymized_data),
            created_by=created_by,
            expires_at=timezone.now() + timedelta(days=expires_in_days),
            metadata={
                'anonymization_parameters': {
                    'method': anonymization_method,
                    'salt': self.anonymizer.salt,
                },
                'data_schema': self._get_data_schema(anonymized_data),
            }
        )
        
        # Add authorized users
        if authorized_users:
            dataset.authorized_users.set(authorized_users)
        
        # Store anonymized data (implement file storage)
        self._store_anonymized_data(dataset, anonymized_data)
        
        # Log creation
        self._log_dataset_creation(dataset, created_by)
        
        return dataset
    
    def _can_create_dataset(self, user: User, dataset_type: str) -> bool:
        """Check if user can create datasets."""
        from security.permissions import get_user_permissions
        
        permission_manager = get_user_permissions(user)
        return permission_manager.can_anonymize_data()
    
    def _get_data_schema(self, data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Get schema of the anonymized data."""
        if not data:
            return {}
        
        schema = {}
        for key, value in data[0].items():
            if key.startswith('_'):  # Skip metadata fields
                continue
            schema[key] = type(value).__name__
        
        return schema
    
    def _store_anonymized_data(self, dataset: AnonymizedDataset, data: List[Dict[str, Any]]):
        """Store anonymized data to file."""
        import json
        import os
        
        # Create directory if it doesn't exist
        storage_dir = os.path.join(settings.MEDIA_ROOT, 'anonymized_datasets')
        os.makedirs(storage_dir, exist_ok=True)
        
        # Generate filename
        filename = f"dataset_{dataset.id}_{dataset.created_at.strftime('%Y%m%d_%H%M%S')}.json"
        file_path = os.path.join(storage_dir, filename)
        
        # Write data to file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        # Update dataset record
        dataset.file_path = file_path
        dataset.file_size = os.path.getsize(file_path)
        dataset.status = AnonymizedDataset.Status.COMPLETED
        dataset.save()
    
    def _log_dataset_creation(self, dataset: AnonymizedDataset, user: User):
        """Log dataset creation for audit."""
        from security.audit import log_audit_event, AuditLog
        
        log_audit_event(
            user=user,
            action=AuditLog.ActionType.CREATE,
            obj=dataset,
            description=f"Created anonymized dataset: {dataset.name}",
            severity=AuditLog.Severity.MEDIUM,
            metadata={
                'dataset_type': dataset.dataset_type,
                'record_count': dataset.anonymized_record_count,
                'anonymization_method': dataset.anonymization_method,
            }
        )
    
    def get_anonymized_data(self, dataset: AnonymizedDataset, user: User) -> List[Dict[str, Any]]:
        """
        Get anonymized data from dataset.
        
        Args:
            dataset: Dataset to access
            user: User requesting access
            
        Returns:
            Anonymized data
        """
        # Check access permissions
        if not dataset.can_access(user):
            raise PermissionError("User not authorized to access this dataset")
        
        # Log access
        self._log_dataset_access(dataset, user, DatasetAccessLog.AccessType.VIEW)
        
        # Load data from file
        if not dataset.file_path or not os.path.exists(dataset.file_path):
            raise FileNotFoundError("Dataset file not found")
        
        with open(dataset.file_path, 'r') as f:
            data = json.load(f)
        
        return data
    
    def _log_dataset_access(self, dataset: AnonymizedDataset, user: User, access_type: str):
        """Log dataset access."""
        DatasetAccessLog.objects.create(
            dataset=dataset,
            user=user,
            access_type=access_type,
            ip_address=self._get_client_ip(),
            user_agent=self._get_user_agent(),
        )
    
    def _get_client_ip(self) -> str:
        """Get client IP address."""
        # This would be implemented with request context
        return 'unknown'
    
    def _get_user_agent(self) -> str:
        """Get user agent string."""
        # This would be implemented with request context
        return 'unknown'


# Global service instance
_anonymization_service = None


def get_anonymization_service() -> AnonymizationService:
    """Get global anonymization service instance."""
    global _anonymization_service
    if _anonymization_service is None:
        _anonymization_service = AnonymizationService()
    return _anonymization_service 