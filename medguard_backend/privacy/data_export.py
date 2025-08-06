# -*- coding: utf-8 -*-
"""
MedGuard SA - Data Export Engine

Continuation of wagtail_privacy.py for data export functionality.
This module contains the DataExporter and DataExportManager classes.
"""

import json
import csv
import xml.etree.ElementTree as ET
from io import StringIO, BytesIO
import zipfile
import hashlib
import os
from typing import Dict, Any, List, Optional
import logging

from django.conf import settings
from django.apps import apps
from django.utils import timezone
from django.template.loader import render_to_string

from .wagtail_privacy import DataExportRequest, DataExportTemplate, DataAnonymizer

logger = logging.getLogger(__name__)


class DataExporter:
    """
    Core data export engine for generating compliant data exports.
    
    Handles the actual data extraction, formatting, and file generation
    for GDPR and POPIA compliance exports.
    """
    
    def __init__(self, export_request: DataExportRequest):
        """Initialize exporter with a specific export request."""
        self.export_request = export_request
        self.template = export_request.template
        self.patient = export_request.patient
        
    def generate_export(self) -> str:
        """Generate the complete data export and return file path."""
        try:
            # Mark request as processing
            self.export_request.status = 'processing'
            self.export_request.save(update_fields=['status'])
            
            # Collect data from all specified models
            export_data = self._collect_patient_data()
            
            # Apply anonymization if required
            if self.template.anonymize_data and self.template.anonymization_profile:
                export_data = self._anonymize_export_data(export_data)
            
            # Generate export file
            file_path = self._generate_export_file(export_data)
            
            # Calculate file hash and size
            file_hash, file_size = self._calculate_file_metrics(file_path)
            
            # Update export request
            self.export_request.status = 'completed'
            self.export_request.completed_at = timezone.now()
            self.export_request.export_file_path = file_path
            self.export_request.export_file_hash = file_hash
            self.export_request.file_size_bytes = file_size
            self.export_request.total_records = self._count_total_records(export_data)
            self.export_request.save()
            
            logger.info(
                f"Data export completed for request {self.export_request.request_id}. "
                f"File: {file_path}, Records: {self.export_request.total_records}"
            )
            
            return file_path
            
        except Exception as e:
            # Mark request as failed
            self.export_request.status = 'failed'
            self.export_request.error_message = str(e)
            self.export_request.save(update_fields=['status', 'error_message'])
            
            logger.error(
                f"Data export failed for request {self.export_request.request_id}: {e}"
            )
            raise
    
    def _collect_patient_data(self) -> Dict[str, Any]:
        """Collect all patient data according to template configuration."""
        export_data = {
            'metadata': self._generate_metadata(),
            'patient_info': self._get_patient_basic_info(),
            'models': {}
        }
        
        # Collect data from specified models
        for model_path in self.template.included_models:
            try:
                app_label, model_name = model_path.split('.')
                model_class = apps.get_model(app_label, model_name)
                
                # Get patient-related records
                records = self._get_model_records(model_class)
                
                if records:
                    export_data['models'][model_path] = {
                        'model_name': model_name,
                        'count': len(records),
                        'records': records
                    }
                    
            except (ValueError, LookupError) as e:
                logger.warning(f"Could not load model {model_path}: {e}")
                continue
        
        return export_data
    
    def _get_patient_basic_info(self) -> Dict[str, Any]:
        """Get basic patient information."""
        patient_info = {
            'id': self.patient.id,
            'username': self.patient.username,
            'email': self.patient.email,
            'first_name': self.patient.first_name,
            'last_name': self.patient.last_name,
            'date_joined': self.patient.date_joined.isoformat(),
            'last_login': self.patient.last_login.isoformat() if self.patient.last_login else None,
            'is_active': self.patient.is_active,
        }
        
        # Remove excluded fields
        for field in self.template.excluded_fields:
            if field in patient_info:
                del patient_info[field]
        
        return patient_info
    
    def _get_model_records(self, model_class) -> List[Dict[str, Any]]:
        """Get records from a model for the patient."""
        records = []
        
        # Try different field names to find patient relationship
        patient_fields = ['patient', 'user', 'created_by', 'owner']
        queryset = None
        
        for field_name in patient_fields:
            if hasattr(model_class, field_name):
                filter_kwargs = {field_name: self.patient}
                
                # Apply date range filter if specified
                if self.export_request.date_range_start or self.export_request.date_range_end:
                    date_field = self._get_date_field(model_class)
                    if date_field:
                        if self.export_request.date_range_start:
                            filter_kwargs[f"{date_field}__gte"] = self.export_request.date_range_start
                        if self.export_request.date_range_end:
                            filter_kwargs[f"{date_field}__lte"] = self.export_request.date_range_end
                
                try:
                    queryset = model_class.objects.filter(**filter_kwargs)
                    break
                except Exception as e:
                    logger.debug(f"Failed to query {model_class.__name__} with {field_name}: {e}")
                    continue
        
        if not queryset:
            return records
        
        # Convert queryset to dictionaries
        for obj in queryset:
            record = {}
            for field in obj._meta.fields:
                if field.name not in self.template.excluded_fields:
                    value = getattr(obj, field.name)
                    
                    # Handle special field types
                    if hasattr(value, 'isoformat'):  # DateTime fields
                        value = value.isoformat()
                    elif hasattr(value, 'url'):  # File fields
                        value = value.url if value else None
                    elif hasattr(value, '__str__'):
                        value = str(value)
                    
                    record[field.name] = value
            
            records.append(record)
        
        return records
    
    def _get_date_field(self, model_class) -> Optional[str]:
        """Get the primary date field for a model."""
        date_fields = ['created_at', 'date_created', 'created', 'updated_at', 'date_modified']
        
        for field_name in date_fields:
            if hasattr(model_class, field_name):
                return field_name
        
        return None
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate export metadata."""
        metadata = {
            'export_request_id': self.export_request.request_id,
            'export_type': self.template.get_compliance_type_display(),
            'export_format': self.template.get_export_format_display(),
            'patient_id': self.patient.id,
            'requested_by': self.export_request.requested_by.username if self.export_request.requested_by else None,
            'request_type': self.export_request.get_request_type_display(),
            'legal_basis': self.export_request.legal_basis,
            'purpose': self.export_request.purpose,
            'generated_at': timezone.now().isoformat(),
            'date_range': {
                'start': self.export_request.date_range_start.isoformat() if self.export_request.date_range_start else None,
                'end': self.export_request.date_range_end.isoformat() if self.export_request.date_range_end else None,
            },
            'anonymized': self.template.anonymize_data,
            'verification': {
                'identity_verified': self.export_request.requester_identity_verified,
                'verification_method': self.export_request.verification_method,
            },
            'compliance_info': {
                'gdpr_compliant': True,
                'popia_compliant': True,
                'retention_period': '30 days',
                'data_controller': 'MedGuard SA',
            }
        }
        
        return metadata
    
    def _anonymize_export_data(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply anonymization to export data."""
        if not self.template.anonymization_profile:
            return export_data
        
        anonymizer = DataAnonymizer(self.template.anonymization_profile)
        
        # Anonymize patient basic info
        if 'patient_info' in export_data:
            export_data['patient_info'] = anonymizer.anonymize_record(
                export_data['patient_info']
            )
        
        # Anonymize model records
        if 'models' in export_data:
            for model_path, model_data in export_data['models'].items():
                anonymized_records = []
                for record in model_data['records']:
                    anonymized_record = anonymizer.anonymize_record(record)
                    anonymized_records.append(anonymized_record)
                
                export_data['models'][model_path]['records'] = anonymized_records
        
        return export_data
    
    def _generate_export_file(self, export_data: Dict[str, Any]) -> str:
        """Generate the export file in the specified format."""
        # Create exports directory if it doesn't exist
        export_dir = os.path.join(settings.MEDIA_ROOT, 'privacy_exports')
        os.makedirs(export_dir, exist_ok=True)
        
        # Generate filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.export_request.request_id}_{timestamp}"
        
        if self.template.export_format == 'json':
            return self._generate_json_export(export_data, export_dir, filename)
        elif self.template.export_format == 'csv':
            return self._generate_csv_export(export_data, export_dir, filename)
        elif self.template.export_format == 'xml':
            return self._generate_xml_export(export_data, export_dir, filename)
        elif self.template.export_format == 'html':
            return self._generate_html_export(export_data, export_dir, filename)
        else:
            # Default to JSON
            return self._generate_json_export(export_data, export_dir, filename)
    
    def _generate_json_export(self, export_data: Dict[str, Any], export_dir: str, filename: str) -> str:
        """Generate JSON format export."""
        file_path = os.path.join(export_dir, f"{filename}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        return file_path
    
    def _generate_csv_export(self, export_data: Dict[str, Any], export_dir: str, filename: str) -> str:
        """Generate CSV format export as a ZIP file with multiple CSV files."""
        zip_path = os.path.join(export_dir, f"{filename}.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add metadata file
            metadata_csv = StringIO()
            metadata_writer = csv.writer(metadata_csv)
            metadata_writer.writerow(['Key', 'Value'])
            
            for key, value in export_data['metadata'].items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        metadata_writer.writerow([f"{key}.{sub_key}", sub_value])
                else:
                    metadata_writer.writerow([key, value])
            
            zipf.writestr('metadata.csv', metadata_csv.getvalue())
            
            # Add patient info
            if 'patient_info' in export_data:
                patient_csv = StringIO()
                patient_writer = csv.writer(patient_csv)
                
                patient_info = export_data['patient_info']
                patient_writer.writerow(patient_info.keys())
                patient_writer.writerow(patient_info.values())
                
                zipf.writestr('patient_info.csv', patient_csv.getvalue())
            
            # Add model data
            for model_path, model_data in export_data.get('models', {}).items():
                if model_data['records']:
                    model_csv = StringIO()
                    model_writer = csv.writer(model_csv)
                    
                    # Write headers
                    headers = list(model_data['records'][0].keys())
                    model_writer.writerow(headers)
                    
                    # Write data
                    for record in model_data['records']:
                        model_writer.writerow([record.get(h, '') for h in headers])
                    
                    zipf.writestr(f"{model_data['model_name']}.csv", model_csv.getvalue())
        
        return zip_path
    
    def _generate_xml_export(self, export_data: Dict[str, Any], export_dir: str, filename: str) -> str:
        """Generate XML format export."""
        file_path = os.path.join(export_dir, f"{filename}.xml")
        
        root = ET.Element('DataExport')
        
        # Add metadata
        metadata_elem = ET.SubElement(root, 'Metadata')
        for key, value in export_data['metadata'].items():
            if isinstance(value, dict):
                sub_elem = ET.SubElement(metadata_elem, key)
                for sub_key, sub_value in value.items():
                    sub_sub_elem = ET.SubElement(sub_elem, sub_key)
                    sub_sub_elem.text = str(sub_value)
            else:
                elem = ET.SubElement(metadata_elem, key)
                elem.text = str(value)
        
        # Add patient info
        if 'patient_info' in export_data:
            patient_elem = ET.SubElement(root, 'PatientInfo')
            for key, value in export_data['patient_info'].items():
                elem = ET.SubElement(patient_elem, key)
                elem.text = str(value)
        
        # Add model data
        models_elem = ET.SubElement(root, 'Models')
        for model_path, model_data in export_data.get('models', {}).items():
            model_elem = ET.SubElement(models_elem, 'Model')
            model_elem.set('name', model_data['model_name'])
            model_elem.set('count', str(model_data['count']))
            
            records_elem = ET.SubElement(model_elem, 'Records')
            for record in model_data['records']:
                record_elem = ET.SubElement(records_elem, 'Record')
                for key, value in record.items():
                    field_elem = ET.SubElement(record_elem, key)
                    field_elem.text = str(value) if value is not None else ''
        
        # Write to file
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        
        return file_path
    
    def _generate_html_export(self, export_data: Dict[str, Any], export_dir: str, filename: str) -> str:
        """Generate HTML format export."""
        file_path = os.path.join(export_dir, f"{filename}.html")
        
        # Use Django template if available, otherwise generate basic HTML
        try:
            html_content = render_to_string('privacy/data_export.html', {
                'export_data': export_data,
                'request': self.export_request,
                'template': self.template
            })
        except:
            # Fallback to basic HTML generation
            html_content = self._generate_basic_html(export_data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return file_path
    
    def _generate_basic_html(self, export_data: Dict[str, Any]) -> str:
        """Generate basic HTML export."""
        html = ['<!DOCTYPE html>']
        html.append('<html><head><meta charset="utf-8">')
        html.append('<title>Data Export Report</title>')
        html.append('<style>body{font-family:Arial,sans-serif;margin:40px;}</style>')
        html.append('</head><body>')
        
        html.append('<h1>Personal Data Export Report</h1>')
        
        # Metadata
        html.append('<h2>Export Information</h2>')
        html.append('<table border="1" cellpadding="5">')
        for key, value in export_data['metadata'].items():
            if isinstance(value, dict):
                html.append(f'<tr><td><strong>{key}</strong></td><td>{json.dumps(value, indent=2)}</td></tr>')
            else:
                html.append(f'<tr><td><strong>{key}</strong></td><td>{value}</td></tr>')
        html.append('</table>')
        
        # Patient info
        if 'patient_info' in export_data:
            html.append('<h2>Personal Information</h2>')
            html.append('<table border="1" cellpadding="5">')
            for key, value in export_data['patient_info'].items():
                html.append(f'<tr><td><strong>{key}</strong></td><td>{value}</td></tr>')
            html.append('</table>')
        
        # Model data
        for model_path, model_data in export_data.get('models', {}).items():
            html.append(f'<h2>{model_data["model_name"]} ({model_data["count"]} records)</h2>')
            
            if model_data['records']:
                html.append('<table border="1" cellpadding="5">')
                
                # Headers
                headers = list(model_data['records'][0].keys())
                html.append('<tr>')
                for header in headers:
                    html.append(f'<th>{header}</th>')
                html.append('</tr>')
                
                # Data rows
                for record in model_data['records']:
                    html.append('<tr>')
                    for header in headers:
                        value = record.get(header, '')
                        html.append(f'<td>{value}</td>')
                    html.append('</tr>')
                
                html.append('</table>')
        
        html.append('</body></html>')
        return ''.join(html)
    
    def _calculate_file_metrics(self, file_path: str) -> tuple:
        """Calculate file hash and size."""
        # Calculate SHA-256 hash
        hash_obj = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        file_hash = hash_obj.hexdigest()
        file_size = os.path.getsize(file_path)
        
        return file_hash, file_size
    
    def _count_total_records(self, export_data: Dict[str, Any]) -> int:
        """Count total records in export."""
        total = 1  # Patient info counts as 1 record
        
        for model_data in export_data.get('models', {}).values():
            total += model_data['count']
        
        return total


class DataExportManager:
    """
    Manager for handling data export operations and compliance.
    
    Provides high-level methods for creating, processing, and managing
    data export requests.
    """
    
    @staticmethod
    def create_export_request(
        patient,
        template: DataExportTemplate,
        requested_by=None,
        request_type: str = 'patient_self',
        legal_basis: str = "",
        purpose: str = "",
        date_range_start=None,
        date_range_end=None
    ) -> DataExportRequest:
        """Create a new data export request."""
        
        export_request = DataExportRequest.objects.create(
            patient=patient,
            requested_by=requested_by or patient,
            request_type=request_type,
            template=template,
            legal_basis=legal_basis,
            purpose=purpose,
            date_range_start=date_range_start,
            date_range_end=date_range_end
        )
        
        logger.info(
            f"Created data export request {export_request.request_id} "
            f"for patient {patient.id} using template {template.name}"
        )
        
        return export_request
    
    @staticmethod
    def process_export_request(export_request: DataExportRequest) -> str:
        """Process an export request and generate the export file."""
        exporter = DataExporter(export_request)
        return exporter.generate_export()
    
    @staticmethod
    def get_patient_export_requests(patient) -> List[DataExportRequest]:
        """Get all export requests for a patient."""
        return DataExportRequest.objects.filter(patient=patient).order_by('-created_at')
    
    @staticmethod
    def cleanup_expired_exports():
        """Clean up expired export requests and files."""
        expired_requests = DataExportRequest.objects.filter(
            expiry_date__lt=timezone.now(),
            status='completed'
        )
        
        cleaned_count = 0
        
        for request in expired_requests:
            # Delete export file if it exists
            if request.export_file_path and os.path.exists(request.export_file_path):
                try:
                    os.remove(request.export_file_path)
                    logger.info(f"Deleted expired export file: {request.export_file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete export file {request.export_file_path}: {e}")
            
            # Update request status
            request.status = 'expired'
            request.export_file_path = ""
            request.save(update_fields=['status', 'export_file_path'])
            
            cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} expired export requests")
        return cleaned_count
    
    @staticmethod
    def generate_compliance_report() -> Dict[str, Any]:
        """Generate compliance report for data exports."""
        from datetime import timedelta
        
        total_requests = DataExportRequest.objects.count()
        
        report = {
            'generated_at': timezone.now(),
            'total_requests': total_requests,
            'status_breakdown': {},
            'request_type_breakdown': {},
            'template_usage': {},
            'compliance_metrics': {}
        }
        
        # Status breakdown
        for status, status_name in DataExportRequest.REQUEST_STATUS:
            count = DataExportRequest.objects.filter(status=status).count()
            report['status_breakdown'][status] = {
                'name': status_name,
                'count': count,
                'percentage': (count / total_requests * 100) if total_requests > 0 else 0
            }
        
        # Request type breakdown
        for req_type, type_name in DataExportRequest.REQUEST_TYPES:
            count = DataExportRequest.objects.filter(request_type=req_type).count()
            report['request_type_breakdown'][req_type] = {
                'name': type_name,
                'count': count
            }
        
        # Template usage
        for template in DataExportTemplate.objects.filter(is_active=True):
            count = DataExportRequest.objects.filter(template=template).count()
            report['template_usage'][template.name] = {
                'compliance_type': template.get_compliance_type_display(),
                'format': template.get_export_format_display(),
                'usage_count': count
            }
        
        # Compliance metrics
        recent_requests = DataExportRequest.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        report['compliance_metrics'] = {
            'requests_last_30_days': recent_requests.count(),
            'identity_verification_rate': (
                recent_requests.filter(requester_identity_verified=True).count() / 
                recent_requests.count() * 100
            ) if recent_requests.count() > 0 else 0,
        }
        
        return report