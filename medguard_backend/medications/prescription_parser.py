"""
Comprehensive prescription parser service for MedGuard SA.

This service handles South African prescription formats with:
- Doctor and patient information extraction
- 21-medication prescription parsing
- Complex instruction parsing (e.g., "Take three tablets three times a day")
- Brand name to generic mapping
- ICD-10 code extraction and condition mapping
- Multiple medication types (FlexPen, SolarStar Pen, tablets, cream)
- Quantity validation with proper parsing
- Timing instruction extraction
- "As needed" medication handling
- Repeat information processing
- Confidence scoring for all extracted fields
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, date, time
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence levels for extracted data."""
    HIGH = 0.9
    MEDIUM = 0.7
    LOW = 0.5
    VERY_LOW = 0.3


@dataclass
class ExtractedField:
    """Represents an extracted field with confidence scoring."""
    value: Any
    confidence: float
    source_text: str
    validation_errors: List[str] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []


class MedicationType(Enum):
    """Medication types found in prescriptions."""
    TABLET = "tablet"
    CAPSULE = "capsule"
    INJECTION = "injection"
    INHALER = "inhaler"
    CREAM = "cream"
    OINTMENT = "ointment"
    DROPS = "drops"
    PATCH = "patch"
    PEN = "pen"
    LIQUID = "liquid" 


