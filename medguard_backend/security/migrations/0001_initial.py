# Generated manually for HIPAA compliance security models

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('users', '0001_initial'),
    ]

    operations = [
        # Audit Log Model
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('create', 'Create'), ('read', 'Read'), ('update', 'Update'), ('delete', 'Delete'), ('export', 'Export'), ('import', 'Import'), ('login', 'Login'), ('logout', 'Logout'), ('access_denied', 'Access Denied'), ('password_change', 'Password Change'), ('permission_change', 'Permission Change'), ('data_anonymization', 'Data Anonymization'), ('breach_attempt', 'Breach Attempt')], help_text='Type of action performed', max_length=50)),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='low', help_text='Severity level of the action', max_length=20)),
                ('object_id', models.PositiveIntegerField(help_text='ID of the object')),
                ('object_repr', models.CharField(help_text='String representation of the object', max_length=200)),
                ('changes', models.JSONField(blank=True, default=dict, help_text='JSON representation of changes made')),
                ('previous_values', models.JSONField(blank=True, default=dict, help_text='Previous values before changes')),
                ('new_values', models.JSONField(blank=True, default=dict, help_text='New values after changes')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address of the request', null=True)),
                ('user_agent', models.TextField(blank=True, help_text='User agent string')),
                ('request_path', models.CharField(blank=True, help_text='Request path/URL', max_length=500)),
                ('request_method', models.CharField(blank=True, help_text='HTTP method used', max_length=10)),
                ('session_id', models.CharField(blank=True, help_text='Session ID', max_length=100)),
                ('description', models.TextField(blank=True, help_text='Human-readable description of the action')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional metadata about the action')),
                ('timestamp', models.DateTimeField(auto_now_add=True, help_text='When the action occurred')),
                ('retention_date', models.DateTimeField(blank=True, help_text='Date until which this log should be retained', null=True)),
                ('is_anonymized', models.BooleanField(default=False, help_text='Whether this log entry has been anonymized')),
                ('content_type', models.ForeignKey(help_text='Content type of the object', on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(blank=True, help_text='User who performed the action', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to='users.user')),
            ],
            options={
                'verbose_name': 'Audit Log',
                'verbose_name_plural': 'Audit Logs',
                'db_table': 'audit_logs',
                'ordering': ['-timestamp'],
            },
        ),
        
        # Anonymized Dataset Model
        migrations.CreateModel(
            name='AnonymizedDataset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the anonymized dataset', max_length=200)),
                ('description', models.TextField(blank=True, help_text='Description of the dataset and its purpose')),
                ('dataset_type', models.CharField(choices=[('patient_data', 'Patient Data'), ('medication_data', 'Medication Data'), ('audit_data', 'Audit Data'), ('research_data', 'Research Data'), ('reporting_data', 'Reporting Data')], help_text='Type of dataset', max_length=20)),
                ('anonymization_method', models.CharField(choices=[('k_anonymity', 'K-Anonymity'), ('l_diversity', 'L-Diversity'), ('t_closeness', 'T-Closeness'), ('differential_privacy', 'Differential Privacy'), ('hashing', 'Hashing'), ('generalization', 'Generalization')], default='k_anonymity', help_text='Method used for anonymization', max_length=30)),
                ('status', models.CharField(choices=[('created', 'Created'), ('processing', 'Processing'), ('completed', 'Completed'), ('expired', 'Expired'), ('deleted', 'Deleted')], default='created', help_text='Current status of the dataset', max_length=20)),
                ('original_record_count', models.PositiveIntegerField(help_text='Number of records in original dataset')),
                ('anonymized_record_count', models.PositiveIntegerField(help_text='Number of records in anonymized dataset')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When the dataset was created')),
                ('expires_at', models.DateTimeField(help_text='When the dataset expires and should be deleted')),
                ('deleted_at', models.DateTimeField(blank=True, help_text='When the dataset was deleted', null=True)),
                ('hipaa_compliant', models.BooleanField(default=True, help_text='Whether the dataset is HIPAA compliant')),
                ('popia_compliant', models.BooleanField(default=True, help_text='Whether the dataset is POPIA compliant')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional metadata about the dataset')),
                ('file_path', models.CharField(blank=True, help_text='Path to the anonymized dataset file', max_length=500)),
                ('file_size', models.PositiveIntegerField(blank=True, help_text='Size of the dataset file in bytes', null=True)),
                ('authorized_users', models.ManyToManyField(blank=True, help_text='Users authorized to access this dataset', related_name='authorized_datasets', to='users.user')),
                ('created_by', models.ForeignKey(help_text='User who created the dataset', on_delete=django.db.models.deletion.CASCADE, related_name='created_datasets', to='users.user')),
            ],
            options={
                'verbose_name': 'Anonymized Dataset',
                'verbose_name_plural': 'Anonymized Datasets',
                'db_table': 'security_anonymized_datasets',
                'ordering': ['-created_at'],
            },
        ),
        
        # Dataset Access Log Model
        migrations.CreateModel(
            name='DatasetAccessLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_type', models.CharField(choices=[('view', 'View'), ('download', 'Download'), ('export', 'Export'), ('delete', 'Delete')], help_text='Type of access', max_length=20)),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address of the access', null=True)),
                ('user_agent', models.TextField(blank=True, help_text='User agent string')),
                ('timestamp', models.DateTimeField(auto_now_add=True, help_text='When the access occurred')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional metadata about the access')),
                ('dataset', models.ForeignKey(help_text='Dataset that was accessed', on_delete=django.db.models.deletion.CASCADE, related_name='access_logs', to='security.anonymizeddataset')),
                ('user', models.ForeignKey(help_text='User who accessed the dataset', on_delete=django.db.models.deletion.CASCADE, related_name='dataset_access_logs', to='users.user')),
            ],
            options={
                'verbose_name': 'Dataset Access Log',
                'verbose_name_plural': 'Dataset Access Logs',
                'db_table': 'security_dataset_access_logs',
                'ordering': ['-timestamp'],
            },
        ),
        
        # Indexes for performance
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', 'action'], name='audit_logs_user_action_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['content_type', 'object_id'], name='audit_logs_content_type_object_id_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['action', 'timestamp'], name='audit_logs_action_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['severity', 'timestamp'], name='audit_logs_severity_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['ip_address', 'timestamp'], name='audit_logs_ip_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['timestamp'], name='audit_logs_timestamp_idx'),
        ),
        
        migrations.AddIndex(
            model_name='anonymizeddataset',
            index=models.Index(fields=['dataset_type', 'status'], name='anonymized_datasets_type_status_idx'),
        ),
        migrations.AddIndex(
            model_name='anonymizeddataset',
            index=models.Index(fields=['created_at'], name='anonymized_datasets_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='anonymizeddataset',
            index=models.Index(fields=['expires_at'], name='anonymized_datasets_expires_at_idx'),
        ),
        migrations.AddIndex(
            model_name='anonymizeddataset',
            index=models.Index(fields=['created_by'], name='anonymized_datasets_created_by_idx'),
        ),
        
        migrations.AddIndex(
            model_name='datasetaccesslog',
            index=models.Index(fields=['dataset', 'user'], name='dataset_access_logs_dataset_user_idx'),
        ),
        migrations.AddIndex(
            model_name='datasetaccesslog',
            index=models.Index(fields=['access_type', 'timestamp'], name='dataset_access_logs_access_type_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='datasetaccesslog',
            index=models.Index(fields=['timestamp'], name='dataset_access_logs_timestamp_idx'),
        ),
    ] 