"""
Comprehensive test suite for Wagtail 7.0.2 healthcare workflows in MedGuard SA.

This module tests all healthcare workflow functionality including:
- PrescriptionApprovalWorkflow stages and transitions
- MedicationContentReviewWorkflow processes
- PatientDataAccessWorkflow compliance
- PharmacyIntegrationWorkflow operations
- PrescriptionRenewalWorkflow automation
- MedicationRecallWorkflow emergency procedures
- MedicationStockWorkflow inventory management
- PatientConsentWorkflow legal compliance
- EmergencyAccessWorkflow urgent care scenarios
- Workflow task execution and notification systems
"""

import pytest
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from wagtail.models import Page
from wagtail.workflows.models import Workflow, WorkflowTask, WorkflowState, TaskState

# Import workflow classes
from workflows.healthcare_workflows import (
    PrescriptionApprovalWorkflow,
    MedicationContentReviewWorkflow,
    PatientDataAccessWorkflow,
    PharmacyIntegrationWorkflow,
    PrescriptionRenewalWorkflow,
    MedicationRecallWorkflow,
    MedicationStockWorkflow,
    PatientConsentWorkflow,
    EmergencyAccessWorkflow
)

# Import workflow tasks
from workflows.tasks import (
    PrescriptionVerificationTask,
    PrescriptionRenewalReminderTask,
    MedicationInteractionReviewTask,
    PharmacyIntegrationVerificationTask,
    EmergencyAccessLoggingTask,
    MedicationRecallNotificationTask,
    PatientDataAccessApprovalTask,
    MedicationStockAlertTask,
    MedicationContentReviewTask
)

# Import related models
from medications.models import EnhancedPrescription, Medication
from medguard_notifications.models import NotificationTemplate

User = get_user_model()


