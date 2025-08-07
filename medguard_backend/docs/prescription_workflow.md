# Prescription Workflow Management in MedGuard SA

## Overview

This guide covers the complete prescription workflow management system in Wagtail 7.0.2, designed for healthcare providers in South Africa. The system ensures compliance with SAHPRA regulations and provides comprehensive prescription tracking.

## Prescription Workflow Architecture

### 1. Workflow States

```python
# medications/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail import blocks

class PrescriptionStatus(models.TextChoices):
    """Prescription workflow states"""
    DRAFT = 'draft', _('Draft')
    PENDING_REVIEW = 'pending_review', _('Pending Review')
    UNDER_REVIEW = 'under_review', _('Under Review')
    APPROVED = 'approved', _('Approved')
    DISPENSED = 'dispensed', _('Dispensed')
    COMPLETED = 'completed', _('Completed')
    CANCELLED = 'cancelled', _('Cancelled')
    EXPIRED = 'expired', _('Expired')

class PrescriptionWorkflow(models.Model):
    """Main prescription workflow model"""
    
    # Basic Information
    prescription_number = models.CharField(
        max_length=20,
        unique=True,
        help_text=_("Unique prescription identifier")
    )
    
    patient = models.ForeignKey(
        'users.Patient',
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    
    prescribing_physician = models.ForeignKey(
        'users.Physician',
        on_delete=models.CASCADE,
        related_name='prescribed_medications'
    )
    
    # Workflow State
    status = models.CharField(
        max_length=20,
        choices=PrescriptionStatus.choices,
        default=PrescriptionStatus.DRAFT
    )
    
    # Dates and Timing
    created_at = models.DateTimeField(auto_now_add=True)
    prescribed_date = models.DateTimeField(null=True, blank=True)
    review_date = models.DateTimeField(null=True, blank=True)
    dispensed_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    # Clinical Information
    diagnosis = models.TextField(
        help_text=_("Primary diagnosis or condition")
    )
    
    clinical_notes = models.TextField(
        blank=True,
        help_text=_("Additional clinical notes")
    )
    
    # Prescription Content
    medications = StreamField([
        ('medication_item', blocks.StructBlock([
            ('medication', blocks.PageChooserBlock(
                page_type='medications.MedicationPage',
                required=True
            )),
            ('dosage', blocks.CharBlock(
                max_length=100,
                help_text=_("e.g., 10mg twice daily")
            )),
            ('quantity', blocks.IntegerBlock(
                min_value=1,
                help_text=_("Number of units to dispense")
            )),
            ('duration', blocks.CharBlock(
                max_length=50,
                help_text=_("Treatment duration (e.g., 30 days)")
            )),
            ('instructions', blocks.TextBlock(
                required=False,
                help_text=_("Special instructions for patient")
            )),
            ('repeats', blocks.IntegerBlock(
                default=0,
                min_value=0,
                max_value=5,
                help_text=_("Number of repeats allowed")
            )),
        ]))
    ], use_json_field=True)
    
    # Approval and Review
    reviewed_by = models.ForeignKey(
        'users.Pharmacist',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_prescriptions'
    )
    
    review_notes = models.TextField(
        blank=True,
        help_text=_("Pharmacist review notes")
    )
    
    # Dispensing Information
    dispensed_by = models.ForeignKey(
        'users.Pharmacist',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispensed_prescriptions'
    )
    
    dispensing_pharmacy = models.ForeignKey(
        'medications.Pharmacy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _("Prescription Workflow")
        verbose_name_plural = _("Prescription Workflows")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Prescription {self.prescription_number} - {self.patient}"
    
    def generate_prescription_number(self):
        """Generate unique prescription number"""
        from datetime import datetime
        import random
        
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = f"{random.randint(1000, 9999)}"
        return f"RX{date_str}{random_str}"
    
    def save(self, *args, **kwargs):
        if not self.prescription_number:
            self.prescription_number = self.generate_prescription_number()
        super().save(*args, **kwargs)
    
    def can_be_dispensed(self):
        """Check if prescription can be dispensed"""
        return (
            self.status == PrescriptionStatus.APPROVED and
            self.expiry_date and
            timezone.now() < self.expiry_date
        )
```

