"""
Secure document management using Wagtail 7.0.2's document privacy controls.

This module provides healthcare-specific document privacy controls including:
- Role-based document access
- Patient consent tracking
- Audit trails for document access
- Encryption for sensitive documents
- HIPAA-compliant document handling
"""

import logging
from typing import Optional, List, Dict, Any
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from wagtail.documents.models import Document
from wagtail.documents.permissions import permission_policy
from wagtail.permission_policies import ModelPermissionPolicy

from .models import SecurityEvent, DocumentAccessLog, PatientConsent
from .encryption import encrypt_document_content, decrypt_document_content
from .audit import log_security_event

logger = logging.getLogger(__name__)
User = get_user_model()


class HealthcareDocumentPrivacyMixin:
    """
    Mixin for healthcare document privacy controls.
    
    Provides HIPAA-compliant document access controls and audit trails.
    """
    
    # Document privacy levels
    PRIVACY_PUBLIC = 'public'
    PRIVACY_INTERNAL = 'internal'
    PRIVACY_CONFIDENTIAL = 'confidential'
    PRIVACY_RESTRICTED = 'restricted'
    
    # Healthcare document types
    DOC_TYPE_PRESCRIPTION = 'prescription'
    DOC_TYPE_MEDICAL_RECORD = 'medical_record'
    DOC_TYPE_LAB_RESULT = 'lab_result'
    DOC_TYPE_CONSENT_FORM = 'consent_form'
    DOC_TYPE_ADMINISTRATIVE = 'administrative'
    
    class Meta:
        abstract = True
    
    def get_privacy_level(self) -> str:
        """Get document privacy level based on content and metadata."""
        if hasattr(self, 'privacy_level'):
            return self.privacy_level
        return self.PRIVACY_INTERNAL
    
    def get_required_permissions(self) -> List[str]:
        """Get required permissions for document access."""
        privacy_level = self.get_privacy_level()
        
        if privacy_level == self.PRIVACY_PUBLIC:
            return ['security.view_public_documents']
        elif privacy_level == self.PRIVACY_INTERNAL:
            return ['security.view_internal_documents']
        elif privacy_level == self.PRIVACY_CONFIDENTIAL:
            return ['security.view_confidential_documents']
        elif privacy_level == self.PRIVACY_RESTRICTED:
            return ['security.view_restricted_documents']
        
        return ['security.view_documents']
    
    def requires_patient_consent(self) -> bool:
        """Check if document requires patient consent for access."""
        return self.get_privacy_level() in [
            self.PRIVACY_CONFIDENTIAL, 
            self.PRIVACY_RESTRICTED
        ]


class SecureDocumentManager(models.Manager):
    """
    Manager for secure document operations with privacy controls.
    """
    
    def get_accessible_documents(self, user: User, patient_id: Optional[int] = None) -> models.QuerySet:
        """
        Get documents accessible to user based on permissions and patient consent.
        
        Args:
            user: The user requesting access
            patient_id: Optional patient ID for patient-specific documents
            
        Returns:
            QuerySet of accessible documents
        """
        if not user.is_authenticated:
            return self.none()
        
        # Get user permissions
        user_permissions = user.get_all_permissions()
        
        # Base queryset
        queryset = self.get_queryset()
        
        # Filter by privacy level based on permissions
        accessible_levels = []
        
        if 'security.view_public_documents' in user_permissions:
            accessible_levels.append(HealthcareDocumentPrivacyMixin.PRIVACY_PUBLIC)
        
        if 'security.view_internal_documents' in user_permissions:
            accessible_levels.append(HealthcareDocumentPrivacyMixin.PRIVACY_INTERNAL)
        
        if 'security.view_confidential_documents' in user_permissions:
            accessible_levels.append(HealthcareDocumentPrivacyMixin.PRIVACY_CONFIDENTIAL)
        
        if 'security.view_restricted_documents' in user_permissions:
            accessible_levels.append(HealthcareDocumentPrivacyMixin.PRIVACY_RESTRICTED)
        
        if not accessible_levels:
            return self.none()
        
        # Filter by privacy level
        queryset = queryset.filter(privacy_level__in=accessible_levels)
        
        # Filter by patient consent if required
        if patient_id:
            queryset = self._filter_by_patient_consent(queryset, user, patient_id)
        
        return queryset
    
    def _filter_by_patient_consent(self, queryset: models.QuerySet, user: User, patient_id: int) -> models.QuerySet:
        """Filter documents by patient consent requirements."""
        # Get documents that require consent
        consent_required_docs = queryset.filter(
            privacy_level__in=[
                HealthcareDocumentPrivacyMixin.PRIVACY_CONFIDENTIAL,
                HealthcareDocumentPrivacyMixin.PRIVACY_RESTRICTED
            ]
        )
        
        # Check patient consent for these documents
        consented_docs = []
        for doc in consent_required_docs:
            if self._has_patient_consent(user, patient_id, doc):
                consented_docs.append(doc.id)
        
        # Combine non-consent-required docs with consented docs
        non_consent_docs = queryset.exclude(
            privacy_level__in=[
                HealthcareDocumentPrivacyMixin.PRIVACY_CONFIDENTIAL,
                HealthcareDocumentPrivacyMixin.PRIVACY_RESTRICTED
            ]
        )
        
        return queryset.filter(
            models.Q(id__in=consented_docs) | 
            models.Q(id__in=non_consent_docs.values_list('id', flat=True))
        )
    
    def _has_patient_consent(self, user: User, patient_id: int, document) -> bool:
        """Check if user has patient consent for document access."""
        try:
            consent = PatientConsent.objects.get(
                patient_id=patient_id,
                document_type=document.get_document_type(),
                user=user,
                is_active=True,
                expires_at__gt=timezone.now()
            )
            return consent.is_granted
        except PatientConsent.DoesNotExist:
            return False