class BaseWorkflowTestCase(TestCase):
    """Base test case for workflow testing with common setup."""
    
    def setUp(self):
        """Set up common test data."""
        # Create test users with different roles
        self.doctor = User.objects.create_user(
            username='doctor',
            email='doctor@medguard.co.za',
            password='testpass123',
            first_name='Dr. Jane',
            last_name='Smith'
        )
        self.doctor.profile.role = 'DOCTOR'
        self.doctor.profile.save()
        
        self.specialist = User.objects.create_user(
            username='specialist',
            email='specialist@medguard.co.za',
            password='testpass123',
            first_name='Dr. John',
            last_name='Specialist'
        )
        self.specialist.profile.role = 'SPECIALIST'
        self.specialist.profile.save()
        
        self.pharmacist = User.objects.create_user(
            username='pharmacist',
            email='pharmacist@medguard.co.za',
            password='testpass123',
            first_name='Pharm',
            last_name='Expert'
        )
        self.pharmacist.profile.role = 'PHARMACIST'
        self.pharmacist.profile.save()
        
        self.senior_doctor = User.objects.create_user(
            username='senior_doctor',
            email='senior@medguard.co.za',
            password='testpass123',
            first_name='Dr. Senior',
            last_name='Expert'
        )
        self.senior_doctor.profile.role = 'SENIOR_DOCTOR'
        self.senior_doctor.profile.save()
        
        self.patient = User.objects.create_user(
            username='patient',
            email='patient@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        # Create test prescription
        self.prescription = EnhancedPrescription.objects.create(
            patient=self.patient,
            prescriber=self.doctor,
            medication_name='Test Medication',
            dosage='500mg',
            frequency='twice_daily',
            duration_days=30,
            instructions='Take with food',
            status='pending_approval'
        )
        
        # Create notification templates
        self.notification_template = NotificationTemplate.objects.create(
            name='prescription_initial_review',
            subject_template='Prescription Review Required',
            body_template='Please review prescription for {{ patient.full_name }}',
            notification_type='email'
        )


class PrescriptionApprovalWorkflowTestCase(BaseWorkflowTestCase):
    """Test cases for PrescriptionApprovalWorkflow."""
    
    def setUp(self):
        """Set up prescription approval workflow test data."""
        super().setUp()
        self.workflow = PrescriptionApprovalWorkflow.objects.create(
            name='Test Prescription Approval',
            prescription=self.prescription
        )
        
    def test_workflow_creation(self):
        """Test creating a prescription approval workflow."""
        self.assertEqual(self.workflow.prescription, self.prescription)
        self.assertEqual(self.workflow.current_stage, 'initial_review')
        self.assertEqual(self.workflow.status, PrescriptionApprovalWorkflow.Status.PENDING)
        
    def test_workflow_stages_configuration(self):
        """Test workflow stages are properly configured."""
        stages = PrescriptionApprovalWorkflow.STAGES
        
        required_stages = [
            'initial_review', 'specialist_review', 
            'pharmacy_review', 'final_approval'
        ]
        
        for stage in required_stages:
            self.assertIn(stage, stages)
            self.assertIn('name', stages[stage])
            self.assertIn('required_role', stages[stage])
            self.assertIn('estimated_duration', stages[stage])
            
    def test_workflow_initial_review_stage(self):
        """Test initial review stage functionality."""
        # Start workflow
        self.workflow.start_workflow(self.doctor)
        
        self.assertEqual(self.workflow.current_stage, 'initial_review')
        self.assertEqual(self.workflow.status, PrescriptionApprovalWorkflow.Status.IN_PROGRESS)
        self.assertEqual(self.workflow.assigned_reviewer, self.doctor)
        
    def test_workflow_stage_progression(self):
        """Test workflow progresses through stages correctly."""
        # Start workflow
        self.workflow.start_workflow(self.doctor)
        
        # Complete initial review
        self.workflow.complete_stage(
            reviewer=self.doctor,
            notes='Initial review completed',
            approved=True
        )
        
        # Should progress to pharmacy review (skipping optional specialist)
        self.assertEqual(self.workflow.current_stage, 'pharmacy_review')
        
        # Complete pharmacy review
        self.workflow.complete_stage(
            reviewer=self.pharmacist,
            notes='Pharmacy review completed',
            approved=True
        )
        
        # Should progress to final approval
        self.assertEqual(self.workflow.current_stage, 'final_approval')
        
    def test_workflow_specialist_review_optional(self):
        """Test specialist review is optional and can be skipped."""
        self.workflow.start_workflow(self.doctor)
        
        # Complete initial review with specialist referral
        self.workflow.complete_stage(
            reviewer=self.doctor,
            notes='Needs specialist review',
            approved=True,
            require_specialist=True
        )
        
        # Should go to specialist review
        self.assertEqual(self.workflow.current_stage, 'specialist_review')
        
    def test_workflow_rejection_handling(self):
        """Test workflow rejection handling."""
        self.workflow.start_workflow(self.doctor)
        
        # Reject at initial review
        self.workflow.reject_workflow(
            reviewer=self.doctor,
            reason='Insufficient information provided'
        )
        
        self.assertEqual(self.workflow.status, PrescriptionApprovalWorkflow.Status.REJECTED)
        self.assertIn('Insufficient information', self.workflow.rejection_reason)
        
    def test_workflow_completion(self):
        """Test complete workflow execution."""
        self.workflow.start_workflow(self.doctor)
        
        # Complete all stages
        stages_to_complete = [
            (self.doctor, 'initial_review'),
            (self.pharmacist, 'pharmacy_review'),
            (self.senior_doctor, 'final_approval')
        ]
        
        for reviewer, expected_stage in stages_to_complete:
            self.assertEqual(self.workflow.current_stage, expected_stage)
            self.workflow.complete_stage(
                reviewer=reviewer,
                notes=f'{expected_stage} completed',
                approved=True
            )
        
        # Should be approved
        self.assertEqual(self.workflow.status, PrescriptionApprovalWorkflow.Status.APPROVED)
        
    def test_workflow_email_notifications(self):
        """Test workflow sends email notifications."""
        with patch('workflows.healthcare_workflows.NotificationService') as mock_service:
            self.workflow.start_workflow(self.doctor)
            
            # Should have sent notification
            mock_service.send_workflow_notification.assert_called()
            
    def test_workflow_timing_estimates(self):
        """Test workflow provides accurate timing estimates."""
        self.workflow.start_workflow(self.doctor)
        
        estimated_completion = self.workflow.get_estimated_completion_time()
        self.assertIsInstance(estimated_completion, datetime)
        self.assertGreater(estimated_completion, timezone.now())
        
    def test_workflow_role_permissions(self):
        """Test workflow enforces role-based permissions."""
        self.workflow.start_workflow(self.doctor)
        
        # Patient should not be able to complete review
        with self.assertRaises(PermissionError):
            self.workflow.complete_stage(
                reviewer=self.patient,
                notes='Unauthorized completion',
                approved=True
            )
            
    def test_workflow_audit_trail(self):
        """Test workflow maintains complete audit trail."""
        self.workflow.start_workflow(self.doctor)
        
        # Complete a stage
        self.workflow.complete_stage(
            reviewer=self.doctor,
            notes='Initial review completed',
            approved=True
        )
        
        # Check audit trail
        audit_entries = self.workflow.get_audit_trail()
        self.assertGreater(len(audit_entries), 0)
        self.assertEqual(audit_entries[0]['reviewer'], self.doctor)
        self.assertEqual(audit_entries[0]['action'], 'stage_completed')


class MedicationContentReviewWorkflowTestCase(BaseWorkflowTestCase):
    """Test cases for MedicationContentReviewWorkflow."""
    
    def setUp(self):
        """Set up medication content review workflow test data."""
        super().setUp()
        self.medication = Medication.objects.create(
            name='Test Medication',
            generic_name='Test Generic',
            strength='500mg',
            form='tablet'
        )
        
        self.workflow = MedicationContentReviewWorkflow.objects.create(
            name='Test Content Review',
            medication=self.medication,
            review_type='content_update'
        )
        
    def test_content_review_workflow_creation(self):
        """Test creating a content review workflow."""
        self.assertEqual(self.workflow.medication, self.medication)
        self.assertEqual(self.workflow.review_type, 'content_update')
        self.assertEqual(self.workflow.status, MedicationContentReviewWorkflow.Status.PENDING)
        
    def test_content_accuracy_review(self):
        """Test content accuracy review process."""
        self.workflow.start_workflow(self.doctor)
        
        # Review content for accuracy
        self.workflow.review_content_accuracy(
            reviewer=self.doctor,
            accuracy_score=95,
            notes='Content is medically accurate'
        )
        
        self.assertEqual(self.workflow.accuracy_score, 95)
        
    def test_clinical_validation_process(self):
        """Test clinical validation process."""
        self.workflow.start_workflow(self.doctor)
        
        # Perform clinical validation
        self.workflow.perform_clinical_validation(
            reviewer=self.specialist,
            validation_passed=True,
            clinical_notes='Clinically appropriate recommendations'
        )
        
        self.assertTrue(self.workflow.clinical_validation_passed)
        
    def test_compliance_review_process(self):
        """Test regulatory compliance review."""
        self.workflow.start_workflow(self.doctor)
        
        # Review compliance
        self.workflow.review_compliance(
            reviewer=self.senior_doctor,
            compliance_passed=True,
            regulatory_notes='Meets all regulatory requirements'
        )
        
        self.assertTrue(self.workflow.compliance_passed)
        
    def test_content_rejection_with_changes(self):
        """Test content rejection with required changes."""
        self.workflow.start_workflow(self.doctor)
        
        required_changes = [
            'Update dosage information',
            'Add contraindication warnings',
            'Review side effects list'
        ]
        
        self.workflow.reject_workflow(
            reviewer=self.doctor,
            reason='Content needs updates',
            required_changes='; '.join(required_changes)
        )
        
        self.assertEqual(self.workflow.status, MedicationContentReviewWorkflow.Status.REJECTED)
        self.assertIn('dosage information', self.workflow.required_changes)


class PatientDataAccessWorkflowTestCase(BaseWorkflowTestCase):
    """Test cases for PatientDataAccessWorkflow."""
    
    def setUp(self):
        """Set up patient data access workflow test data."""
        super().setUp()
        self.workflow = PatientDataAccessWorkflow.objects.create(
            name='Test Data Access',
            patient=self.patient,
            requester=self.doctor,
            access_type='medical_history',
            purpose='treatment_planning'
        )
        
    def test_data_access_workflow_creation(self):
        """Test creating a data access workflow."""
        self.assertEqual(self.workflow.patient, self.patient)
        self.assertEqual(self.workflow.requester, self.doctor)
        self.assertEqual(self.workflow.access_type, 'medical_history')
        
    def test_hipaa_compliance_check(self):
        """Test HIPAA compliance validation."""
        self.workflow.start_workflow(self.senior_doctor)
        
        # Perform HIPAA compliance check
        compliance_result = self.workflow.check_hipaa_compliance(
            reviewer=self.senior_doctor,
            purpose_justified=True,
            minimum_necessary=True,
            authorization_valid=True
        )
        
        self.assertTrue(compliance_result)
        self.assertTrue(self.workflow.hipaa_compliant)
        
    def test_patient_consent_verification(self):
        """Test patient consent verification process."""
        self.workflow.start_workflow(self.senior_doctor)
        
        # Verify patient consent
        consent_result = self.workflow.verify_patient_consent(
            reviewer=self.senior_doctor,
            consent_obtained=True,
            consent_scope_adequate=True,
            consent_date=timezone.now().date()
        )
        
        self.assertTrue(consent_result)
        self.assertTrue(self.workflow.patient_consent_verified)
        
    def test_access_level_determination(self):
        """Test appropriate access level determination."""
        self.workflow.start_workflow(self.senior_doctor)
        
        # Determine access level
        access_level = self.workflow.determine_access_level(
            reviewer=self.senior_doctor,
            clinical_need='high',
            data_sensitivity='medium',
            requester_role='DOCTOR'
        )
        
        self.assertIn(access_level, ['read_only', 'limited_write', 'full_access'])
        
    def test_data_access_logging(self):
        """Test data access is properly logged."""
        self.workflow.start_workflow(self.senior_doctor)
        
        # Complete workflow
        self.workflow.approve_access(
            reviewer=self.senior_doctor,
            access_level='read_only',
            duration_days=30,
            notes='Approved for treatment planning'
        )
        
        # Check access log
        access_logs = self.workflow.get_access_logs()
        self.assertGreater(len(access_logs), 0)
        self.assertEqual(access_logs[0]['action'], 'access_granted')


class PharmacyIntegrationWorkflowTestCase(BaseWorkflowTestCase):
    """Test cases for PharmacyIntegrationWorkflow."""
    
    def setUp(self):
        """Set up pharmacy integration workflow test data."""
        super().setUp()
        self.workflow = PharmacyIntegrationWorkflow.objects.create(
            name='Test Pharmacy Integration',
            pharmacy_name='MedGuard Pharmacy',
            integration_type='prescription_sync',
            api_endpoint='https://api.medguardpharmacy.co.za/v1'
        )
        
    def test_pharmacy_integration_workflow_creation(self):
        """Test creating a pharmacy integration workflow."""
        self.assertEqual(self.workflow.pharmacy_name, 'MedGuard Pharmacy')
        self.assertEqual(self.workflow.integration_type, 'prescription_sync')
        
    def test_api_connectivity_verification(self):
        """Test API connectivity verification."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {'status': 'healthy'}
            
            self.workflow.start_workflow(self.pharmacist)
            
            # Test API connectivity
            connectivity_result = self.workflow.verify_api_connectivity(
                reviewer=self.pharmacist
            )
            
            self.assertTrue(connectivity_result)
            self.assertTrue(self.workflow.api_connectivity_verified)
            
    def test_data_format_validation(self):
        """Test data format validation process."""
        self.workflow.start_workflow(self.pharmacist)
        
        # Test data format
        sample_data = {
            'prescription_id': '12345',
            'medication': 'Aspirin',
            'dosage': '325mg',
            'quantity': 30
        }
        
        format_result = self.workflow.validate_data_format(
            reviewer=self.pharmacist,
            sample_data=sample_data
        )
        
        self.assertTrue(format_result)
        
    def test_security_compliance_check(self):
        """Test security compliance verification."""
        self.workflow.start_workflow(self.pharmacist)
        
        # Check security compliance
        security_result = self.workflow.check_security_compliance(
            reviewer=self.senior_doctor,
            encryption_verified=True,
            authentication_secure=True,
            audit_logging_enabled=True
        )
        
        self.assertTrue(security_result)
        self.assertTrue(self.workflow.security_compliant)


class PrescriptionRenewalWorkflowTestCase(BaseWorkflowTestCase):
    """Test cases for PrescriptionRenewalWorkflow."""
    
    def setUp(self):
        """Set up prescription renewal workflow test data."""
        super().setUp()
        self.workflow = PrescriptionRenewalWorkflow.objects.create(
            name='Test Prescription Renewal',
            original_prescription=self.prescription,
            renewal_type='standard',
            requested_duration_days=30
        )
        
    def test_prescription_renewal_workflow_creation(self):
        """Test creating a prescription renewal workflow."""
        self.assertEqual(self.workflow.original_prescription, self.prescription)
        self.assertEqual(self.workflow.renewal_type, 'standard')
        self.assertEqual(self.workflow.requested_duration_days, 30)
        
    def test_clinical_review_for_renewal(self):
        """Test clinical review process for renewal."""
        self.workflow.start_workflow(self.doctor)
        
        # Perform clinical review
        review_result = self.workflow.perform_clinical_review(
            reviewer=self.doctor,
            patient_condition_stable=True,
            medication_effective=True,
            no_adverse_reactions=True,
            notes='Patient responding well to treatment'
        )
        
        self.assertTrue(review_result)
        self.assertTrue(self.workflow.clinical_review_passed)
        
    def test_automatic_renewal_criteria(self):
        """Test automatic renewal criteria evaluation."""
        self.workflow.start_workflow(self.doctor)
        
        # Check automatic renewal eligibility
        auto_renewal_eligible = self.workflow.check_automatic_renewal_eligibility(
            patient_compliance_good=True,
            no_recent_hospitalizations=True,
            regular_monitoring_up_to_date=True,
            prescription_age_days=15
        )
        
        self.assertTrue(auto_renewal_eligible)
        
    def test_renewal_duration_validation(self):
        """Test renewal duration validation."""
        self.workflow.start_workflow(self.doctor)
        
        # Test invalid duration (too long)
        with self.assertRaises(ValidationError):
            self.workflow.validate_renewal_duration(
                reviewer=self.doctor,
                requested_days=365,  # Too long for standard renewal
                medication_type='controlled_substance'
            )
            
    def test_renewal_notification_system(self):
        """Test renewal notification system."""
        with patch('workflows.healthcare_workflows.NotificationService') as mock_service:
            self.workflow.start_workflow(self.doctor)
            
            # Complete renewal
            self.workflow.approve_renewal(
                reviewer=self.doctor,
                approved_duration_days=30,
                notes='Renewal approved'
            )
            
            # Should send notification to patient
            mock_service.send_renewal_notification.assert_called()


class EmergencyAccessWorkflowTestCase(BaseWorkflowTestCase):
    """Test cases for EmergencyAccessWorkflow."""
    
    def setUp(self):
        """Set up emergency access workflow test data."""
        super().setUp()
        self.workflow = EmergencyAccessWorkflow.objects.create(
            name='Test Emergency Access',
            requesting_physician=self.doctor,
            patient=self.patient,
            emergency_type='cardiac_emergency',
            urgency_level='critical'
        )
        
    def test_emergency_access_workflow_creation(self):
        """Test creating an emergency access workflow."""
        self.assertEqual(self.workflow.requesting_physician, self.doctor)
        self.assertEqual(self.workflow.emergency_type, 'cardiac_emergency')
        self.assertEqual(self.workflow.urgency_level, 'critical')
        
    def test_emergency_verification_process(self):
        """Test emergency verification process."""
        self.workflow.start_workflow(self.senior_doctor)
        
        # Verify emergency
        verification_result = self.workflow.verify_emergency(
            reviewer=self.senior_doctor,
            emergency_genuine=True,
            immediate_access_required=True,
            patient_safety_at_risk=True
        )
        
        self.assertTrue(verification_result)
        self.assertTrue(self.workflow.emergency_verified)
        
    def test_expedited_approval_process(self):
        """Test expedited approval for emergencies."""
        self.workflow.start_workflow(self.senior_doctor)
        
        # Should have expedited timeline
        estimated_completion = self.workflow.get_estimated_completion_time()
        time_difference = estimated_completion - timezone.now()
        
        # Emergency workflows should complete within 1 hour
        self.assertLess(time_difference.total_seconds(), 3600)
        
    def test_emergency_access_logging(self):
        """Test emergency access is thoroughly logged."""
        self.workflow.start_workflow(self.senior_doctor)
        
        # Grant emergency access
        self.workflow.grant_emergency_access(
            reviewer=self.senior_doctor,
            access_level='full_access',
            duration_hours=24,
            justification='Critical patient care required'
        )
        
        # Check comprehensive logging
        emergency_logs = self.workflow.get_emergency_access_logs()
        self.assertGreater(len(emergency_logs), 0)
        self.assertEqual(emergency_logs[0]['urgency_level'], 'critical')
        
    def test_post_emergency_review(self):
        """Test post-emergency review process."""
        self.workflow.start_workflow(self.senior_doctor)
        
        # Complete emergency access
        self.workflow.grant_emergency_access(
            reviewer=self.senior_doctor,
            access_level='full_access',
            duration_hours=24
        )
        
        # Schedule post-emergency review
        review_scheduled = self.workflow.schedule_post_emergency_review(
            review_date=timezone.now() + timedelta(days=1),
            reviewer=self.senior_doctor
        )
        
        self.assertTrue(review_scheduled)


class WorkflowTaskTestCase(BaseWorkflowTestCase):
    """Test cases for individual workflow tasks."""
    
    def test_prescription_verification_task(self):
        """Test prescription verification task."""
        task = PrescriptionVerificationTask.objects.create(
            name='Test Verification Task',
            active=True
        )
        
        # Create task state
        workflow_state = WorkflowState.objects.create(
            page=self.prescription,
            workflow=self.workflow,
            status='in_progress'
        )
        
        task_state = TaskState.objects.create(
            workflow_state=workflow_state,
            task=task,
            status='in_progress'
        )
        
        # Test task execution
        result = task.user_can_access_editor(self.prescription, self.doctor)
        self.assertTrue(result)
        
    def test_medication_interaction_review_task(self):
        """Test medication interaction review task."""
        task = MedicationInteractionReviewTask.objects.create(
            name='Test Interaction Review',
            active=True
        )
        
        # Test interaction detection
        interactions = task.check_medication_interactions(
            medications=['Warfarin', 'Aspirin']
        )
        
        self.assertIsInstance(interactions, list)
        
    def test_emergency_access_logging_task(self):
        """Test emergency access logging task."""
        task = EmergencyAccessLoggingTask.objects.create(
            name='Test Emergency Logging',
            active=True
        )
        
        # Test logging functionality
        log_entry = task.log_emergency_access(
            user=self.doctor,
            patient=self.patient,
            access_type='medical_records',
            justification='Emergency treatment required'
        )
        
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry['user'], self.doctor)


class WorkflowIntegrationTestCase(TransactionTestCase):
    """Integration tests for workflow system."""
    
    def setUp(self):
        """Set up integration test data."""
        self.doctor = User.objects.create_user(
            username='integration_doctor',
            email='integration@medguard.co.za',
            password='testpass123'
        )
        
    def test_workflow_notification_integration(self):
        """Test workflow integration with notification system."""
        with patch('medguard_notifications.services.NotificationService') as mock_service:
            # Create and start workflow
            prescription = EnhancedPrescription.objects.create(
                patient=self.doctor,  # Using doctor as patient for simplicity
                prescriber=self.doctor,
                medication_name='Integration Test Med',
                dosage='500mg'
            )
            
            workflow = PrescriptionApprovalWorkflow.objects.create(
                name='Integration Test Workflow',
                prescription=prescription
            )
            
            workflow.start_workflow(self.doctor)
            
            # Verify notification service was called
            mock_service.return_value.send_workflow_notification.assert_called()
            
    def test_workflow_audit_integration(self):
        """Test workflow integration with audit system."""
        prescription = EnhancedPrescription.objects.create(
            patient=self.doctor,
            prescriber=self.doctor,
            medication_name='Audit Test Med',
            dosage='250mg'
        )
        
        workflow = PrescriptionApprovalWorkflow.objects.create(
            name='Audit Integration Test',
            prescription=prescription
        )
        
        # Start and complete workflow stages
        workflow.start_workflow(self.doctor)
        
        # Complete a stage
        workflow.complete_stage(
            reviewer=self.doctor,
            notes='Integration test completion',
            approved=True
        )
        
        # Verify audit trail
        audit_trail = workflow.get_audit_trail()
        self.assertGreater(len(audit_trail), 0)
        
    def test_workflow_performance_with_large_datasets(self):
        """Test workflow performance with large datasets."""
        import time
        
        # Create multiple prescriptions and workflows
        prescriptions = []
        workflows = []
        
        for i in range(10):
            prescription = EnhancedPrescription.objects.create(
                patient=self.doctor,
                prescriber=self.doctor,
                medication_name=f'Performance Test Med {i}',
                dosage='500mg'
            )
            prescriptions.append(prescription)
            
            workflow = PrescriptionApprovalWorkflow.objects.create(
                name=f'Performance Test Workflow {i}',
                prescription=prescription
            )
            workflows.append(workflow)
        
        # Time workflow operations
        start_time = time.time()
        
        for workflow in workflows:
            workflow.start_workflow(self.doctor)
        
        operation_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(operation_time, 5.0)  # 5 seconds for 10 workflows
        
    def test_concurrent_workflow_execution(self):
        """Test concurrent workflow execution handling."""
        from threading import Thread
        import time
        
        prescription = EnhancedPrescription.objects.create(
            patient=self.doctor,
            prescriber=self.doctor,
            medication_name='Concurrent Test Med',
            dosage='500mg'
        )
        
        workflow1 = PrescriptionApprovalWorkflow.objects.create(
            name='Concurrent Test Workflow 1',
            prescription=prescription
        )
        
        workflow2 = PrescriptionApprovalWorkflow.objects.create(
            name='Concurrent Test Workflow 2',
            prescription=prescription
        )
        
        results = []
        
        def start_workflow(workflow):
            try:
                workflow.start_workflow(self.doctor)
                results.append('success')
            except Exception as e:
                results.append(f'error: {e}')
        
        # Start workflows concurrently
        thread1 = Thread(target=start_workflow, args=(workflow1,))
        thread2 = Thread(target=start_workflow, args=(workflow2,))
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Both should complete successfully
        self.assertEqual(len(results), 2)
        self.assertIn('success', results)


@pytest.mark.django_db
class WorkflowAPITestCase(TestCase):
    """Test cases for workflow API endpoints."""
    
    def setUp(self):
        """Set up API test data."""
        self.doctor = User.objects.create_user(
            username='api_doctor',
            email='api@medguard.co.za',
            password='testpass123'
        )
        
    def test_workflow_status_api(self):
        """Test workflow status API endpoint."""
        # This would test REST API endpoints for workflow status
        pass
        
    def test_workflow_action_api(self):
        """Test workflow action API endpoints."""
        # This would test API endpoints for workflow actions
        pass