### 2. Prescription Review Process

```python
# medications/workflows.py
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from celery import shared_task

class PrescriptionReviewManager:
    """Manages prescription review workflow"""
    
    @staticmethod
    def submit_for_review(prescription):
        """Submit prescription for pharmacist review"""
        prescription.status = PrescriptionStatus.PENDING_REVIEW
        prescription.save()
        
        # Notify pharmacists
        PrescriptionReviewManager.notify_pharmacists(prescription)
        
        # Schedule automatic expiry
        PrescriptionReviewManager.schedule_expiry(prescription)
    
    @staticmethod
    def assign_reviewer(prescription, pharmacist):
        """Assign pharmacist to review prescription"""
        prescription.status = PrescriptionStatus.UNDER_REVIEW
        prescription.reviewed_by = pharmacist
        prescription.review_date = timezone.now()
        prescription.save()
        
        # Notify physician of assignment
        PrescriptionReviewManager.notify_physician_assignment(prescription)
    
    @staticmethod
    def approve_prescription(prescription, pharmacist, notes=""):
        """Approve prescription for dispensing"""
        prescription.status = PrescriptionStatus.APPROVED
        prescription.reviewed_by = pharmacist
        prescription.review_notes = notes
        prescription.save()
        
        # Set expiry date (30 days from approval)
        from datetime import timedelta
        prescription.expiry_date = timezone.now() + timedelta(days=30)
        prescription.save()
        
        # Notify patient and physician
        PrescriptionReviewManager.notify_approval(prescription)
    
    @staticmethod
    def reject_prescription(prescription, pharmacist, reason):
        """Reject prescription with reason"""
        prescription.status = PrescriptionStatus.CANCELLED
        prescription.reviewed_by = pharmacist
        prescription.review_notes = f"REJECTED: {reason}"
        prescription.save()
        
        # Notify physician for revision
        PrescriptionReviewManager.notify_rejection(prescription)
    
    @staticmethod
    def notify_pharmacists(prescription):
        """Notify available pharmacists of new prescription"""
        from users.models import Pharmacist
        
        pharmacists = Pharmacist.objects.filter(is_active=True)
        for pharmacist in pharmacists:
            send_notification_email.delay(
                pharmacist.email,
                'New Prescription for Review',
                'emails/prescription_review_notification.html',
                {'prescription': prescription}
            )
    
    @staticmethod
    def schedule_expiry(prescription, days=30):
        """Schedule prescription expiry"""
        from datetime import timedelta
        
        expire_prescription.apply_async(
            args=[prescription.id],
            eta=timezone.now() + timedelta(days=days)
        )

@shared_task
def send_notification_email(email, subject, template, context):
    """Send notification email"""
    html_content = render_to_string(template, context)
    send_mail(
        subject=subject,
        message="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_content
    )

@shared_task
def expire_prescription(prescription_id):
    """Expire prescription if not dispensed"""
    try:
        prescription = PrescriptionWorkflow.objects.get(id=prescription_id)
        if prescription.status == PrescriptionStatus.APPROVED:
            prescription.status = PrescriptionStatus.EXPIRED
            prescription.save()
            
            # Notify relevant parties
            send_notification_email.delay(
                prescription.patient.email,
                'Prescription Expired',
                'emails/prescription_expired.html',
                {'prescription': prescription}
            )
    except PrescriptionWorkflow.DoesNotExist:
        pass
```

### 3. Dispensing Workflow

