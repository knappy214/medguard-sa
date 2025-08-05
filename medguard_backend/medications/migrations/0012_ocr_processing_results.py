# Generated manually for MedGuard SA OCR processing result storage
from django.db import migrations, models
import django.db.models.deletion
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0011_prescription_workflow_states'),
    ]

    operations = [
        # Create OCRProcessingResult model
        migrations.CreateModel(
            name='OCRProcessingResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('processing_status', models.CharField(
                    choices=[
                        ('pending', _('Pending')),
                        ('processing', _('Processing')),
                        ('completed', _('Completed')),
                        ('failed', _('Failed')),
                        ('cancelled', _('Cancelled'))
                    ],
                    default='pending',
                    max_length=20,
                    help_text=_('Status of OCR processing')
                )),
                ('processing_priority', models.CharField(
                    choices=[
                        ('low', _('Low')),
                        ('medium', _('Medium')),
                        ('high', _('High')),
                        ('urgent', _('Urgent'))
                    ],
                    default='medium',
                    max_length=10,
                    help_text=_('Priority level for processing')
                )),
                ('processing_started_at', models.DateTimeField(blank=True, null=True, help_text=_('When processing started'))),
                ('processing_completed_at', models.DateTimeField(blank=True, null=True, help_text=_('When processing completed'))),
                ('processing_duration_seconds', models.PositiveIntegerField(blank=True, null=True, help_text=_('Processing duration in seconds'))),
                ('ocr_engine_used', models.CharField(blank=True, max_length=100, help_text=_('OCR engine used for processing'))),
                ('ocr_engine_version', models.CharField(blank=True, max_length=50, help_text=_('Version of OCR engine used'))),
                ('confidence_score', models.FloatField(blank=True, null=True, help_text=_('Overall confidence score (0-1)'))),
                ('extracted_text', models.TextField(blank=True, help_text=_('Raw extracted text from image'))),
                ('processed_text', models.TextField(blank=True, help_text=_('Processed and cleaned text'))),
                ('text_blocks', models.JSONField(default=list, help_text=_('Text blocks with coordinates and confidence scores'))),
                ('detected_language', models.CharField(blank=True, max_length=10, help_text=_('Detected language of the text'))),
                ('language_confidence', models.FloatField(blank=True, null=True, help_text=_('Confidence in language detection'))),
                ('image_quality_score', models.FloatField(blank=True, null=True, help_text=_('Quality score of the input image'))),
                ('image_metadata', models.JSONField(default=dict, help_text=_('Metadata about the input image'))),
                ('processing_errors', models.JSONField(default=list, help_text=_('List of errors encountered during processing'))),
                ('processing_warnings', models.JSONField(default=list, help_text=_('List of warnings during processing'))),
                ('processing_notes', models.TextField(blank=True, help_text=_('Additional notes about processing'))),
                ('retry_count', models.PositiveIntegerField(default=0, help_text=_('Number of processing attempts'))),
                ('max_retries', models.PositiveIntegerField(default=3, help_text=_('Maximum number of retry attempts'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this OCR result was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this OCR result was last updated'))),
            ],
            options={
                'verbose_name': _('OCR Processing Result'),
                'verbose_name_plural': _('OCR Processing Results'),
                'db_table': 'ocr_processing_results',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create PrescriptionImage model
        migrations.CreateModel(
            name='PrescriptionImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_file', models.ImageField(upload_to='prescriptions/images/', help_text=_('Prescription image file'))),
                ('image_type', models.CharField(
                    choices=[
                        ('original', _('Original Image')),
                        ('processed', _('Processed Image')),
                        ('enhanced', _('Enhanced Image')),
                        ('cropped', _('Cropped Image')),
                        ('annotated', _('Annotated Image'))
                    ],
                    default='original',
                    max_length=20,
                    help_text=_('Type of prescription image')
                )),
                ('image_format', models.CharField(blank=True, max_length=10, help_text=_('Image format (JPEG, PNG, etc.)'))),
                ('image_size_bytes', models.PositiveIntegerField(blank=True, null=True, help_text=_('Size of image file in bytes'))),
                ('image_width', models.PositiveIntegerField(blank=True, null=True, help_text=_('Width of image in pixels'))),
                ('image_height', models.PositiveIntegerField(blank=True, null=True, help_text=_('Height of image in pixels'))),
                ('image_resolution_dpi', models.PositiveIntegerField(blank=True, null=True, help_text=_('Image resolution in DPI'))),
                ('image_quality_score', models.FloatField(blank=True, null=True, help_text=_('Quality score of the image'))),
                ('image_metadata', models.JSONField(default=dict, help_text=_('Metadata about the image'))),
                ('upload_source', models.CharField(
                    choices=[
                        ('web_upload', _('Web Upload')),
                        ('mobile_camera', _('Mobile Camera')),
                        ('mobile_gallery', _('Mobile Gallery')),
                        ('email_attachment', _('Email Attachment')),
                        ('api_upload', _('API Upload')),
                        ('scanner', _('Scanner'))
                    ],
                    max_length=20,
                    help_text=_('Source of the image upload')
                )),
                ('upload_device_info', models.JSONField(default=dict, help_text=_('Information about the upload device'))),
                ('upload_location', models.CharField(blank=True, max_length=200, help_text=_('Location where image was uploaded'))),
                ('upload_ip_address', models.GenericIPAddressField(blank=True, null=True, help_text=_('IP address of upload'))),
                ('upload_user_agent', models.TextField(blank=True, help_text=_('User agent of upload'))),
                ('is_processed', models.BooleanField(default=False, help_text=_('Whether image has been processed'))),
                ('processing_priority', models.CharField(
                    choices=[
                        ('low', _('Low')),
                        ('medium', _('Medium')),
                        ('high', _('High')),
                        ('urgent', _('Urgent'))
                    ],
                    default='medium',
                    max_length=10,
                    help_text=_('Priority for processing this image')
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this image was uploaded'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this image was last updated'))),
            ],
            options={
                'verbose_name': _('Prescription Image'),
                'verbose_name_plural': _('Prescription Images'),
                'db_table': 'prescription_images',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create TextExtractionResult model
        migrations.CreateModel(
            name='TextExtractionResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('extraction_type', models.CharField(
                    choices=[
                        ('full_text', _('Full Text Extraction')),
                        ('structured_data', _('Structured Data Extraction')),
                        ('field_specific', _('Field-Specific Extraction')),
                        ('medication_list', _('Medication List Extraction')),
                        ('patient_info', _('Patient Information Extraction')),
                        ('doctor_info', _('Doctor Information Extraction'))
                    ],
                    max_length=20,
                    help_text=_('Type of text extraction performed')
                )),
                ('extraction_status', models.CharField(
                    choices=[
                        ('pending', _('Pending')),
                        ('in_progress', _('In Progress')),
                        ('completed', _('Completed')),
                        ('failed', _('Failed')),
                        ('partial', _('Partial Success'))
                    ],
                    default='pending',
                    max_length=20,
                    help_text=_('Status of text extraction')
                )),
                ('extracted_data', models.JSONField(default=dict, help_text=_('Extracted structured data'))),
                ('confidence_scores', models.JSONField(default=dict, help_text=_('Confidence scores for extracted fields'))),
                ('validation_results', models.JSONField(default=dict, help_text=_('Validation results for extracted data'))),
                ('extraction_errors', models.JSONField(default=list, help_text=_('Errors encountered during extraction'))),
                ('extraction_warnings', models.JSONField(default=list, help_text=_('Warnings during extraction'))),
                ('extraction_notes', models.TextField(blank=True, help_text=_('Notes about the extraction process'))),
                ('extraction_duration_seconds', models.PositiveIntegerField(blank=True, null=True, help_text=_('Extraction duration in seconds'))),
                ('extraction_algorithm', models.CharField(blank=True, max_length=100, help_text=_('Algorithm used for extraction'))),
                ('extraction_algorithm_version', models.CharField(blank=True, max_length=50, help_text=_('Version of extraction algorithm'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this extraction result was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this extraction result was last updated'))),
            ],
            options={
                'verbose_name': _('Text Extraction Result'),
                'verbose_name_plural': _('Text Extraction Results'),
                'db_table': 'text_extraction_results',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create ImageProcessingJob model
        migrations.CreateModel(
            name='ImageProcessingJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_id', models.CharField(max_length=100, unique=True, help_text=_('Unique job identifier'))),
                ('job_type', models.CharField(
                    choices=[
                        ('ocr_processing', _('OCR Processing')),
                        ('image_enhancement', _('Image Enhancement')),
                        ('text_extraction', _('Text Extraction')),
                        ('prescription_parsing', _('Prescription Parsing')),
                        ('quality_assessment', _('Quality Assessment')),
                        ('batch_processing', _('Batch Processing'))
                    ],
                    max_length=20,
                    help_text=_('Type of processing job')
                )),
                ('job_status', models.CharField(
                    choices=[
                        ('queued', _('Queued')),
                        ('running', _('Running')),
                        ('completed', _('Completed')),
                        ('failed', _('Failed')),
                        ('cancelled', _('Cancelled')),
                        ('paused', _('Paused'))
                    ],
                    default='queued',
                    max_length=20,
                    help_text=_('Status of the processing job')
                )),
                ('job_priority', models.CharField(
                    choices=[
                        ('low', _('Low')),
                        ('medium', _('Medium')),
                        ('high', _('High')),
                        ('urgent', _('Urgent'))
                    ],
                    default='medium',
                    max_length=10,
                    help_text=_('Priority of the job')
                )),
                ('job_parameters', models.JSONField(default=dict, help_text=_('Parameters for the processing job'))),
                ('job_result', models.JSONField(default=dict, help_text=_('Result of the processing job'))),
                ('job_errors', models.JSONField(default=list, help_text=_('Errors encountered during job execution'))),
                ('job_warnings', models.JSONField(default=list, help_text=_('Warnings during job execution'))),
                ('job_progress', models.FloatField(default=0.0, help_text=_('Progress percentage (0-100)'))),
                ('job_started_at', models.DateTimeField(blank=True, null=True, help_text=_('When job started'))),
                ('job_completed_at', models.DateTimeField(blank=True, null=True, help_text=_('When job completed'))),
                ('job_duration_seconds', models.PositiveIntegerField(blank=True, null=True, help_text=_('Job duration in seconds'))),
                ('worker_node', models.CharField(blank=True, max_length=100, help_text=_('Worker node that processed the job'))),
                ('retry_count', models.PositiveIntegerField(default=0, help_text=_('Number of retry attempts'))),
                ('max_retries', models.PositiveIntegerField(default=3, help_text=_('Maximum number of retries'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this job was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this job was last updated'))),
            ],
            options={
                'verbose_name': _('Image Processing Job'),
                'verbose_name_plural': _('Image Processing Jobs'),
                'db_table': 'image_processing_jobs',
                'ordering': ['-created_at'],
            },
        ),
        
        # Add foreign key relationships
        migrations.AddField(
            model_name='ocrprocessingresult',
            name='prescription_image',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='ocr_results',
                to='medications.prescriptionimage',
                help_text=_('Prescription image this OCR result belongs to')
            ),
        ),
        migrations.AddField(
            model_name='textextractionresult',
            name='ocr_result',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='text_extractions',
                to='medications.ocrprocessingresult',
                help_text=_('OCR result this text extraction is based on')
            ),
        ),
        migrations.AddField(
            model_name='imageprocessingjob',
            name='prescription_image',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='processing_jobs',
                to='medications.prescriptionimage',
                help_text=_('Prescription image this job processes')
            ),
        ),
        
        # Create indexes for performance
        migrations.AddIndex(
            model_name='ocrprocessingresult',
            index=models.Index(fields=['processing_status'], name='ocr_processing_status_idx'),
        ),
        migrations.AddIndex(
            model_name='ocrprocessingresult',
            index=models.Index(fields=['processing_priority'], name='ocr_processing_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='ocrprocessingresult',
            index=models.Index(fields=['processing_started_at'], name='ocr_processing_started_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionimage',
            index=models.Index(fields=['is_processed'], name='prescription_image_processed_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionimage',
            index=models.Index(fields=['processing_priority'], name='prescription_image_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionimage',
            index=models.Index(fields=['upload_source'], name='prescription_image_source_idx'),
        ),
        migrations.AddIndex(
            model_name='textextractionresult',
            index=models.Index(fields=['extraction_type'], name='text_extraction_type_idx'),
        ),
        migrations.AddIndex(
            model_name='textextractionresult',
            index=models.Index(fields=['extraction_status'], name='text_extraction_status_idx'),
        ),
        migrations.AddIndex(
            model_name='imageprocessingjob',
            index=models.Index(fields=['job_status'], name='image_job_status_idx'),
        ),
        migrations.AddIndex(
            model_name='imageprocessingjob',
            index=models.Index(fields=['job_priority'], name='image_job_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='imageprocessingjob',
            index=models.Index(fields=['job_type'], name='image_job_type_idx'),
        ),
        migrations.AddIndex(
            model_name='imageprocessingjob',
            index=models.Index(fields=['job_started_at'], name='image_job_started_idx'),
        ),
    ] 