class PrescriptionParser:
    """
    Comprehensive prescription parser for South African healthcare.
    
    Handles complex prescription formats with multiple medications,
    various instruction patterns, and comprehensive validation.
    """
    
    # Brand name to generic mappings for South African medications
    BRAND_TO_GENERIC = {
        # Diabetes medications
        'NOVORAPID': 'Insulin aspart',
        'LANTUS': 'Insulin glargine',
        'HUMALOG': 'Insulin lispro',
        'LEVEMIR': 'Insulin detemir',
        'TRESIBA': 'Insulin degludec',
        'VICTOZA': 'Liraglutide',
        'OZEMPIC': 'Semaglutide',
        'JARDIANCE': 'Empagliflozin',
        'FORXIGA': 'Dapagliflozin',
        'METFORMIN': 'Metformin',
        'GLUCOPHAGE': 'Metformin',
        'DIAMICRON': 'Gliclazide',
        'AMARYL': 'Glimepiride',
        
        # Cardiovascular medications
        'LIPITOR': 'Atorvastatin',
        'CRESTOR': 'Rosuvastatin',
        'ZOCOR': 'Simvastatin',
        'PLAVIX': 'Clopidogrel',
        'ASPIRIN': 'Acetylsalicylic acid',
        'DISPRIN': 'Acetylsalicylic acid',
        'ADCO-DOL': 'Paracetamol + Codeine',
        'STILPAINE': 'Paracetamol + Codeine',
        
        # Hypertension medications
        'COZAAR': 'Losartan',
        'DIOVAN': 'Valsartan',
        'MICARDIS': 'Telmisartan',
        'NORVASC': 'Amlodipine',
        'ADALAT': 'Nifedipine',
        'CARDURA': 'Doxazosin',
        'INDERAL': 'Propranolol',
        'TENORMIN': 'Atenolol',
        
        # Pain medications
        'PANADO': 'Paracetamol',
        'BRUFEN': 'Ibuprofen',
        'VOLTAREN': 'Diclofenac',
        'ARCOXIA': 'Etoricoxib',
        'TRAMADOL': 'Tramadol',
        
        # Respiratory medications
        'VENTOLIN': 'Salbutamol',
        'SERETIDE': 'Fluticasone + Salmeterol',
        'SYMBICORT': 'Budesonide + Formoterol',
        'SINGULAIR': 'Montelukast',
        'PULMICORT': 'Budesonide',
        
        # Mental health medications
        'PROZAC': 'Fluoxetine',
        'ZOLOFT': 'Sertraline',
        'CELEXA': 'Citalopram',
        'LEXAPRO': 'Escitalopram',
        'WELLBUTRIN': 'Bupropion',
        'RITALIN': 'Methylphenidate',
        'CONCERTA': 'Methylphenidate',
        'ADDERALL': 'Amphetamine + Dextroamphetamine',
        
        # Antibiotics
        'AUGMENTIN': 'Amoxicillin + Clavulanic acid',
        'ZITHROMAX': 'Azithromycin',
        'KLACID': 'Clarithromycin',
        'CIPRO': 'Ciprofloxacin',
        'FLAGYL': 'Metronidazole',
        
        # Other common medications
        'OMEPRAZOLE': 'Omeprazole',
        'LANSOPRAZOLE': 'Lansoprazole',
        'PANTOPRAZOLE': 'Pantoprazole',
        'RANITIDINE': 'Ranitidine',
        'ZANTAC': 'Ranitidine',
        'GAVISCON': 'Aluminium hydroxide + Magnesium carbonate',
        'MOVICOL': 'Macrogol',
        'LACTULOSE': 'Lactulose',
        'SENNA': 'Senna glycosides',
        'DULCOLAX': 'Bisacodyl',
    }
    
    # ICD-10 code mappings for South African healthcare
    ICD10_MAPPINGS = {
        # Diabetes mellitus
        'E10.4': 'Type 1 diabetes mellitus with neurological complications',
        'E11.4': 'Type 2 diabetes mellitus with neurological complications',
        'E11.9': 'Type 2 diabetes mellitus without complications',
        'E10.9': 'Type 1 diabetes mellitus without complications',
        'E13.4': 'Other specified diabetes mellitus with neurological complications',
        'E11.65': 'Type 2 diabetes mellitus with hyperglycemia',
        'E11.22': 'Type 2 diabetes mellitus with diabetic chronic kidney disease',
        
        # Mental and behavioral disorders
        'F90.9': 'Attention-deficit hyperactivity disorder, unspecified type',
        'F90.0': 'Attention-deficit hyperactivity disorder, predominantly inattentive type',
        'F90.1': 'Attention-deficit hyperactivity disorder, predominantly hyperactive type',
        'F32.9': 'Major depressive disorder, unspecified',
        'F41.9': 'Anxiety disorder, unspecified',
        'F33.9': 'Major depressive disorder, recurrent, unspecified',
        'F31.9': 'Bipolar affective disorder, unspecified',
        'F41.1': 'Generalized anxiety disorder',
        'F43.1': 'Post-traumatic stress disorder',
        
        # Cardiovascular diseases
        'I10': 'Essential (primary) hypertension',
        'I11.9': 'Hypertensive heart disease without heart failure',
        'I12.9': 'Hypertensive chronic kidney disease with stage 1 through stage 4 chronic kidney disease',
        'I25.10': 'Atherosclerotic heart disease of native coronary artery without angina pectoris',
        'I48.91': 'Unspecified atrial fibrillation',
        'I25.2': 'Old myocardial infarction',
        'I50.9': 'Heart failure, unspecified',
        'I63.9': 'Cerebral infarction, unspecified',
        
        # Respiratory diseases
        'J45.901': 'Unspecified asthma with (acute) exacerbation',
        'J44.9': 'Chronic obstructive pulmonary disease, unspecified',
        'J45.909': 'Unspecified asthma, uncomplicated',
        'J45.990': 'Exercise induced bronchospasm',
        'J44.1': 'Chronic obstructive pulmonary disease with (acute) exacerbation',
        'J45.20': 'Mild intermittent asthma, uncomplicated',
        'J45.30': 'Mild persistent asthma, uncomplicated',
        
        # Pain and musculoskeletal
        'M79.3': 'Sciatica, unspecified side',
        'R52.9': 'Pain, unspecified',
        'M54.5': 'Low back pain',
        'M79.1': 'Myalgia',
        'M15.9': 'Polyosteoarthritis, unspecified site',
        'M16.9': 'Osteoarthritis of hip, unspecified',
        'M17.9': 'Osteoarthritis of knee, unspecified',
        'M25.50': 'Pain in unspecified joint',
        
        # Infections
        'N39.0': 'Urinary tract infection, site not specified',
        'A09.9': 'Infectious gastroenteritis and colitis, unspecified',
        'J06.9': 'Acute upper respiratory infection, unspecified',
        'B20': 'Human immunodeficiency virus [HIV] disease',
        'B20.9': 'Human immunodeficiency virus [HIV] disease, unspecified',
        'A15.9': 'Respiratory tuberculosis unspecified, unspecified',
        
        # Other common conditions
        'Z51.11': 'Encounter for antineoplastic chemotherapy',
        'Z79.4': 'Long term (current) use of insulin',
        'Z79.899': 'Other long term (current) drug therapy',
        'Z00.00': 'Encounter for general adult medical examination without abnormal findings',
        'Z51.12': 'Encounter for antineoplastic immunotherapy',
        'Z79.01': 'Long term (current) use of anticoagulants',
        'Z79.02': 'Long term (current) use of antithrombotics/antiplatelets',
        'Z79.3': 'Long term (current) use of hormonal contraceptives',
    }
    
    # Complex instruction patterns
    COMPLEX_INSTRUCTION_PATTERNS = [
        # "Take three tablets three times a day" pattern
        r'take\s+(\d+)\s+(tablets?|capsules?|drops?|puffs?)\s+(\d+)\s+times?\s+(daily|a\s+day|per\s+day)',
        # "Take 2 tablets morning and evening" pattern
        r'take\s+(\d+)\s+(tablets?|capsules?|drops?|puffs?)\s+(morning|evening|night|noon|12h00)\s+and\s+(morning|evening|night|noon|12h00)',
        # "Take 1 tablet at 8h00 and 20h00" pattern
        r'take\s+(\d+)\s+(tablets?|capsules?|drops?|puffs?)\s+at\s+(\d{1,2}h\d{2})\s+and\s+(\d{1,2}h\d{2})',
        # "Inject 20 units once daily at bedtime" pattern
        r'inject\s+(\d+)\s+(units?|ml|mg)\s+once\s+daily\s+at\s+(bedtime|night|morning|noon)',
        # "Apply cream twice daily" pattern
        r'apply\s+(cream|ointment|gel)\s+(\d+)\s+times?\s+(daily|a\s+day)',
        # "Use inhaler as needed" pattern
        r'use\s+(inhaler|puffer)\s+(as\s+needed|as\s+required|prn|when\s+needed)',
    ]
    
    # Quantity patterns with validation
    QUANTITY_PATTERNS = [
        r'x\s*(\d+)',  # x 3, x 30, x 60, x 270
        r'(\d+)\s*(tablets?|capsules?|units?|ml|mg|mcg)',
        r'quantity:\s*(\d+)',
        r'qty:\s*(\d+)',
        r'(\d+)\s*(pcs|pieces)',
    ]
    
    # Timing patterns
    TIMING_PATTERNS = [
        (r'morning|am|before\s+breakfast|with\s+breakfast', 'morning'),
        (r'noon|midday|12h00|12:00|with\s+lunch', 'noon'),
        (r'evening|pm|before\s+bed|night|at\s+bedtime|with\s+dinner', 'night'),
        (r'(\d{1,2})h(\d{2})?|(\d{1,2}):(\d{2})', 'custom_time'),
        (r'twice\s+daily|two\s+times\s+daily|2x\s+daily|bid', 'twice_daily'),
        (r'three\s+times\s+daily|thrice\s+daily|3x\s+daily|tid', 'three_times_daily'),
        (r'four\s+times\s+daily|4x\s+daily|qid', 'four_times_daily'),
        (r'as\s+needed|as\s+required|prn|when\s+needed|when\s+required', 'as_needed'),
    ]
    
    # Repeat patterns
    REPEAT_PATTERNS = [
        r'\+?\s*(\d+)\s*repeats?',
        r'repeat\s*(\d+)\s*times?',
        r'(\d+)\s*refills?',
        r'refill\s*(\d+)\s*times?',
    ]
    
    # Medication type patterns
    MEDICATION_TYPE_PATTERNS = [
        (r'flexpen|flex\s*pen', MedicationType.PEN),
        (r'solarstar\s*pen|solar\s*star\s*pen', MedicationType.PEN),
        (r'tablets?', MedicationType.TABLET),
        (r'capsules?', MedicationType.CAPSULE),
        (r'cream|ointment', MedicationType.CREAM),
        (r'injection|inject', MedicationType.INJECTION),
        (r'inhaler|puffer', MedicationType.INHALER),
        (r'drops?', MedicationType.DROPS),
        (r'patch|patches', MedicationType.PATCH),
        (r'liquid|syrup', MedicationType.LIQUID),
    ] 
    
    @classmethod
    def parse_prescription(cls, prescription_text: str) -> Dict[str, Any]:
        """
        Parse a complete prescription with all required fields.
        
        Args:
            prescription_text: Raw prescription text
            
        Returns:
            Dictionary containing parsed prescription data with confidence scores
        """
        try:
            # Initialize result structure
            result = {
                'doctor_info': cls._extract_doctor_info(prescription_text),
                'patient_info': cls._extract_patient_info(prescription_text),
                'medications': cls._extract_medications(prescription_text),
                'icd10_codes': cls._extract_icd10_codes(prescription_text),
                'prescription_metadata': cls._extract_prescription_metadata(prescription_text),
                'overall_confidence': 0.0,
                'parsing_errors': [],
                'warnings': []
            }
            
            # Calculate overall confidence
            confidence_scores = []
            for section in ['doctor_info', 'patient_info', 'medications', 'icd10_codes']:
                if isinstance(result[section], ExtractedField):
                    confidence_scores.append(result[section].confidence)
                elif isinstance(result[section], list):
                    for item in result[section]:
                        if isinstance(item, ExtractedField):
                            confidence_scores.append(item.confidence)
            
            if confidence_scores:
                result['overall_confidence'] = sum(confidence_scores) / len(confidence_scores)
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing prescription: {e}")
            return {
                'error': str(e),
                'overall_confidence': 0.0,
                'parsing_errors': [str(e)]
            }
    
    @classmethod
    def _extract_doctor_info(cls, text: str) -> ExtractedField:
        """Extract doctor information from prescription text."""
        doctor_patterns = [
            r'dr\.?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'doctor\s*:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'prescribed\s+by\s*:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'physician\s*:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
        ]
        
        for pattern in doctor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return ExtractedField(
                    value=match.group(1).strip(),
                    confidence=ConfidenceLevel.HIGH.value,
                    source_text=match.group(0)
                )
        
        return ExtractedField(
            value=None,
            confidence=ConfidenceLevel.VERY_LOW.value,
            source_text="",
            validation_errors=["No doctor information found"]
        )
    
    @classmethod
    def _extract_patient_info(cls, text: str) -> ExtractedField:
        """Extract patient information from prescription text."""
        patient_patterns = [
            r'patient\s*:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'name\s*:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'id\s*:\s*(\d+)',
            r'date\s+of\s+birth\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]
        
        patient_info = {}
        confidence = ConfidenceLevel.MEDIUM.value
        
        for pattern in patient_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'name' in pattern.lower():
                    patient_info['name'] = match.group(1).strip()
                elif 'id' in pattern.lower():
                    patient_info['id'] = match.group(1).strip()
                elif 'birth' in pattern.lower():
                    patient_info['date_of_birth'] = match.group(1).strip()
        
        if patient_info:
            return ExtractedField(
                value=patient_info,
                confidence=confidence,
                source_text=text[:200]  # First 200 chars as source
            )
        
        return ExtractedField(
            value={},
            confidence=ConfidenceLevel.VERY_LOW.value,
            source_text="",
            validation_errors=["No patient information found"]
        )
    
    @classmethod
    def _extract_medications(cls, text: str) -> List[ExtractedField]:
        """Extract medications from prescription text."""
        medications = []
        
        # Split text into potential medication sections
        medication_sections = cls._split_into_medication_sections(text)
        
        for i, section in enumerate(medication_sections):
            if len(medications) >= 21:  # Limit to 21 medications
                break
                
            medication = cls._parse_single_medication(section, i + 1)
            if medication.value:  # Only add if medication was found
                medications.append(medication)
        
        return medications
    
    @classmethod
    def _split_into_medication_sections(cls, text: str) -> List[str]:
        """Split prescription text into individual medication sections."""
        # Split by numbered medication sections (1., 2., 3., etc.)
        sections = re.split(r'\n\s*(\d+)\.\s*', text)
        
        medication_sections = []
        for i in range(1, len(sections), 2):  # Skip the first empty section and take every other section
            if i + 1 < len(sections):
                # Combine the number and the medication text
                section_text = f"{sections[i]}. {sections[i+1]}"
                medication_sections.append(section_text.strip())
        
        # If no numbered sections found, try other patterns
        if not medication_sections:
            # Try bullet points
            sections = re.split(r'\n\s*[-*]\s*', text)
            medication_sections = [s.strip() for s in sections if s.strip()]
        
        # If still no sections, try medication name patterns
        if not medication_sections:
            # Look for medication names in all caps
            medication_names = re.findall(r'\n\s*([A-Z][A-Z\s]+)\s*\n', text)
            if medication_names:
                # Split by medication names
                sections = re.split(r'\n\s*[A-Z][A-Z\s]+\s*\n', text)
                medication_sections = [s.strip() for s in sections if s.strip()]
        
        return medication_sections
    
    @classmethod
    def _parse_single_medication(cls, section: str, medication_number: int) -> ExtractedField:
        """Parse a single medication section."""
        try:
            medication_data = {
                'medication_number': medication_number,
                'name': cls._extract_medication_name(section),
                'generic_name': cls._extract_generic_name(section),
                'strength': cls._extract_strength(section),
                'quantity': cls._extract_quantity(section),
                'instructions': cls._extract_instructions(section),
                'medication_type': cls._extract_medication_type(section),
                'timing': cls._extract_timing(section),
                'repeats': cls._extract_repeats(section),
                'as_needed': cls._extract_as_needed(section),
            }
            
            # Calculate confidence for this medication
            confidence_scores = []
            for field_name, field_value in medication_data.items():
                if isinstance(field_value, ExtractedField):
                    confidence_scores.append(field_value.confidence)
                elif field_value is not None:
                    confidence_scores.append(ConfidenceLevel.MEDIUM.value)
            
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            return ExtractedField(
                value=medication_data,
                confidence=overall_confidence,
                source_text=section
            )
            
        except Exception as e:
            logger.error(f"Error parsing medication {medication_number}: {e}")
            return ExtractedField(
                value=None,
                confidence=ConfidenceLevel.VERY_LOW.value,
                source_text=section,
                validation_errors=[str(e)]
            ) 
    
    @classmethod
    def _extract_medication_name(cls, text: str) -> ExtractedField:
        """Extract medication name from text."""
        # Look for brand names in our mapping
        text_upper = text.upper()
        for brand_name in cls.BRAND_TO_GENERIC.keys():
            if brand_name in text_upper:
                return ExtractedField(
                    value=brand_name.title(),
                    confidence=ConfidenceLevel.HIGH.value,
                    source_text=brand_name
                )
        
        # Look for common medication name patterns
        name_patterns = [
            r'([A-Z][A-Z\s]+)',  # All caps names
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # Title case names
            r'([A-Z][a-z]+)',  # Single word names
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                if len(name) > 2:  # Avoid very short matches
                    return ExtractedField(
                        value=name,
                        confidence=ConfidenceLevel.MEDIUM.value,
                        source_text=name
                    )
        
        return ExtractedField(
            value=None,
            confidence=ConfidenceLevel.VERY_LOW.value,
            source_text="",
            validation_errors=["No medication name found"]
        )
    
    @classmethod
    def _extract_generic_name(cls, text: str) -> ExtractedField:
        """Extract generic name from text."""
        # First check if we can map from brand name
        text_upper = text.upper()
        for brand_name, generic_name in cls.BRAND_TO_GENERIC.items():
            if brand_name in text_upper:
                return ExtractedField(
                    value=generic_name,
                    confidence=ConfidenceLevel.HIGH.value,
                    source_text=brand_name
                )
        
        # Look for generic name patterns
        generic_patterns = [
            r'generic\s*:\s*([A-Z][a-z\s]+)',
            r'\(([A-Z][a-z\s]+)\)',  # Parenthetical generic names
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+\(generic\)',
        ]
        
        for pattern in generic_patterns:
            match = re.search(pattern, text)
            if match:
                return ExtractedField(
                    value=match.group(1).strip(),
                    confidence=ConfidenceLevel.MEDIUM.value,
                    source_text=match.group(0)
                )
        
        return ExtractedField(
            value=None,
            confidence=ConfidenceLevel.LOW.value,
            source_text="",
            validation_errors=["No generic name found"]
        )
    
    @classmethod
    def _extract_strength(cls, text: str) -> ExtractedField:
        """Extract medication strength from text."""
        strength_patterns = [
            r'(\d+(?:\.\d+)?)\s*(mg|mcg|ml|units?|g|mcg/ml|mg/ml|units/ml)',
            r'strength\s*:\s*(\d+(?:\.\d+)?)\s*(mg|mcg|ml|units?|g)',
            r'(\d+(?:\.\d+)?)\s*(mg|mcg|ml|units?|g)\s*(tablets?|capsules?|drops?|units?)',
        ]
        
        for pattern in strength_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                strength = f"{match.group(1)}{match.group(2)}"
                return ExtractedField(
                    value=strength,
                    confidence=ConfidenceLevel.HIGH.value,
                    source_text=match.group(0)
                )
        
        return ExtractedField(
            value=None,
            confidence=ConfidenceLevel.VERY_LOW.value,
            source_text="",
            validation_errors=["No strength information found"]
        )
    
    @classmethod
    def _extract_quantity(cls, text: str) -> ExtractedField:
        """Extract quantity from text with validation."""
        for pattern in cls.QUANTITY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                quantity = int(match.group(1))
                
                # Validate quantity
                validation_errors = []
                if quantity <= 0:
                    validation_errors.append("Quantity must be positive")
                elif quantity > 1000:
                    validation_errors.append("Quantity seems unusually high")
                
                confidence = ConfidenceLevel.HIGH.value
                if validation_errors:
                    confidence = ConfidenceLevel.MEDIUM.value
                
                return ExtractedField(
                    value=quantity,
                    confidence=confidence,
                    source_text=match.group(0),
                    validation_errors=validation_errors
                )
        
        return ExtractedField(
            value=None,
            confidence=ConfidenceLevel.VERY_LOW.value,
            source_text="",
            validation_errors=["No quantity found"]
        )
    
    @classmethod
    def _extract_instructions(cls, text: str) -> ExtractedField:
        """Extract medication instructions from text."""
        # First try complex instruction patterns
        for pattern in cls.COMPLEX_INSTRUCTION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Clean up the instruction text
                instruction = match.group(0).strip()
                # Remove extra whitespace and newlines
                instruction = re.sub(r'\s+', ' ', instruction)
                return ExtractedField(
                    value=instruction,
                    confidence=ConfidenceLevel.HIGH.value,
                    source_text=match.group(0)
                )
        
        # Look for general instruction patterns
        instruction_patterns = [
            r'take\s+([^.\n]*(?:[^.\n]*\n[^.\n]*)*?)(?=\n|$)',
            r'use\s+([^.\n]*(?:[^.\n]*\n[^.\n]*)*?)(?=\n|$)',
            r'apply\s+([^.\n]*(?:[^.\n]*\n[^.\n]*)*?)(?=\n|$)',
            r'inject\s+([^.\n]*(?:[^.\n]*\n[^.\n]*)*?)(?=\n|$)',
            r'instructions?\s*:\s*([^.\n]*(?:[^.\n]*\n[^.\n]*)*?)(?=\n|$)',
        ]
        
        for pattern in instruction_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                instruction = match.group(1).strip()
                # Clean up the instruction text
                instruction = re.sub(r'\s+', ' ', instruction)
                # Remove quantity and repeat information from instructions
                instruction = re.sub(r'quantity:\s*x?\s*\d+', '', instruction, flags=re.IGNORECASE)
                instruction = re.sub(r'\+?\s*\d+\s*repeats?', '', instruction, flags=re.IGNORECASE)
                instruction = instruction.strip()
                
                if instruction:
                    return ExtractedField(
                        value=instruction,
                        confidence=ConfidenceLevel.MEDIUM.value,
                        source_text=match.group(0)
                    )
        
        return ExtractedField(
            value=None,
            confidence=ConfidenceLevel.VERY_LOW.value,
            source_text="",
            validation_errors=["No instructions found"]
        )
    
    @classmethod
    def _extract_medication_type(cls, text: str) -> ExtractedField:
        """Extract medication type from text."""
        text_lower = text.lower()
        
        for pattern, med_type in cls.MEDICATION_TYPE_PATTERNS:
            if re.search(pattern, text_lower):
                return ExtractedField(
                    value=med_type.value,
                    confidence=ConfidenceLevel.HIGH.value,
                    source_text=pattern
                )
        
        return ExtractedField(
            value=MedicationType.TABLET.value,  # Default to tablet
            confidence=ConfidenceLevel.LOW.value,
            source_text="",
            validation_errors=["No medication type found, defaulting to tablet"]
        )
    
    @classmethod
    def _extract_timing(cls, text: str) -> ExtractedField:
        """Extract timing information from text."""
        timing_info = []
        
        for pattern, timing_type in cls.TIMING_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if timing_type == 'custom_time':
                    # Extract the actual time
                    time_match = re.search(r'(\d{1,2})h(\d{2})?|(\d{1,2}):(\d{2})', match.group(0))
                    if time_match:
                        timing_info.append({
                            'type': timing_type,
                            'value': time_match.group(0),
                            'confidence': ConfidenceLevel.HIGH.value
                        })
                else:
                    timing_info.append({
                        'type': timing_type,
                        'value': match.group(0),
                        'confidence': ConfidenceLevel.HIGH.value
                    })
        
        if timing_info:
            return ExtractedField(
                value=timing_info,
                confidence=ConfidenceLevel.HIGH.value,
                source_text=text
            )
        
        return ExtractedField(
            value=[],
            confidence=ConfidenceLevel.LOW.value,
            source_text="",
            validation_errors=["No timing information found"]
        )
    
    @classmethod
    def _extract_repeats(cls, text: str) -> ExtractedField:
        """Extract repeat information from text."""
        for pattern in cls.REPEAT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                repeats = int(match.group(1))
                
                # Validate repeats
                validation_errors = []
                if repeats < 0:
                    validation_errors.append("Repeats cannot be negative")
                elif repeats > 12:
                    validation_errors.append("Repeats seem unusually high")
                
                confidence = ConfidenceLevel.HIGH.value
                if validation_errors:
                    confidence = ConfidenceLevel.MEDIUM.value
                
                return ExtractedField(
                    value=repeats,
                    confidence=confidence,
                    source_text=match.group(0),
                    validation_errors=validation_errors
                )
        
        return ExtractedField(
            value=0,
            confidence=ConfidenceLevel.LOW.value,
            source_text="",
            validation_errors=["No repeat information found"]
        )
    
    @classmethod
    def _extract_as_needed(cls, text: str) -> ExtractedField:
        """Extract 'as needed' information from text."""
        as_needed_patterns = [
            r'as\s+needed',
            r'as\s+required',
            r'prn',
            r'when\s+needed',
            r'when\s+required',
        ]
        
        for pattern in as_needed_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return ExtractedField(
                    value=True,
                    confidence=ConfidenceLevel.HIGH.value,
                    source_text=pattern
                )
        
        return ExtractedField(
            value=False,
            confidence=ConfidenceLevel.MEDIUM.value,
            source_text="",
            validation_errors=["No 'as needed' information found"]
        ) 
    
    @classmethod
    def _extract_icd10_codes(cls, text: str) -> List[ExtractedField]:
        """Extract ICD-10 codes from text."""
        icd10_pattern = r'[A-Z]\d{2}(?:\.\d{1,2})?'
        matches = re.finditer(icd10_pattern, text)
        
        icd10_codes = []
        for match in matches:
            code = match.group(0)
            description = cls.ICD10_MAPPINGS.get(code, "Unknown condition")
            
            icd10_codes.append(ExtractedField(
                value={
                    'code': code,
                    'description': description,
                    'category': cls._get_icd10_category(code)
                },
                confidence=ConfidenceLevel.HIGH.value,
                source_text=match.group(0)
            ))
        
        return icd10_codes
    
    @classmethod
    def _get_icd10_category(cls, code: str) -> str:
        """Get category for ICD-10 code."""
        if code.startswith('E'):
            return 'Endocrine, nutritional and metabolic diseases'
        elif code.startswith('F'):
            return 'Mental and behavioural disorders'
        elif code.startswith('I'):
            return 'Diseases of the circulatory system'
        elif code.startswith('J'):
            return 'Diseases of the respiratory system'
        elif code.startswith('M'):
            return 'Diseases of the musculoskeletal system and connective tissue'
        elif code.startswith('N'):
            return 'Diseases of the genitourinary system'
        elif code.startswith('A'):
            return 'Certain infectious and parasitic diseases'
        elif code.startswith('Z'):
            return 'Factors influencing health status and contact with health services'
        else:
            return 'Other conditions'
    
    @classmethod
    def _extract_prescription_metadata(cls, text: str) -> ExtractedField:
        """Extract prescription metadata (date, number, etc.)."""
        metadata = {}
        
        # Extract prescription date
        date_patterns = [
            r'date\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                metadata['prescription_date'] = match.group(1)
                break
        
        # Extract prescription number
        number_patterns = [
            r'rx\s*#?\s*:?\s*(\w+)',
            r'prescription\s*#?\s*:?\s*(\w+)',
            r'(\w{2,10}-\d{4}-\d{3,6})',  # Common prescription number format
        ]
        
        for pattern in number_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['prescription_number'] = match.group(1)
                break
        
        confidence = ConfidenceLevel.MEDIUM.value if metadata else ConfidenceLevel.VERY_LOW.value
        
        return ExtractedField(
            value=metadata,
            confidence=confidence,
            source_text=text[:200]  # First 200 chars as source
        )
    
    @classmethod
    def validate_parsed_data(cls, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parsed prescription data and add validation results.
        
        Args:
            parsed_data: Parsed prescription data
            
        Returns:
            Validated data with validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Validate doctor information
        if parsed_data.get('doctor_info'):
            doctor_info = parsed_data['doctor_info']
            if isinstance(doctor_info, ExtractedField) and doctor_info.confidence < ConfidenceLevel.MEDIUM.value:
                validation_results['warnings'].append("Doctor information confidence is low")
        
        # Validate patient information
        if parsed_data.get('patient_info'):
            patient_info = parsed_data['patient_info']
            if isinstance(patient_info, ExtractedField) and patient_info.confidence < ConfidenceLevel.MEDIUM.value:
                validation_results['warnings'].append("Patient information confidence is low")
        
        # Validate medications
        medications = parsed_data.get('medications', [])
        if not medications:
            validation_results['errors'].append("No medications found in prescription")
            validation_results['is_valid'] = False
        
        for i, medication in enumerate(medications):
            if isinstance(medication, ExtractedField) and medication.value:
                med_data = medication.value
                
                # Check for required fields
                if not med_data.get('name'):
                    validation_results['errors'].append(f"Medication {i+1}: Missing name")
                    validation_results['is_valid'] = False
                
                if not med_data.get('strength'):
                    validation_results['warnings'].append(f"Medication {i+1}: Missing strength")
                
                if not med_data.get('instructions'):
                    validation_results['warnings'].append(f"Medication {i+1}: Missing instructions")
                
                # Check confidence levels
                if medication.confidence < ConfidenceLevel.MEDIUM.value:
                    validation_results['warnings'].append(f"Medication {i+1}: Low confidence in parsing")
        
        # Validate ICD-10 codes
        icd10_codes = parsed_data.get('icd10_codes', [])
        if not icd10_codes:
            validation_results['warnings'].append("No ICD-10 codes found")
        
        # Add validation results to parsed data
        parsed_data['validation'] = validation_results
        
        return parsed_data
    
    @classmethod
    def format_parsed_data(cls, parsed_data: Dict[str, Any]) -> str:
        """
        Format parsed prescription data into a readable string.
        
        Args:
            parsed_data: Parsed prescription data
            
        Returns:
            Formatted string representation
        """
        output = []
        
        # Doctor information
        if parsed_data.get('doctor_info'):
            doctor_info = parsed_data['doctor_info']
            if isinstance(doctor_info, ExtractedField) and doctor_info.value:
                output.append(f"Doctor: {doctor_info.value}")
        
        # Patient information
        if parsed_data.get('patient_info'):
            patient_info = parsed_data['patient_info']
            if isinstance(patient_info, ExtractedField) and patient_info.value:
                if isinstance(patient_info.value, dict):
                    patient_str = []
                    if patient_info.value.get('name'):
                        patient_str.append(f"Name: {patient_info.value['name']}")
                    if patient_info.value.get('id'):
                        patient_str.append(f"ID: {patient_info.value['id']}")
                    if patient_info.value.get('date_of_birth'):
                        patient_str.append(f"DOB: {patient_info.value['date_of_birth']}")
                    output.append(f"Patient: {', '.join(patient_str)}")
                else:
                    output.append(f"Patient: {patient_info.value}")
        
        # Medications
        medications = parsed_data.get('medications', [])
        if medications:
            output.append("\nMedications:")
            for i, medication in enumerate(medications):
                if isinstance(medication, ExtractedField) and medication.value:
                    med_data = medication.value
                    output.append(f"  {i+1}. {cls._get_field_value(med_data.get('name'))}")
                    
                    generic_name = cls._get_field_value(med_data.get('generic_name'))
                    if generic_name:
                        output.append(f"     Generic: {generic_name}")
                    
                    strength = cls._get_field_value(med_data.get('strength'))
                    if strength:
                        output.append(f"     Strength: {strength}")
                    
                    quantity = cls._get_field_value(med_data.get('quantity'))
                    if quantity:
                        output.append(f"     Quantity: {quantity}")
                    
                    instructions = cls._get_field_value(med_data.get('instructions'))
                    if instructions:
                        output.append(f"     Instructions: {instructions}")
                    
                    timing = cls._get_field_value(med_data.get('timing'))
                    if timing and isinstance(timing, list) and timing:
                        timing_str = []
                        for t in timing:
                            if isinstance(t, dict):
                                timing_str.append(f"{t.get('type', '')}: {t.get('value', '')}")
                        if timing_str:
                            output.append(f"     Timing: {', '.join(timing_str)}")
                    
                    repeats = cls._get_field_value(med_data.get('repeats'))
                    if repeats and repeats > 0:
                        output.append(f"     Repeats: {repeats}")
                    
                    as_needed = cls._get_field_value(med_data.get('as_needed'))
                    if as_needed:
                        output.append(f"     As needed: Yes")
        
        # ICD-10 codes
        icd10_codes = parsed_data.get('icd10_codes', [])
        if icd10_codes:
            output.append("\nICD-10 Codes:")
            for code_data in icd10_codes:
                if isinstance(code_data, ExtractedField) and code_data.value:
                    code_info = code_data.value
                    output.append(f"  {code_info['code']}: {code_info['description']}")
        
        # Overall confidence
        confidence = parsed_data.get('overall_confidence', 0.0)
        output.append(f"\nOverall Confidence: {confidence:.1%}")
        
        # Validation results
        if parsed_data.get('validation'):
            validation = parsed_data['validation']
            if validation.get('errors'):
                output.append(f"\nErrors: {', '.join(validation['errors'])}")
            if validation.get('warnings'):
                output.append(f"\nWarnings: {', '.join(validation['warnings'])}")
        
        return '\n'.join(output)
    
    @classmethod
    def _get_field_value(cls, field):
        """Helper method to extract value from ExtractedField or return the value directly."""
        if isinstance(field, ExtractedField):
            return field.value
        return field


# Example usage and testing
if __name__ == "__main__":
    # Example prescription text
    sample_prescription = """
    Dr. John Smith
    
    Patient: Jane Doe
    ID: 12345
    Date: 15/12/2024
    RX#: RX-2024-001
    
    ICD-10: E11.9, I10, F32.9
    
    1. NOVORAPID FlexPen 100 units/ml
       Take 20 units before meals
       Quantity: x 3
       + 5 REPEATS
    
    2. LANTUS Solostar Pen 100 units/ml
       Inject 30 units once daily at bedtime
       Quantity: x 3
       + 5 REPEATS
    
    3. METFORMIN 500mg tablets
       Take three tablets three times a day with meals
       Quantity: x 270
       + 5 REPEATS
    
    4. ATORVASTATIN 20mg tablets
       Take one tablet daily at night
       Quantity: x 30
       + 5 REPEATS
    
    5. OMEPRAZOLE 20mg capsules
       Take one capsule daily in the morning
       Quantity: x 30
       + 5 REPEATS
    """
    
    # Parse the prescription
    parsed = PrescriptionParser.parse_prescription(sample_prescription)
    
    # Validate the parsed data
    validated = PrescriptionParser.validate_parsed_data(parsed)
    
    # Format and print results
    print("=== Parsed Prescription ===")
    print(PrescriptionParser.format_parsed_data(validated))
    
    print("\n=== Raw Parsed Data ===")
    import json
    print(json.dumps(validated, indent=2, default=str)) 