```python
# medications/dispensing.py
from django.utils import timezone
from django.core.exceptions import ValidationError

class DispensingManager:
    """Manages medication dispensing workflow"""
    
    @staticmethod
    def validate_dispensing(prescription, pharmacist, pharmacy):
        """Validate prescription can be dispensed"""
        errors = []
        
        # Check prescription status
        if prescription.status != PrescriptionStatus.APPROVED:
            errors.append(_("Prescription is not approved for dispensing"))
        
        # Check expiry
        if prescription.expiry_date and timezone.now() > prescription.expiry_date:
            errors.append(_("Prescription has expired"))
        
        # Check pharmacist authorization
        if not pharmacist.is_licensed:
            errors.append(_("Pharmacist is not licensed to dispense"))
        
        # Check pharmacy authorization
        if not pharmacy.is_authorized:
            errors.append(_("Pharmacy is not authorized to dispense"))
        
        if errors:
            raise ValidationError(errors)
    
    @staticmethod
    def dispense_prescription(prescription, pharmacist, pharmacy, dispensed_items):
        """Process prescription dispensing"""
        
        # Validate dispensing
        DispensingManager.validate_dispensing(prescription, pharmacist, pharmacy)
        
        # Update prescription status
        prescription.status = PrescriptionStatus.DISPENSED
        prescription.dispensed_by = pharmacist
        prescription.dispensing_pharmacy = pharmacy
        prescription.dispensed_date = timezone.now()
        prescription.save()
        
        # Create dispensing record
        dispensing_record = DispensingRecord.objects.create(
            prescription=prescription,
            dispensed_by=pharmacist,
            pharmacy=pharmacy,
            dispensed_date=timezone.now(),
            dispensed_items=dispensed_items
        )
        
        # Update inventory
        DispensingManager.update_inventory(pharmacy, dispensed_items)
        
        # Generate dispensing label
        DispensingManager.generate_dispensing_label(dispensing_record)
        
        # Notify patient
        DispensingManager.notify_patient_dispensed(prescription)
        
        return dispensing_record
    
    @staticmethod
    def partial_dispense(prescription, pharmacist, pharmacy, available_items):
        """Handle partial dispensing"""
        
        # Create partial dispensing record
        partial_record = PartialDispensingRecord.objects.create(
            prescription=prescription,
            dispensed_by=pharmacist,
            pharmacy=pharmacy,
            dispensed_items=available_items,
            remaining_items=prescription.get_remaining_items(available_items)
        )
        
        # Check if fully dispensed
        if prescription.is_fully_dispensed():
            prescription.status = PrescriptionStatus.COMPLETED
        
        prescription.save()
        return partial_record

class DispensingRecord(models.Model):
    """Record of prescription dispensing"""
    
    prescription = models.ForeignKey(
        PrescriptionWorkflow,
        on_delete=models.CASCADE,
        related_name='dispensing_records'
    )
    
    dispensed_by = models.ForeignKey(
        'users.Pharmacist',
        on_delete=models.CASCADE
    )
    
    pharmacy = models.ForeignKey(
        'medications.Pharmacy',
        on_delete=models.CASCADE
    )
    
    dispensed_date = models.DateTimeField(default=timezone.now)
    
    dispensed_items = StreamField([
        ('dispensed_item', blocks.StructBlock([
            ('medication', blocks.PageChooserBlock(page_type='medications.MedicationPage')),
            ('quantity_dispensed', blocks.IntegerBlock()),
            ('batch_number', blocks.CharBlock(max_length=50)),
            ('expiry_date', blocks.DateBlock()),
            ('manufacturer', blocks.CharBlock(max_length=200)),
        ]))
    ], use_json_field=True)
    
    dispensing_notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _("Dispensing Record")
        verbose_name_plural = _("Dispensing Records")
```

## Prescription Templates and Forms

### 1. Prescription Creation Form

```python
# medications/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import PrescriptionWorkflow

class PrescriptionForm(forms.ModelForm):
    """Form for creating prescriptions"""
    
    class Meta:
        model = PrescriptionWorkflow
        fields = [
            'patient', 'diagnosis', 'clinical_notes', 'medications'
        ]
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 3}),
            'clinical_notes': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.physician = kwargs.pop('physician', None)
        super().__init__(*args, **kwargs)
        
        # Filter patients to physician's patients only
        if self.physician:
            self.fields['patient'].queryset = self.physician.patients.all()
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate medication combinations
        self.validate_drug_interactions(cleaned_data)
        
        # Validate dosages
        self.validate_dosages(cleaned_data)
        
        return cleaned_data
    
    def validate_drug_interactions(self, data):
        """Check for dangerous drug interactions"""
        medications = data.get('medications', [])
        
        # Implementation for drug interaction checking
        # This would integrate with a drug interaction database
        pass
    
    def validate_dosages(self, data):
        """Validate medication dosages"""
        medications = data.get('medications', [])
        
        for med_block in medications:
            if med_block.block_type == 'medication_item':
                # Validate dosage format and safety
                pass
```

