"""
Prescription OCR Services
Core OCR processing services for prescription image analysis.
"""
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.utils.translation import gettext as _
from PIL import Image as PILImage
import pytesseract
from .models import PrescriptionOCRResult, OCRTemplate

logger = logging.getLogger(__name__)


class PrescriptionOCRService:
    """Service for processing prescription images with OCR."""
    
    def __init__(self):
        """Initialize the OCR service."""
        self.tesseract_config = getattr(
            settings, 
            'TESSERACT_CONFIG', 
            '--oem 3 --psm 6'
        )
    
    def process_prescription_image(
        self, 
        image_path: str, 
        template_id: Optional[int] = None
    ) -> Dict:
        """
        Process a prescription image and extract medication data.
        
        Args:
            image_path: Path to the prescription image
            template_id: Optional OCR template ID for better accuracy
            
        Returns:
            Dictionary containing extracted data and confidence scores
        """
        try:
            # Load and preprocess image
            image = PILImage.open(image_path)
            processed_image = self._preprocess_image(image)
            
            # Extract text using OCR
            extracted_text = pytesseract.image_to_string(
                processed_image, 
                config=self.tesseract_config
            )
            
            # Get confidence score
            confidence_data = pytesseract.image_to_data(
                processed_image, 
                output_type=pytesseract.Output.DICT
            )
            confidence_score = self._calculate_confidence(confidence_data)
            
            # Parse extracted text
            parsed_data = self._parse_prescription_text(
                extracted_text, 
                template_id
            )
            
            return {
                'success': True,
                'extracted_text': extracted_text,
                'confidence_score': confidence_score,
                'parsed_data': parsed_data,
                'processing_time': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'extracted_text': '',
                'confidence_score': 0.0,
                'parsed_data': {},
                'processing_time': datetime.now()
            }
    
    def _preprocess_image(self, image: PILImage) -> PILImage:
        """
        Preprocess image to improve OCR accuracy.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Resize if too small
        width, height = image.size
        if width < 800 or height < 600:
            scale_factor = max(800 / width, 600 / height)
            new_size = (int(width * scale_factor), int(height * scale_factor))
            image = image.resize(new_size, PILImage.LANCZOS)
        
        return image
    
    def _calculate_confidence(self, confidence_data: Dict) -> float:
        """
        Calculate average confidence score from OCR data.
        
        Args:
            confidence_data: OCR confidence data from pytesseract
            
        Returns:
            Average confidence score (0-1)
        """
        confidences = [
            conf for conf in confidence_data['conf'] 
            if conf > 0
        ]
        
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences) / 100.0
    
    def _parse_prescription_text(
        self, 
        text: str, 
        template_id: Optional[int] = None
    ) -> Dict:
        """
        Parse extracted text to identify medication data.
        
        Args:
            text: Raw OCR text
            template_id: Optional template for parsing
            
        Returns:
            Dictionary with parsed medication data
        """
        parsed_data = {
            'medication_name': '',
            'dosage': '',
            'frequency': '',
            'prescriber_name': '',
            'prescription_date': None,
            'patient_name': '',
            'pharmacy_info': ''
        }
        
        # Use template if provided
        if template_id:
            template = self._get_ocr_template(template_id)
            if template:
                return self._apply_template_parsing(text, template)
        
        # Default parsing patterns
        parsed_data.update(self._apply_default_patterns(text))
        
        return parsed_data
    
    def _get_ocr_template(self, template_id: int) -> Optional[OCRTemplate]:
        """Get OCR template by ID."""
        try:
            return OCRTemplate.objects.get(id=template_id, is_active=True)
        except OCRTemplate.DoesNotExist:
            return None
    
    def _apply_template_parsing(
        self, 
        text: str, 
        template: OCRTemplate
    ) -> Dict:
        """Apply template-based parsing to extract data."""
        parsed_data = {}
        
        for field, pattern in template.regex_patterns.items():
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    parsed_data[field] = match.group(1).strip()
                else:
                    parsed_data[field] = ''
            except Exception as e:
                logger.warning(f"Template pattern failed for {field}: {e}")
                parsed_data[field] = ''
        
        return parsed_data
    
    def _apply_default_patterns(self, text: str) -> Dict:
        """Apply default regex patterns for common prescription formats."""
        patterns = {
            'medication_name': [
                r'(?:medication|drug|rx)[\s:]+([a-zA-Z\s]+?)(?:\s+\d|$)',
                r'^([A-Z][a-zA-Z\s]+?)(?:\s+\d|\s+mg|\s+mcg)',
            ],
            'dosage': [
                r'(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?))',
                r'(?:take|dosage)[\s:]+(\d+(?:\.\d+)?\s*\w+)',
            ],
            'frequency': [
                r'(?:take|frequency)[\s:]+(.+?)(?:daily|weekly|monthly)',
                r'(\d+\s*(?:times?|x)\s*(?:daily|per day|a day))',
                r'(once|twice|three times|four times)\s*(?:daily|per day)',
            ],
            'prescriber_name': [
                r'(?:dr|doctor|prescriber)[\s.:]+([a-zA-Z\s.]+)',
                r'(?:signed|prescribed by)[\s:]+([a-zA-Z\s.]+)',
            ],
            'prescription_date': [
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(?:date|prescribed)[\s:]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ]
        }
        
        parsed_data = {}
        
        for field, field_patterns in patterns.items():
            parsed_data[field] = ''
            for pattern in field_patterns:
                try:
                    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                    if match:
                        parsed_data[field] = match.group(1).strip()
                        break
                except Exception as e:
                    logger.warning(f"Pattern matching failed for {field}: {e}")
                    continue
        
        return parsed_data
    
    def validate_ocr_result(self, ocr_result: Dict) -> Tuple[bool, List[str]]:
        """
        Validate OCR results for completeness and accuracy.
        
        Args:
            ocr_result: OCR processing result
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check confidence score
        if ocr_result.get('confidence_score', 0) < 0.7:
            issues.append(_("Low OCR confidence score"))
        
        # Check required fields
        parsed_data = ocr_result.get('parsed_data', {})
        required_fields = ['medication_name']
        
        for field in required_fields:
            if not parsed_data.get(field):
                issues.append(_(f"Missing required field: {field}"))
        
        # Validate medication name format
        med_name = parsed_data.get('medication_name', '')
        if med_name and not re.match(r'^[a-zA-Z\s]+$', med_name):
            issues.append(_("Invalid medication name format"))
        
        # Validate dosage format
        dosage = parsed_data.get('dosage', '')
        if dosage and not re.match(r'^\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?)$', dosage):
            issues.append(_("Invalid dosage format"))
        
        return len(issues) == 0, issues
