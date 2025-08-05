# Generated manually for MedGuard SA - Add OCR processing fields and metadata
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0002_add_prescription_fields'),
    ]

    operations = [
        # Add OCR processing fields to Medication model
        
        # OCR processing status
        migrations.AddField(
            model_name='medication',
            name='ocr_processing_status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('pending', _('Pending')),
                    ('processing', _('Processing')),
                    ('completed', _('Completed')),
                    ('failed', _('Failed')),
                    ('retry', _('Retry Required')),
                ],
                default='pending',
                help_text=_('Status of OCR processing for medication images')
            ),
        ),
        
        # OCR processing priority
        migrations.AddField(
            model_name='medication',
            name='ocr_processing_priority',
            field=models.CharField(
                max_length=10,
                choices=[
                    ('low', _('Low')),
                    ('medium', _('Medium')),
                    ('high', _('High')),
                    ('urgent', _('Urgent')),
                ],
                default='medium',
                help_text=_('Priority level for OCR processing')
            ),
        ),
        
        # OCR processing attempts
        migrations.AddField(
            model_name='medication',
            name='ocr_processing_attempts',
            field=models.PositiveIntegerField(
                default=0,
                help_text=_('Number of OCR processing attempts made')
            ),
        ),
        
        # OCR processing last attempt
        migrations.AddField(
            model_name='medication',
            name='ocr_processing_last_attempt',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('Last time OCR processing was attempted')
            ),
        ),
        
        # OCR processing error
        migrations.AddField(
            model_name='medication',
            name='ocr_processing_error',
            field=models.TextField(
                blank=True,
                help_text=_('Last error message from OCR processing')
            ),
        ),
        
        # OCR extracted text
        migrations.AddField(
            model_name='medication',
            name='ocr_extracted_text',
            field=models.TextField(
                blank=True,
                help_text=_('Raw text extracted from medication image via OCR')
            ),
        ),
        
        # OCR confidence score
        migrations.AddField(
            model_name='medication',
            name='ocr_confidence_score',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Confidence score of OCR extraction (0-1)')
            ),
        ),
        
        # OCR processing metadata
        migrations.AddField(
            model_name='medication',
            name='ocr_metadata',
            field=models.JSONField(
                default=dict,
                help_text=_('Metadata about OCR processing (engine used, processing time, etc.)')
            ),
        ),
        
        # OCR extracted fields
        migrations.AddField(
            model_name='medication',
            name='ocr_extracted_fields',
            field=models.JSONField(
                default=dict,
                help_text=_('Structured data extracted from OCR (medication name, dosage, etc.)')
            ),
        ),
        
        # OCR processing engine
        migrations.AddField(
            model_name='medication',
            name='ocr_engine_used',
            field=models.CharField(
                max_length=50,
                blank=True,
                help_text=_('OCR engine used for processing')
            ),
        ),
        
        # OCR processing time
        migrations.AddField(
            model_name='medication',
            name='ocr_processing_time_ms',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Time taken for OCR processing in milliseconds')
            ),
        ),
        
        # OCR image quality score
        migrations.AddField(
            model_name='medication',
            name='ocr_image_quality_score',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Quality score of image for OCR processing (0-1)')
            ),
        ),
        
        # OCR language detection
        migrations.AddField(
            model_name='medication',
            name='ocr_detected_language',
            field=models.CharField(
                max_length=10,
                blank=True,
                help_text=_('Language detected in the image during OCR')
            ),
        ),
        
        # OCR text regions
        migrations.AddField(
            model_name='medication',
            name='ocr_text_regions',
            field=models.JSONField(
                default=list,
                help_text=_('Bounding boxes and text regions detected in image')
            ),
        ),
        
        # OCR validation status
        migrations.AddField(
            model_name='medication',
            name='ocr_validation_status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('not_validated', _('Not Validated')),
                    ('pending_validation', _('Pending Validation')),
                    ('validated', _('Validated')),
                    ('validation_failed', _('Validation Failed')),
                    ('manual_review', _('Manual Review Required')),
                ],
                default='not_validated',
                help_text=_('Status of OCR result validation')
            ),
        ),
        
        # OCR validation notes
        migrations.AddField(
            model_name='medication',
            name='ocr_validation_notes',
            field=models.TextField(
                blank=True,
                help_text=_('Notes from OCR validation process')
            ),
        ),
        
        # OCR validation confidence
        migrations.AddField(
            model_name='medication',
            name='ocr_validation_confidence',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Confidence score after validation (0-1)')
            ),
        ),
        
        # OCR processing queue position
        migrations.AddField(
            model_name='medication',
            name='ocr_queue_position',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Position in OCR processing queue')
            ),
        ),
        
        # OCR processing scheduled time
        migrations.AddField(
            model_name='medication',
            name='ocr_scheduled_time',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('Scheduled time for OCR processing')
            ),
        ),
        
        # OCR processing retry count
        migrations.AddField(
            model_name='medication',
            name='ocr_retry_count',
            field=models.PositiveIntegerField(
                default=0,
                help_text=_('Number of times OCR processing has been retried')
            ),
        ),
        
        # OCR processing max retries
        migrations.AddField(
            model_name='medication',
            name='ocr_max_retries',
            field=models.PositiveIntegerField(
                default=3,
                help_text=_('Maximum number of OCR processing retries allowed')
            ),
        ),
        
        # OCR processing timeout
        migrations.AddField(
            model_name='medication',
            name='ocr_timeout_seconds',
            field=models.PositiveIntegerField(
                default=300,
                help_text=_('Timeout for OCR processing in seconds')
            ),
        ),
        
        # OCR processing batch ID
        migrations.AddField(
            model_name='medication',
            name='ocr_batch_id',
            field=models.CharField(
                max_length=100,
                blank=True,
                help_text=_('Batch ID for OCR processing')
            ),
        ),
        
        # OCR processing worker ID
        migrations.AddField(
            model_name='medication',
            name='ocr_worker_id',
            field=models.CharField(
                max_length=100,
                blank=True,
                help_text=_('Worker ID that processed this OCR task')
            ),
        ),
        
        # OCR processing cost
        migrations.AddField(
            model_name='medication',
            name='ocr_processing_cost',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=6,
                null=True,
                blank=True,
                help_text=_('Cost of OCR processing in currency units')
            ),
        ),
        
        # OCR processing currency
        migrations.AddField(
            model_name='medication',
            name='ocr_processing_currency',
            field=models.CharField(
                max_length=3,
                default='USD',
                help_text=_('Currency for OCR processing cost')
            ),
        ),
        
        # Add indexes for OCR fields
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['ocr_processing_status'], name='medication_ocr_status_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['ocr_processing_priority'], name='medication_ocr_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['ocr_validation_status'], name='medication_ocr_validation_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['ocr_scheduled_time'], name='medication_ocr_scheduled_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['ocr_batch_id'], name='medication_ocr_batch_idx'),
        ),
    ] 