### 2. Prescription Review Form

```python
# medications/forms.py
class PrescriptionReviewForm(forms.Form):
    """Form for pharmacist prescription review"""
    
    REVIEW_CHOICES = [
        ('approve', _('Approve')),
        ('reject', _('Reject')),
        ('request_clarification', _('Request Clarification')),
    ]
    
    decision = forms.ChoiceField(
        choices=REVIEW_CHOICES,
        widget=forms.RadioSelect
    )
    
    review_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=True,
        help_text=_("Provide detailed review notes")
    )
    
    clinical_concerns = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text=_("Any clinical concerns or recommendations")
    )
    
    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get('decision')
        
        if decision == 'reject' and not cleaned_data.get('clinical_concerns'):
            raise forms.ValidationError(
                _("Clinical concerns must be provided when rejecting a prescription")
            )
        
        return cleaned_data
```

## Wagtail Admin Integration

### 1. Prescription Admin

```python
# medications/wagtail_hooks.py
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

@hooks.register('register_admin_urls')
def register_prescription_urls():
    return [
        path('prescriptions/', PrescriptionIndexView.as_view(), name='prescription_index'),
        path('prescriptions/create/', PrescriptionCreateView.as_view(), name='prescription_create'),
        path('prescriptions/<int:pk>/', PrescriptionDetailView.as_view(), name='prescription_detail'),
        path('prescriptions/<int:pk>/review/', PrescriptionReviewView.as_view(), name='prescription_review'),
        path('prescriptions/<int:pk>/dispense/', PrescriptionDispenseView.as_view(), name='prescription_dispense'),
    ]

@hooks.register('register_admin_menu_item')
def register_prescription_menu_item():
    return MenuItem(
        _('Prescriptions'),
        reverse('prescription_index'),
        classnames='icon icon-list-ul',
        order=200
    )

class PrescriptionAdmin(ModelAdmin):
    """Wagtail admin for prescriptions"""
    
    model = PrescriptionWorkflow
    menu_label = _('Prescriptions')
    menu_icon = 'list-ul'
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    
    list_display = [
        'prescription_number', 'patient', 'prescribing_physician',
        'status', 'created_at', 'expiry_date'
    ]
    
    list_filter = ['status', 'created_at', 'prescribing_physician']
    search_fields = ['prescription_number', 'patient__name', 'diagnosis']
    
    panels = [
        MultiFieldPanel([
            FieldPanel('prescription_number'),
            FieldPanel('patient'),
            FieldPanel('prescribing_physician'),
            FieldPanel('status'),
        ], heading=_("Basic Information")),
        
        MultiFieldPanel([
            FieldPanel('diagnosis'),
            FieldPanel('clinical_notes'),
        ], heading=_("Clinical Information")),
        
        FieldPanel('medications'),
        
        MultiFieldPanel([
            FieldPanel('reviewed_by'),
            FieldPanel('review_notes'),
            FieldPanel('dispensed_by'),
            FieldPanel('dispensing_pharmacy'),
        ], heading=_("Review and Dispensing")),
    ]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # Filter based on user role
        if hasattr(request.user, 'physician'):
            # Physicians see only their prescriptions
            return qs.filter(prescribing_physician=request.user.physician)
        elif hasattr(request.user, 'pharmacist'):
            # Pharmacists see prescriptions for review/dispensing
            return qs.filter(
                status__in=[
                    PrescriptionStatus.PENDING_REVIEW,
                    PrescriptionStatus.UNDER_REVIEW,
                    PrescriptionStatus.APPROVED
                ]
            )
        
        return qs

modeladmin_register(PrescriptionAdmin)
```