class SecureDocument(Document, HealthcareDocumentPrivacyMixin):
    """
    Secure document model with healthcare privacy controls.
    
    Extends Wagtail's Document model with HIPAA-compliant features.
    """
    
    # Privacy and access control fields
    privacy_level = models.CharField(
        max_length=20,
        choices=[
            (HealthcareDocumentPrivacyMixin.PRIVACY_PUBLIC, _('Public')),
            (HealthcareDocumentPrivacyMixin.PRIVACY_INTERNAL, _('Internal')),
            (HealthcareDocumentPrivacyMixin.PRIVACY_CONFIDENTIAL, _('Confidential')),
            (HealthcareDocumentPrivacyMixin.PRIVACY_RESTRICTED, _('Restricted')),
        ],
        default=HealthcareDocumentPrivacyMixin.PRIVACY_INTERNAL,
        help_text=_('Document privacy level for access control')
    )
    
    document_type = models.CharField(
        max_length=50,
        choices=[
            (HealthcareDocumentPrivacyMixin.DOC_TYPE_PRESCRIPTION, _('Prescription')),
            (HealthcareDocumentPrivacyMixin.DOC_TYPE_MEDICAL_RECORD, _('Medical Record')),
            (HealthcareDocumentPrivacyMixin.DOC_TYPE_LAB_RESULT, _('Lab Result')),
            (HealthcareDocumentPrivacyMixin.DOC_TYPE_CONSENT_FORM, _('Consent Form')),
            (HealthcareDocumentPrivacyMixin.DOC_TYPE_ADMINISTRATIVE, _('Administrative')),
        ],
        help_text=_('Type of healthcare document')
    )
    
    patient_id = models.IntegerField(
        null=True, 
        blank=True,
        help_text=_('Patient ID if document is patient-specific')
    )
    
    encrypted_content = models.BinaryField(
        null=True,
        blank=True,
        help_text=_('Encrypted document content for sensitive documents')
    )
    
    encryption_key_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_('ID of encryption key used for this document')
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_documents'
    )
    
    last_accessed = models.DateTimeField(
        null=True,
        blank=True
    )
    
    access_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of times document has been accessed')
    )
    
    # Metadata
    tags = models.JSONField(
        default=dict,
        help_text=_('Document tags for categorization')
    )
    
    objects = SecureDocumentManager()
    
    class Meta:
        verbose_name = _('Secure Document')
        verbose_name_plural = _('Secure Documents')
        permissions = [
            ('view_public_documents', _('Can view public documents')),
            ('view_internal_documents', _('Can view internal documents')),
            ('view_confidential_documents', _('Can view confidential documents')),
            ('view_restricted_documents', _('Can view restricted documents')),
            ('encrypt_documents', _('Can encrypt documents')),
            ('decrypt_documents', _('Can decrypt documents')),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_privacy_level_display()})"
    
    def get_document_type(self) -> str:
        """Get document type."""
        return self.document_type
    
    def is_encrypted(self) -> bool:
        """Check if document content is encrypted."""
        return bool(self.encrypted_content and self.encryption_key_id)
    
    def encrypt_content(self, content: bytes, user: User) -> bool:
        """
        Encrypt document content.
        
        Args:
            content: Document content to encrypt
            user: User performing encryption
            
        Returns:
            True if encryption successful
        """
        try:
            encrypted_data, key_id = encrypt_document_content(content)
            self.encrypted_content = encrypted_data
            self.encryption_key_id = key_id
            self.save(update_fields=['encrypted_content', 'encryption_key_id'])
            
            # Log encryption event
            log_security_event(
                user=user,
                event_type='document_encrypted',
                target_object=self,
                details={'document_id': self.id, 'privacy_level': self.privacy_level}
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to encrypt document {self.id}: {e}")
            return False
    
    def decrypt_content(self, user: User) -> Optional[bytes]:
        """
        Decrypt document content.
        
        Args:
            user: User requesting decryption
            
        Returns:
            Decrypted content or None if failed
        """
        if not self.is_encrypted():
            return None
        
        try:
            # Check access permissions
            if not self.can_access(user):
                raise PermissionDenied("User does not have permission to access this document")
            
            # Decrypt content
            decrypted_content = decrypt_document_content(
                self.encrypted_content, 
                self.encryption_key_id
            )
            
            # Log access
            self._log_document_access(user)
            
            return decrypted_content
        except Exception as e:
            logger.error(f"Failed to decrypt document {self.id}: {e}")
            return None
    
    def can_access(self, user: User) -> bool:
        """
        Check if user can access this document.
        
        Args:
            user: User to check access for
            
        Returns:
            True if user can access document
        """
        if not user.is_authenticated:
            return False
        
        # Check basic permissions
        required_permissions = self.get_required_permissions()
        if not user.has_perms(required_permissions):
            return False
        
        # Check patient consent if required
        if self.requires_patient_consent() and self.patient_id:
            return self._check_patient_consent(user, self.patient_id)
        
        return True
    
    def _check_patient_consent(self, user: User, patient_id: int) -> bool:
        """Check patient consent for document access."""
        try:
            consent = PatientConsent.objects.get(
                patient_id=patient_id,
                document_type=self.document_type,
                user=user,
                is_active=True,
                expires_at__gt=timezone.now()
            )
            return consent.is_granted
        except PatientConsent.DoesNotExist:
            return False
    
    def _log_document_access(self, user: User):
        """Log document access for audit purposes."""
        self.last_accessed = timezone.now()
        self.access_count += 1
        self.save(update_fields=['last_accessed', 'access_count'])
        
        # Create access log entry
        DocumentAccessLog.objects.create(
            document=self,
            user=user,
            access_type='view',
            ip_address=getattr(user, 'last_ip', None),
            user_agent=getattr(user, 'user_agent', None)
        )
        
        # Log security event
        log_security_event(
            user=user,
            event_type='document_accessed',
            target_object=self,
            details={
                'document_id': self.id,
                'privacy_level': self.privacy_level,
                'access_count': self.access_count
            }
        )


class DocumentAccessLog(models.Model):
    """
    Audit log for document access events.
    """
    
    document = models.ForeignKey(
        SecureDocument,
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='document_access_logs'
    )
    
    access_type = models.CharField(
        max_length=20,
        choices=[
            ('view', _('View')),
            ('download', _('Download')),
            ('edit', _('Edit')),
            ('delete', _('Delete')),
        ]
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('Document Access Log')
        verbose_name_plural = _('Document Access Logs')
    
    def __str__(self):
        return f"{self.document.title} - {self.user.username} - {self.access_type}"


class PatientConsent(models.Model):
    """
    Patient consent for document access.
    """
    
    patient_id = models.IntegerField()
    document_type = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    is_granted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    consent_reason = models.TextField(blank=True)
    consent_method = models.CharField(
        max_length=20,
        choices=[
            ('verbal', _('Verbal')),
            ('written', _('Written')),
            ('digital', _('Digital')),
        ],
        default='digital'
    )
    
    class Meta:
        unique_together = ['patient_id', 'document_type', 'user']
        verbose_name = _('Patient Consent')
        verbose_name_plural = _('Patient Consents')
    
    def __str__(self):
        return f"Patient {self.patient_id} - {self.document_type} - {self.user.username}"
    
    def is_valid(self) -> bool:
        """Check if consent is still valid."""
        return self.is_active and self.is_granted and self.expires_at > timezone.now()


# Wagtail integration
class SecureDocumentPermissionPolicy(ModelPermissionPolicy):
    """
    Custom permission policy for secure documents.
    """
    
    def user_has_permission(self, user, action):
        """Check if user has permission for action."""
        if not user.is_authenticated:
            return False
        
        if action == 'add':
            return user.has_perm('security.add_securedocument')
        elif action == 'change':
            return user.has_perm('security.change_securedocument')
        elif action == 'publish':
            return user.has_perm('security.publish_securedocument')
        elif action == 'bulk_delete':
            return user.has_perm('security.delete_securedocument')
        elif action == 'choose':
            return user.has_perm('security.view_securedocument')
        
        return False
    
    def user_has_any_permission(self, user, actions):
        """Check if user has any of the specified permissions."""
        return any(self.user_has_permission(user, action) for action in actions)
    
    def instances_user_has_permission_for(self, user, action):
        """Get instances user has permission for."""
        if not user.is_authenticated:
            return SecureDocument.objects.none()
        
        if action == 'change':
            return SecureDocument.objects.filter(created_by=user)
        elif action == 'publish':
            return SecureDocument.objects.filter(created_by=user)
        elif action == 'bulk_delete':
            return SecureDocument.objects.filter(created_by=user)
        
        return SecureDocument.objects.all()
    
    def instances_user_has_any_permission_for(self, user, actions):
        """Get instances user has any permission for."""
        querysets = [
            self.instances_user_has_permission_for(user, action)
            for action in actions
        ]
        
        if not querysets:
            return SecureDocument.objects.none()
        
        return querysets[0].union(*querysets[1:])
    
    def users_with_permission_for_instance(self, action, instance):
        """Get users with permission for specific instance."""
        if action in ['change', 'publish', 'bulk_delete']:
            return User.objects.filter(id=instance.created_by.id)
        
        return User.objects.all()


# Register with Wagtail
def get_secure_document_permission_policy():
    """Get secure document permission policy."""
    return SecureDocumentPermissionPolicy(SecureDocument) 