# Generated manually for MedGuard SA final relationships and indexes
from django.db import migrations, models
import django.db.models.deletion
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0015_prescription_renewal_reminders'),
    ]

    operations = [
        # Add missing foreign key relationships
        
        # Link PrescriptionImage to Prescription
        migrations.AddField(
            model_name='prescriptionimage',
            name='prescription',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='images',
                to='medications.prescription',
                help_text=_('Prescription this image belongs to')
            ),
        ),
        
        # Link PrescriptionImage to PrescriptionPatient
        migrations.AddField(
            model_name='prescriptionimage',
            name='patient',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='prescription_images',
                to='medications.prescriptionpatient',
                help_text=_('Patient for this prescription image')
            ),
        ),
        
        # Link PrescriptionMedication to ICD10Code for conditions
        migrations.AddField(
            model_name='prescriptionmedication',
            name='icd10_codes',
            field=models.ManyToManyField(
                blank=True,
                to='medications.icd10code',
                help_text=_('ICD-10 codes for conditions this medication treats')
            ),
        ),
        
        # Link Prescription to ICD10Code for primary diagnosis
        migrations.AddField(
            model_name='prescription',
            name='primary_diagnosis',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='medications.icd10code',
                help_text=_('Primary diagnosis for this prescription')
            ),
        ),
        
        # Link Prescription to ICD10Code for secondary diagnoses
        migrations.AddField(
            model_name='prescription',
            name='secondary_diagnoses',
            field=models.ManyToManyField(
                blank=True,
                related_name='secondary_prescriptions',
                to='medications.icd10code',
                help_text=_('Secondary diagnoses for this prescription')
            ),
        ),
        
        # Create additional indexes for performance optimization
        
        # Medication indexes
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['name', 'generic_name'], name='medication_name_generic_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['manufacturer', 'medication_type'], name='medication_manufacturer_type_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['expiration_date', 'pill_count'], name='medication_expiry_stock_idx'),
        ),
        
        # Prescription indexes
        migrations.AddIndex(
            model_name='prescription',
            index=models.Index(fields=['patient', 'status'], name='prescription_patient_status_idx'),
        ),
        migrations.AddIndex(
            model_name='prescription',
            index=models.Index(fields=['doctor', 'prescription_date'], name='prescription_doctor_date_idx'),
        ),
        migrations.AddIndex(
            model_name='prescription',
            index=models.Index(fields=['prescription_type', 'priority'], name='prescription_type_priority_idx'),
        ),
        
        # PrescriptionMedication indexes
        migrations.AddIndex(
            model_name='prescriptionmedication',
            index=models.Index(fields=['prescription', 'status'], name='prescription_medication_status_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionmedication',
            index=models.Index(fields=['medication_name', 'strength'], name='prescription_medication_name_strength_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionmedication',
            index=models.Index(fields=['timing', 'as_needed'], name='prescription_medication_timing_idx'),
        ),
        
        # PrescriptionDoctor indexes
        migrations.AddIndex(
            model_name='prescriptiondoctor',
            index=models.Index(fields=['name', 'practice_number'], name='doctor_name_practice_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptiondoctor',
            index=models.Index(fields=['specialty'], name='doctor_specialty_idx'),
        ),
        
        # PrescriptionPatient indexes
        migrations.AddIndex(
            model_name='prescriptionpatient',
            index=models.Index(fields=['name', 'id_number'], name='patient_name_id_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionpatient',
            index=models.Index(fields=['medical_aid_number', 'medical_aid_scheme'], name='patient_medical_aid_scheme_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionpatient',
            index=models.Index(fields=['date_of_birth'], name='patient_dob_idx'),
        ),
        
        # ICD10Code indexes
        migrations.AddIndex(
            model_name='icd10code',
            index=models.Index(fields=['code', 'category'], name='icd10_code_category_idx'),
        ),
        migrations.AddIndex(
            model_name='icd10code',
            index=models.Index(fields=['description'], name='icd10_description_idx'),
        ),
        
        # Workflow state indexes
        migrations.AddIndex(
            model_name='prescriptionworkflowstate',
            index=models.Index(fields=['prescription', 'state_changed_at'], name='workflow_prescription_changed_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionworkflowstate',
            index=models.Index(fields=['state_changed_by'], name='workflow_changed_by_idx'),
        ),
        
        # Review indexes
        migrations.AddIndex(
            model_name='prescriptionreview',
            index=models.Index(fields=['prescription', 'review_type'], name='review_prescription_type_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionreview',
            index=models.Index(fields=['reviewer_name', 'review_date'], name='review_reviewer_date_idx'),
        ),
        
        # Dispensing indexes
        migrations.AddIndex(
            model_name='prescriptiondispensing',
            index=models.Index(fields=['prescription', 'dispensing_status'], name='dispensing_prescription_status_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptiondispensing',
            index=models.Index(fields=['dispenser_name', 'dispensing_date'], name='dispensing_dispenser_date_idx'),
        ),
        
        # Validation indexes
        migrations.AddIndex(
            model_name='prescriptionvalidation',
            index=models.Index(fields=['prescription', 'validation_type'], name='validation_prescription_type_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionvalidation',
            index=models.Index(fields=['validation_status', 'validation_date'], name='validation_status_date_idx'),
        ),
        
        # Audit indexes
        migrations.AddIndex(
            model_name='prescriptionaudit',
            index=models.Index(fields=['prescription', 'audit_type'], name='audit_prescription_type_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionaudit',
            index=models.Index(fields=['performed_by', 'performed_at'], name='audit_performer_date_idx'),
        ),
        
        # OCR and Image Processing indexes
        migrations.AddIndex(
            model_name='ocrprocessingresult',
            index=models.Index(fields=['prescription_image', 'processing_status'], name='ocr_image_status_idx'),
        ),
        migrations.AddIndex(
            model_name='ocrprocessingresult',
            index=models.Index(fields=['confidence_score'], name='ocr_confidence_idx'),
        ),
        
        migrations.AddIndex(
            model_name='prescriptionimage',
            index=models.Index(fields=['prescription', 'image_type'], name='image_prescription_type_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionimage',
            index=models.Index(fields=['upload_source', 'created_at'], name='image_source_created_idx'),
        ),
        
        migrations.AddIndex(
            model_name='textextractionresult',
            index=models.Index(fields=['ocr_result', 'extraction_type'], name='extraction_ocr_type_idx'),
        ),
        migrations.AddIndex(
            model_name='textextractionresult',
            index=models.Index(fields=['extraction_status', 'extraction_date'], name='extraction_status_date_idx'),
        ),
        
        migrations.AddIndex(
            model_name='imageprocessingjob',
            index=models.Index(fields=['prescription_image', 'job_type'], name='job_image_type_idx'),
        ),
        migrations.AddIndex(
            model_name='imageprocessingjob',
            index=models.Index(fields=['job_status', 'job_priority'], name='job_status_priority_idx'),
        ),
        
        # Interaction indexes
        migrations.AddIndex(
            model_name='medicationinteraction',
            index=models.Index(fields=['medication1', 'medication2', 'severity_level'], name='interaction_meds_severity_idx'),
        ),
        migrations.AddIndex(
            model_name='medicationinteraction',
            index=models.Index(fields=['interaction_type', 'is_active'], name='interaction_type_active_idx'),
        ),
        
        migrations.AddIndex(
            model_name='patientmedicationinteraction',
            index=models.Index(fields=['patient', 'interaction', 'interaction_status'], name='patient_interaction_status_idx'),
        ),
        migrations.AddIndex(
            model_name='patientmedicationinteraction',
            index=models.Index(fields=['risk_assessment', 'interaction_date'], name='patient_risk_date_idx'),
        ),
        
        migrations.AddIndex(
            model_name='interactioncheck',
            index=models.Index(fields=['patient', 'check_type'], name='check_patient_type_idx'),
        ),
        migrations.AddIndex(
            model_name='interactioncheck',
            index=models.Index(fields=['check_status', 'check_date'], name='check_status_date_idx'),
        ),
        
        migrations.AddIndex(
            model_name='interactionalert',
            index=models.Index(fields=['patient', 'alert_type'], name='alert_patient_type_idx'),
        ),
        migrations.AddIndex(
            model_name='interactionalert',
            index=models.Index(fields=['alert_priority', 'alert_status'], name='alert_priority_status_idx'),
        ),
        
        # Stock Analytics indexes
        migrations.AddIndex(
            model_name='stockreport',
            index=models.Index(fields=['report_type', 'report_period_start', 'report_period_end'], name='report_type_period_range_idx'),
        ),
        migrations.AddIndex(
            model_name='stockreport',
            index=models.Index(fields=['generated_by', 'report_date'], name='report_generator_date_idx'),
        ),
        
        migrations.AddIndex(
            model_name='stocktrend',
            index=models.Index(fields=['medication', 'trend_type', 'trend_date'], name='trend_medication_type_date_idx'),
        ),
        migrations.AddIndex(
            model_name='stocktrend',
            index=models.Index(fields=['usage_rate', 'turnover_rate'], name='trend_usage_turnover_idx'),
        ),
        
        migrations.AddIndex(
            model_name='stockforecast',
            index=models.Index(fields=['medication', 'forecast_type', 'forecast_date'], name='forecast_medication_type_date_idx'),
        ),
        migrations.AddIndex(
            model_name='stockforecast',
            index=models.Index(fields=['confidence_level', 'predicted_stockout_date'], name='forecast_confidence_stockout_idx'),
        ),
        
        migrations.AddIndex(
            model_name='stockalertrule',
            index=models.Index(fields=['medication', 'rule_type'], name='alert_rule_medication_type_idx'),
        ),
        migrations.AddIndex(
            model_name='stockalertrule',
            index=models.Index(fields=['is_active', 'alert_priority'], name='alert_rule_active_priority_idx'),
        ),
        
        migrations.AddIndex(
            model_name='stockperformance',
            index=models.Index(fields=['medication', 'performance_metric', 'performance_date'], name='performance_medication_metric_date_idx'),
        ),
        migrations.AddIndex(
            model_name='stockperformance',
            index=models.Index(fields=['performance_status', 'performance_trend'], name='performance_status_trend_idx'),
        ),
        
        # Renewal and Reminder indexes
        migrations.AddIndex(
            model_name='prescriptionreminder',
            index=models.Index(fields=['patient', 'reminder_type', 'reminder_status'], name='reminder_patient_type_status_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionreminder',
            index=models.Index(fields=['reminder_date', 'reminder_priority'], name='reminder_date_priority_idx'),
        ),
        
        migrations.AddIndex(
            model_name='renewalrequest',
            index=models.Index(fields=['patient', 'request_status'], name='renewal_request_patient_status_idx'),
        ),
        migrations.AddIndex(
            model_name='renewalrequest',
            index=models.Index(fields=['original_prescription_number', 'request_date'], name='renewal_request_prescription_date_idx'),
        ),
        
        migrations.AddIndex(
            model_name='renewalschedule',
            index=models.Index(fields=['patient', 'schedule_type'], name='renewal_schedule_patient_type_idx'),
        ),
        migrations.AddIndex(
            model_name='renewalschedule',
            index=models.Index(fields=['next_renewal_date', 'is_active'], name='renewal_schedule_next_active_idx'),
        ),
        
        migrations.AddIndex(
            model_name='renewalhistory',
            index=models.Index(fields=['patient', 'renewal_type'], name='renewal_history_patient_type_idx'),
        ),
        migrations.AddIndex(
            model_name='renewalhistory',
            index=models.Index(fields=['renewal_date', 'renewal_method'], name='renewal_history_date_method_idx'),
        ),
        
        migrations.AddIndex(
            model_name='notificationtemplate',
            index=models.Index(fields=['template_type', 'template_language'], name='template_type_language_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationtemplate',
            index=models.Index(fields=['is_active', 'template_name'], name='template_active_name_idx'),
        ),
        
        # Create unique constraints
        migrations.AddConstraint(
            model_name='medicationinteraction',
            constraint=models.UniqueConstraint(
                fields=['medication1', 'medication2'],
                name='unique_medication_interaction'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='prescriptionmedication',
            constraint=models.UniqueConstraint(
                fields=['prescription', 'medication_number'],
                name='unique_prescription_medication_order'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='stocktrend',
            constraint=models.UniqueConstraint(
                fields=['medication', 'trend_date', 'trend_type'],
                name='unique_stock_trend'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='stockforecast',
            constraint=models.UniqueConstraint(
                fields=['medication', 'forecast_date', 'forecast_type'],
                name='unique_stock_forecast'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='stockperformance',
            constraint=models.UniqueConstraint(
                fields=['medication', 'performance_date', 'performance_metric'],
                name='unique_stock_performance'
            ),
        ),
        
        # Add check constraints for data integrity
        migrations.AddConstraint(
            model_name='medication',
            constraint=models.CheckConstraint(
                check=models.Q(pill_count__gte=0),
                name='medication_pill_count_non_negative'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='medication',
            constraint=models.CheckConstraint(
                check=models.Q(low_stock_threshold__gt=0),
                name='medication_low_stock_threshold_positive'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='prescriptionmedication',
            constraint=models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name='prescription_medication_quantity_positive'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='prescriptionmedication',
            constraint=models.CheckConstraint(
                check=models.Q(medication_number__gte=1, medication_number__lte=21),
                name='prescription_medication_number_range'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='stocktransaction',
            constraint=models.CheckConstraint(
                check=models.Q(stock_after__gte=0),
                name='stock_transaction_after_non_negative'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='medicationinteraction',
            constraint=models.CheckConstraint(
                check=models.Q(medication1_id__lt=models.F('medication2_id')),
                name='medication_interaction_order'
            ),
        ),
    ] 