### 2. Dashboard Widgets

```python
# medications/dashboard.py
from wagtail.admin.ui.components import Component
from django.template.loader import render_to_string

class PrescriptionDashboardWidget(Component):
    """Dashboard widget for prescription statistics"""
    
    def render_html(self, parent_context):
        # Get prescription statistics
        total_prescriptions = PrescriptionWorkflow.objects.count()
        pending_review = PrescriptionWorkflow.objects.filter(
            status=PrescriptionStatus.PENDING_REVIEW
        ).count()
        approved_today = PrescriptionWorkflow.objects.filter(
            status=PrescriptionStatus.APPROVED,
            review_date__date=timezone.now().date()
        ).count()
        
        context = {
            'total_prescriptions': total_prescriptions,
            'pending_review': pending_review,
            'approved_today': approved_today,
        }
        
        return render_to_string(
            'admin/prescription_dashboard_widget.html',
            context
        )

@hooks.register('construct_homepage_panels')
def add_prescription_dashboard_widget(request, panels):
    panels.append(PrescriptionDashboardWidget())
```

## API Integration

### 1. Prescription API Views

```python
# api/prescription_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _

class PrescriptionViewSet(viewsets.ModelViewSet):
    """API viewset for prescriptions"""
    
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if hasattr(user, 'physician'):
            return PrescriptionWorkflow.objects.filter(
                prescribing_physician=user.physician
            )
        elif hasattr(user, 'pharmacist'):
            return PrescriptionWorkflow.objects.filter(
                status__in=[
                    PrescriptionStatus.PENDING_REVIEW,
                    PrescriptionStatus.UNDER_REVIEW,
                    PrescriptionStatus.APPROVED
                ]
            )
        elif hasattr(user, 'patient'):
            return PrescriptionWorkflow.objects.filter(
                patient=user.patient
            )
        
        return PrescriptionWorkflow.objects.none()
    
    @action(detail=True, methods=['post'])
    def submit_for_review(self, request, pk=None):
        """Submit prescription for review"""
        prescription = self.get_object()
        
        if prescription.status != PrescriptionStatus.DRAFT:
            return Response(
                {'error': _('Prescription is not in draft status')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        PrescriptionReviewManager.submit_for_review(prescription)
        
        return Response({
            'message': _('Prescription submitted for review'),
            'status': prescription.status
        })
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve prescription (pharmacist only)"""
        prescription = self.get_object()
        
        if not hasattr(request.user, 'pharmacist'):
            return Response(
                {'error': _('Only pharmacists can approve prescriptions')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notes = request.data.get('notes', '')
        PrescriptionReviewManager.approve_prescription(
            prescription, request.user.pharmacist, notes
        )
        
        return Response({
            'message': _('Prescription approved'),
            'status': prescription.status
        })
    
    @action(detail=True, methods=['post'])
    def dispense(self, request, pk=None):
        """Dispense prescription (pharmacist only)"""
        prescription = self.get_object()
        
        if not hasattr(request.user, 'pharmacist'):
            return Response(
                {'error': _('Only pharmacists can dispense prescriptions')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            dispensed_items = request.data.get('dispensed_items', [])
            pharmacy = request.user.pharmacist.pharmacy
            
            record = DispensingManager.dispense_prescription(
                prescription, request.user.pharmacist, pharmacy, dispensed_items
            )
            
            return Response({
                'message': _('Prescription dispensed successfully'),
                'dispensing_record_id': record.id
            })
        
        except ValidationError as e:
            return Response(
                {'errors': e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )
```

## Mobile Integration

### 1. Mobile Prescription Views

```python
# mobile/prescription_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_prescriptions(request):
    """Get patient's prescriptions for mobile app"""
    
    if not hasattr(request.user, 'patient'):
        return Response({'error': 'User is not a patient'}, status=400)
    
    prescriptions = PrescriptionWorkflow.objects.filter(
        patient=request.user.patient
    ).select_related('prescribing_physician', 'dispensing_pharmacy')
    
    data = []
    for prescription in prescriptions:
        data.append({
            'id': prescription.id,
            'prescription_number': prescription.prescription_number,
            'status': prescription.get_status_display(),
            'prescribed_date': prescription.prescribed_date,
            'expiry_date': prescription.expiry_date,
            'physician': prescription.prescribing_physician.name,
            'medications': [
                {
                    'name': med.value['medication'].title,
                    'dosage': med.value['dosage'],
                    'instructions': med.value['instructions']
                }
                for med in prescription.medications
                if med.block_type == 'medication_item'
            ]
        })
    
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_prescription_renewal(request, prescription_id):
    """Request prescription renewal"""
    
    try:
        prescription = PrescriptionWorkflow.objects.get(
            id=prescription_id,
            patient=request.user.patient
        )
        
        # Create renewal request
        renewal_request = PrescriptionRenewalRequest.objects.create(
            original_prescription=prescription,
            patient=prescription.patient,
            requested_date=timezone.now(),
            reason=request.data.get('reason', ''),
            status='pending'
        )
        
        # Notify physician
        send_notification_email.delay(
            prescription.prescribing_physician.email,
            'Prescription Renewal Request',
            'emails/renewal_request.html',
            {'renewal_request': renewal_request}
        )
        
        return Response({
            'message': 'Renewal request submitted successfully',
            'request_id': renewal_request.id
        })
    
    except PrescriptionWorkflow.DoesNotExist:
        return Response({'error': 'Prescription not found'}, status=404)
```

## Reporting and Analytics

### 1. Prescription Analytics

```python
# medications/analytics.py
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

class PrescriptionAnalytics:
    """Analytics for prescription workflow"""
    
    @staticmethod
    def get_prescription_metrics(start_date=None, end_date=None):
        """Get prescription workflow metrics"""
        
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        queryset = PrescriptionWorkflow.objects.filter(
            created_at__range=[start_date, end_date]
        )
        
        return {
            'total_prescriptions': queryset.count(),
            'by_status': queryset.values('status').annotate(
                count=Count('id')
            ),
            'average_review_time': queryset.filter(
                review_date__isnull=False
            ).aggregate(
                avg_time=Avg(
                    F('review_date') - F('created_at')
                )
            )['avg_time'],
            'dispensing_rate': queryset.filter(
                status=PrescriptionStatus.DISPENSED
            ).count() / queryset.count() * 100,
        }
    
    @staticmethod
    def get_physician_metrics(physician):
        """Get metrics for specific physician"""
        
        prescriptions = PrescriptionWorkflow.objects.filter(
            prescribing_physician=physician
        )
        
        return {
            'total_prescriptions': prescriptions.count(),
            'approval_rate': prescriptions.filter(
                status=PrescriptionStatus.APPROVED
            ).count() / prescriptions.count() * 100,
            'rejection_rate': prescriptions.filter(
                status=PrescriptionStatus.CANCELLED
            ).count() / prescriptions.count() * 100,
        }
```

## Compliance and Audit

### 1. Audit Trail

```python
# medications/audit.py
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class PrescriptionAuditLog(models.Model):
    """Audit log for prescription changes"""
    
    ACTION_CHOICES = [
        ('create', _('Created')),
        ('update', _('Updated')),
        ('submit', _('Submitted for Review')),
        ('approve', _('Approved')),
        ('reject', _('Rejected')),
        ('dispense', _('Dispensed')),
        ('cancel', _('Cancelled')),
    ]
    
    prescription = models.ForeignKey(
        PrescriptionWorkflow,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE
    )
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _("Prescription Audit Log")
        verbose_name_plural = _("Prescription Audit Logs")
        ordering = ['-timestamp']

# Signal handlers for audit logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

@receiver(pre_save, sender=PrescriptionWorkflow)
def log_prescription_changes(sender, instance, **kwargs):
    """Log prescription changes"""
    if instance.pk:
        # Track changes for existing prescriptions
        old_instance = PrescriptionWorkflow.objects.get(pk=instance.pk)
        changes = {}
        
        for field in instance._meta.fields:
            old_value = getattr(old_instance, field.name)
            new_value = getattr(instance, field.name)
            
            if old_value != new_value:
                changes[field.name] = {
                    'old': str(old_value),
                    'new': str(new_value)
                }
        
        if changes:
            # Store changes to be logged after save
            instance._audit_changes = changes
```

## Testing

### 1. Prescription Workflow Tests

```python
# medications/tests/test_prescription_workflow.py
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from medications.models import PrescriptionWorkflow, PrescriptionStatus
from medications.workflows import PrescriptionReviewManager

class PrescriptionWorkflowTest(TestCase):
    """Test prescription workflow functionality"""
    
    def setUp(self):
        # Create test data
        self.physician = self.create_test_physician()
        self.pharmacist = self.create_test_pharmacist()
        self.patient = self.create_test_patient()
        self.pharmacy = self.create_test_pharmacy()
    
    def test_prescription_creation(self):
        """Test prescription creation"""
        prescription = PrescriptionWorkflow.objects.create(
            patient=self.patient,
            prescribing_physician=self.physician,
            diagnosis="Hypertension",
            medications=[
                {
                    'type': 'medication_item',
                    'value': {
                        'medication': self.medication.pk,
                        'dosage': '10mg once daily',
                        'quantity': 30,
                        'duration': '30 days'
                    }
                }
            ]
        )
        
        self.assertIsNotNone(prescription.prescription_number)
        self.assertEqual(prescription.status, PrescriptionStatus.DRAFT)
    
    def test_prescription_review_workflow(self):
        """Test prescription review process"""
        prescription = self.create_test_prescription()
        
        # Submit for review
        PrescriptionReviewManager.submit_for_review(prescription)
        prescription.refresh_from_db()
        self.assertEqual(prescription.status, PrescriptionStatus.PENDING_REVIEW)
        
        # Assign reviewer
        PrescriptionReviewManager.assign_reviewer(prescription, self.pharmacist)
        prescription.refresh_from_db()
        self.assertEqual(prescription.status, PrescriptionStatus.UNDER_REVIEW)
        self.assertEqual(prescription.reviewed_by, self.pharmacist)
        
        # Approve prescription
        PrescriptionReviewManager.approve_prescription(
            prescription, self.pharmacist, "Approved for dispensing"
        )
        prescription.refresh_from_db()
        self.assertEqual(prescription.status, PrescriptionStatus.APPROVED)
        self.assertIsNotNone(prescription.expiry_date)
    
    def test_prescription_dispensing(self):
        """Test prescription dispensing"""
        prescription = self.create_approved_prescription()
        
        dispensed_items = [
            {
                'type': 'dispensed_item',
                'value': {
                    'medication': self.medication.pk,
                    'quantity_dispensed': 30,
                    'batch_number': 'BATCH001',
                    'expiry_date': timezone.now().date() + timedelta(days=365),
                    'manufacturer': 'Test Pharma'
                }
            }
        ]
        
        record = DispensingManager.dispense_prescription(
            prescription, self.pharmacist, self.pharmacy, dispensed_items
        )
        
        prescription.refresh_from_db()
        self.assertEqual(prescription.status, PrescriptionStatus.DISPENSED)
        self.assertEqual(prescription.dispensed_by, self.pharmacist)
        self.assertIsNotNone(record)
```

## Next Steps

1. **Security Implementation**: See `wagtail_security.md`
2. **Medication Management**: Review `medication_management.md`
3. **API Integration**: Check `wagtail_api.md`
4. **Compliance Setup**: Follow `wagtail_compliance.md`

## Resources

- [SAHPRA Guidelines](https://www.sahpra.org.za/)
- [South African Pharmacy Council](https://www.sapc.za.org/)
- [Healthcare Professional Councils](https://www.hpcsa.co.za/)
- [Django Workflow Documentation](https://docs.djangoproject.com/)
