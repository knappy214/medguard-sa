"""
Comprehensive test suite for Wagtail 7.0.2 StreamField blocks in MedGuard SA.

This module tests all StreamField block functionality including:
- MedicationValidationMixin behavior
- Individual StructBlock validation and rendering
- StreamBlock composition and validation
- Block admin interface functionality
- Block content rendering and display
- Custom validation rules and error handling
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import datetime, time, date
from unittest.mock import Mock, patch

from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.blocks.list_block import ListBlockValidationError
from wagtail.rich_text import RichText
from wagtail.images.tests.utils import Image, get_test_image_file

# Import blocks to test
from medications.blocks import (
    MedicationValidationMixin,
    MedicationInfoStructBlock,
    PrescriptionUploadBlock,
    InteractionWarningBlock,
    StockLevelBlock,
    MedicationSearchFilterBlock,
    PrescriptionTimelineBlock,
    MedicationComparisonTableBlock,
    PharmacyContactBlock,
    MedicationContentStreamBlock
)
from medications.models import (
    MedicationDosageBlock,
    MedicationSideEffectBlock,
    MedicationInteractionBlock,
    MedicationStorageBlock,
    MedicationImageBlock,
    MedicationScheduleBlock,
    MedicationComparisonTableBlock as ModelComparisonTableBlock,
    MedicationContentStreamBlock as ModelContentStreamBlock
)
from medications.page_models import (
    MedicationComparisonBlock,
    PharmacyLocationBlock,
    MedicationGuideBlock,
    PrescriptionHistoryBlock,
    PrescriptionFormStreamBlock,
    MedicationComparisonStreamBlock,
    PharmacyLocatorStreamBlock,
    MedicationGuideStreamBlock,
    PrescriptionHistoryStreamBlock
)


class MedicationValidationMixinTestCase(TestCase):
    """Test cases for MedicationValidationMixin."""
    
    def setUp(self):
        """Set up test data."""
        # Create a test block that uses the mixin
        class TestBlock(MedicationValidationMixin, MedicationInfoStructBlock):
            pass
        
        self.test_block = TestBlock()
        
    def test_valid_medication_name_validation(self):
        """Test validation passes for valid medication names."""
        valid_names = [
            'Aspirin',
            'Acetaminophen 500mg',
            'Co-Trimoxazole (Bactrim)',
            'Multi-Vitamin Complex',
            'Vitamin D3 1000IU'
        ]
        
        for name in valid_names:
            test_data = {
                'name': name,
                'strength': '500mg',
                'form': 'tablet'
            }
            
            # Should not raise validation error
            try:
                cleaned_data = self.test_block.clean(test_data)
                self.assertEqual(cleaned_data['name'], name)
            except StructBlockValidationError:
                self.fail(f"Validation failed for valid medication name: {name}")
                
    def test_invalid_medication_name_validation(self):
        """Test validation fails for invalid medication names."""
        invalid_names = [
            'Aspirin@#$',
            'Medicine with émojis 💊',
            'Name with < HTML',
            'Script<script>alert("xss")</script>',
            'Med|cine'
        ]
        
        for name in invalid_names:
            test_data = {
                'name': name,
                'strength': '500mg',
                'form': 'tablet'
            }
            
            with self.assertRaises(StructBlockValidationError) as context:
                self.test_block.clean(test_data)
            
            self.assertIn('invalid characters', str(context.exception))
            
    def test_dosage_amount_validation(self):
        """Test dosage amount validation rules."""
        # Test valid amounts
        valid_amounts = [0.1, 1.0, 100.5, 999999.99]
        
        for amount in valid_amounts:
            test_data = {
                'name': 'Test Medicine',
                'amount': amount,
                'strength': '500mg'
            }
            
            try:
                cleaned_data = self.test_block.clean(test_data)
                self.assertEqual(cleaned_data['amount'], amount)
            except StructBlockValidationError:
                self.fail(f"Validation failed for valid amount: {amount}")
        
        # Test invalid amounts
        invalid_amounts = [0, -1, 1000000.0]
        
        for amount in invalid_amounts:
            test_data = {
                'name': 'Test Medicine',
                'amount': amount,
                'strength': '500mg'
            }
            
            with self.assertRaises(StructBlockValidationError):
                self.test_block.clean(test_data)
                
    def test_frequency_timing_consistency_validation(self):
        """Test frequency and timing consistency validation."""
        # Valid combination
        valid_data = {
            'name': 'Test Medicine',
            'frequency': 'as_needed',
            'timing': 'custom'
        }
        
        try:
            cleaned_data = self.test_block.clean(valid_data)
            self.assertEqual(cleaned_data['frequency'], 'as_needed')
        except StructBlockValidationError:
            self.fail("Validation failed for valid frequency-timing combination")
        
        # Invalid combination
        invalid_data = {
            'name': 'Test Medicine',
            'frequency': 'as_needed',
            'timing': 'morning'
        }
        
        with self.assertRaises(StructBlockValidationError) as context:
            self.test_block.clean(invalid_data)
        
        self.assertIn('Custom timing is required', str(context.exception))


class MedicationInfoStructBlockTestCase(TestCase):
    """Test cases for MedicationInfoStructBlock."""
    
    def setUp(self):
        """Set up test data."""
        self.block = MedicationInfoStructBlock()
        
    def test_block_structure(self):
        """Test block has required fields."""
        child_blocks = self.block.child_blocks
        
        required_fields = [
            'name', 'generic_name', 'brand_name', 'strength', 
            'form', 'manufacturer', 'ndc_number', 'description'
        ]
        
        for field in required_fields:
            self.assertIn(field, child_blocks)
            
    def test_valid_medication_info_creation(self):
        """Test creating valid medication info block."""
        valid_data = {
            'name': 'Aspirin',
            'generic_name': 'Acetylsalicylic acid',
            'brand_name': 'Bayer Aspirin',
            'strength': '325mg',
            'form': 'tablet',
            'manufacturer': 'Bayer',
            'ndc_number': '12345-678-90',
            'description': 'Pain reliever and fever reducer'
        }
        
        # Should create without errors
        try:
            cleaned_data = self.block.clean(valid_data)
            self.assertEqual(cleaned_data['name'], 'Aspirin')
            self.assertEqual(cleaned_data['strength'], '325mg')
        except Exception as e:
            self.fail(f"Failed to create valid medication info: {e}")
            
    def test_block_rendering(self):
        """Test block renders correctly."""
        test_data = {
            'name': 'Test Medicine',
            'strength': '500mg',
            'form': 'tablet'
        }
        
        # Test rendering doesn't raise errors
        try:
            rendered = self.block.render(test_data)
            self.assertIsInstance(rendered, str)
            self.assertIn('Test Medicine', rendered)
        except Exception as e:
            self.fail(f"Block rendering failed: {e}")


class PrescriptionUploadBlockTestCase(TestCase):
    """Test cases for PrescriptionUploadBlock."""
    
    def setUp(self):
        """Set up test data."""
        self.block = PrescriptionUploadBlock()
        
    def test_prescription_upload_structure(self):
        """Test prescription upload block structure."""
        child_blocks = self.block.child_blocks
        
        expected_fields = [
            'prescription_image', 'patient_name', 'doctor_name',
            'prescription_date', 'notes', 'requires_verification'
        ]
        
        for field in expected_fields:
            self.assertIn(field, child_blocks)
            
    def test_prescription_date_validation(self):
        """Test prescription date validation."""
        # Test with future date (should be invalid)
        future_date = date(2030, 1, 1)
        test_data = {
            'patient_name': 'John Doe',
            'doctor_name': 'Dr. Smith',
            'prescription_date': future_date,
            'requires_verification': True
        }
        
        with self.assertRaises(StructBlockValidationError):
            self.block.clean(test_data)
            
    def test_valid_prescription_upload(self):
        """Test valid prescription upload data."""
        valid_data = {
            'patient_name': 'John Doe',
            'doctor_name': 'Dr. Jane Smith',
            'prescription_date': date(2024, 1, 15),
            'notes': 'Take with food',
            'requires_verification': True
        }
        
        try:
            cleaned_data = self.block.clean(valid_data)
            self.assertEqual(cleaned_data['patient_name'], 'John Doe')
        except Exception as e:
            self.fail(f"Valid prescription upload failed: {e}")


class InteractionWarningBlockTestCase(TestCase):
    """Test cases for InteractionWarningBlock."""
    
    def setUp(self):
        """Set up test data."""
        self.block = InteractionWarningBlock()
        
    def test_interaction_warning_structure(self):
        """Test interaction warning block structure."""
        child_blocks = self.block.child_blocks
        
        expected_fields = [
            'medication_a', 'medication_b', 'interaction_type',
            'severity_level', 'warning_message', 'recommendations'
        ]
        
        for field in expected_fields:
            self.assertIn(field, child_blocks)
            
    def test_severity_level_choices(self):
        """Test severity level has correct choices."""
        severity_field = self.block.child_blocks['severity_level']
        choices = [choice[0] for choice in severity_field.choices]
        
        expected_choices = ['minor', 'moderate', 'major', 'severe']
        for choice in expected_choices:
            self.assertIn(choice, choices)
            
    def test_interaction_validation(self):
        """Test interaction warning validation."""
        valid_data = {
            'medication_a': 'Warfarin',
            'medication_b': 'Aspirin',
            'interaction_type': 'drug_drug',
            'severity_level': 'major',
            'warning_message': 'Increased bleeding risk',
            'recommendations': 'Monitor INR levels closely'
        }
        
        try:
            cleaned_data = self.block.clean(valid_data)
            self.assertEqual(cleaned_data['severity_level'], 'major')
        except Exception as e:
            self.fail(f"Valid interaction warning failed: {e}")


class StockLevelBlockTestCase(TestCase):
    """Test cases for StockLevelBlock."""
    
    def setUp(self):
        """Set up test data."""
        self.block = StockLevelBlock()
        
    def test_stock_level_structure(self):
        """Test stock level block structure."""
        child_blocks = self.block.child_blocks
        
        expected_fields = [
            'medication_name', 'current_stock', 'minimum_stock',
            'maximum_stock', 'reorder_point', 'supplier_info'
        ]
        
        for field in expected_fields:
            self.assertIn(field, child_blocks)
            
    def test_stock_level_validation(self):
        """Test stock level validation rules."""
        # Test invalid stock levels (negative values)
        invalid_data = {
            'medication_name': 'Test Medicine',
            'current_stock': -5,
            'minimum_stock': 10,
            'maximum_stock': 100
        }
        
        with self.assertRaises(StructBlockValidationError):
            self.block.clean(invalid_data)
            
        # Test valid stock levels
        valid_data = {
            'medication_name': 'Test Medicine',
            'current_stock': 50,
            'minimum_stock': 10,
            'maximum_stock': 100,
            'reorder_point': 25
        }
        
        try:
            cleaned_data = self.block.clean(valid_data)
            self.assertEqual(cleaned_data['current_stock'], 50)
        except Exception as e:
            self.fail(f"Valid stock level failed: {e}")
            
    def test_stock_level_logic_validation(self):
        """Test stock level logical consistency."""
        # Test minimum > maximum (should be invalid)
        invalid_data = {
            'medication_name': 'Test Medicine',
            'current_stock': 50,
            'minimum_stock': 100,
            'maximum_stock': 50
        }
        
        with self.assertRaises(StructBlockValidationError):
            self.block.clean(invalid_data)


class MedicationDosageBlockTestCase(TestCase):
    """Test cases for MedicationDosageBlock."""
    
    def setUp(self):
        """Set up test data."""
        self.block = MedicationDosageBlock()
        
    def test_dosage_block_structure(self):
        """Test dosage block has required fields."""
        child_blocks = self.block.child_blocks
        
        expected_fields = [
            'amount', 'unit', 'frequency', 'timing',
            'duration', 'instructions', 'route'
        ]
        
        for field in expected_fields:
            self.assertIn(field, child_blocks)
            
    def test_dosage_amount_validation(self):
        """Test dosage amount validation."""
        # Test zero dosage (should be invalid)
        invalid_data = {
            'amount': 0,
            'unit': 'mg',
            'frequency': 'twice_daily',
            'route': 'oral'
        }
        
        with self.assertRaises(StructBlockValidationError):
            self.block.clean(invalid_data)
            
        # Test valid dosage
        valid_data = {
            'amount': Decimal('500.0'),
            'unit': 'mg',
            'frequency': 'twice_daily',
            'timing': 'with_meals',
            'route': 'oral',
            'instructions': 'Take with food'
        }
        
        try:
            cleaned_data = self.block.clean(valid_data)
            self.assertEqual(cleaned_data['amount'], Decimal('500.0'))
        except Exception as e:
            self.fail(f"Valid dosage failed: {e}")


class MedicationScheduleBlockTestCase(TestCase):
    """Test cases for MedicationScheduleBlock."""
    
    def setUp(self):
        """Set up test data."""
        self.block = MedicationScheduleBlock()
        
    def test_schedule_block_structure(self):
        """Test schedule block structure."""
        child_blocks = self.block.child_blocks
        
        expected_fields = [
            'start_date', 'end_date', 'times_per_day',
            'schedule_times', 'skip_weekends', 'special_instructions'
        ]
        
        for field in expected_fields:
            self.assertIn(field, child_blocks)
            
    def test_schedule_date_validation(self):
        """Test schedule date validation."""
        # Test end date before start date
        invalid_data = {
            'start_date': date(2024, 2, 1),
            'end_date': date(2024, 1, 1),
            'times_per_day': 2
        }
        
        with self.assertRaises(StructBlockValidationError):
            self.block.clean(invalid_data)
            
        # Test valid date range
        valid_data = {
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 2, 1),
            'times_per_day': 2,
            'schedule_times': ['08:00', '20:00']
        }
        
        try:
            cleaned_data = self.block.clean(valid_data)
            self.assertEqual(cleaned_data['times_per_day'], 2)
        except Exception as e:
            self.fail(f"Valid schedule failed: {e}")


class MedicationContentStreamBlockTestCase(TestCase):
    """Test cases for MedicationContentStreamBlock."""
    
    def setUp(self):
        """Set up test data."""
        self.stream_block = MedicationContentStreamBlock()
        
    def test_stream_block_child_blocks(self):
        """Test stream block contains expected child blocks."""
        child_blocks = self.stream_block.child_blocks
        
        expected_blocks = [
            'medication_info', 'dosage_info', 'side_effects',
            'interactions', 'storage_info', 'schedule'
        ]
        
        for block_name in expected_blocks:
            self.assertIn(block_name, child_blocks)
            
    def test_stream_block_validation(self):
        """Test stream block validation."""
        # Test valid stream data
        valid_stream_data = [
            {
                'type': 'medication_info',
                'value': {
                    'name': 'Aspirin',
                    'strength': '325mg',
                    'form': 'tablet'
                }
            },
            {
                'type': 'dosage_info',
                'value': {
                    'amount': Decimal('325.0'),
                    'unit': 'mg',
                    'frequency': 'once_daily',
                    'route': 'oral'
                }
            }
        ]
        
        try:
            cleaned_data = self.stream_block.clean(valid_stream_data)
            self.assertEqual(len(cleaned_data), 2)
        except Exception as e:
            self.fail(f"Valid stream block failed: {e}")
            
    def test_stream_block_rendering(self):
        """Test stream block rendering."""
        stream_data = [
            {
                'type': 'medication_info',
                'value': {
                    'name': 'Test Medicine',
                    'strength': '500mg'
                }
            }
        ]
        
        try:
            rendered = self.stream_block.render(stream_data)
            self.assertIsInstance(rendered, str)
            self.assertIn('Test Medicine', rendered)
        except Exception as e:
            self.fail(f"Stream block rendering failed: {e}")


class PharmacyLocationBlockTestCase(TestCase):
    """Test cases for PharmacyLocationBlock."""
    
    def setUp(self):
        """Set up test data."""
        self.block = PharmacyLocationBlock()
        
    def test_pharmacy_location_structure(self):
        """Test pharmacy location block structure."""
        child_blocks = self.block.child_blocks
        
        expected_fields = [
            'name', 'address', 'phone', 'email',
            'operating_hours', 'services_offered', 'coordinates'
        ]
        
        for field in expected_fields:
            self.assertIn(field, child_blocks)
            
    def test_pharmacy_contact_validation(self):
        """Test pharmacy contact information validation."""
        valid_data = {
            'name': 'MedGuard Pharmacy',
            'address': '123 Health Street, Cape Town, 8001',
            'phone': '+27-21-123-4567',
            'email': 'info@medguardpharmacy.co.za',
            'operating_hours': 'Mon-Fri: 8AM-6PM, Sat: 9AM-2PM'
        }
        
        try:
            cleaned_data = self.block.clean(valid_data)
            self.assertEqual(cleaned_data['name'], 'MedGuard Pharmacy')
        except Exception as e:
            self.fail(f"Valid pharmacy location failed: {e}")


class BlockAdminInterfaceTestCase(TestCase):
    """Test cases for block admin interface functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.medication_block = MedicationInfoStructBlock()
        self.stream_block = MedicationContentStreamBlock()
        
    def test_block_admin_form_rendering(self):
        """Test block renders properly in admin forms."""
        # Test with empty data
        try:
            form_html = self.medication_block.render_form(
                value=None,
                prefix='test',
                errors=None
            )
            self.assertIsInstance(form_html, str)
            self.assertIn('name', form_html)
        except Exception as e:
            self.fail(f"Admin form rendering failed: {e}")
            
    def test_block_admin_validation_errors(self):
        """Test block validation errors display in admin."""
        invalid_data = {
            'name': 'Invalid@Name',
            'amount': -1
        }
        
        try:
            self.medication_block.clean(invalid_data)
        except StructBlockValidationError as e:
            # Should contain specific error messages
            self.assertIn('invalid characters', str(e))
            
    def test_stream_block_admin_interface(self):
        """Test stream block admin interface."""
        try:
            form_html = self.stream_block.render_form(
                value=[],
                prefix='stream',
                errors=None
            )
            self.assertIsInstance(form_html, str)
        except Exception as e:
            self.fail(f"Stream block admin interface failed: {e}")


class BlockPerformanceTestCase(TestCase):
    """Test cases for block performance and optimization."""
    
    def setUp(self):
        """Set up test data."""
        self.stream_block = MedicationContentStreamBlock()
        
    def test_large_stream_block_performance(self):
        """Test performance with large stream blocks."""
        # Create large stream data
        large_stream_data = []
        for i in range(100):
            large_stream_data.append({
                'type': 'medication_info',
                'value': {
                    'name': f'Medicine {i}',
                    'strength': '500mg',
                    'form': 'tablet'
                }
            })
        
        # Test validation performance
        import time
        start_time = time.time()
        
        try:
            cleaned_data = self.stream_block.clean(large_stream_data)
            validation_time = time.time() - start_time
            
            # Should complete within reasonable time (< 1 second)
            self.assertLess(validation_time, 1.0)
            self.assertEqual(len(cleaned_data), 100)
        except Exception as e:
            self.fail(f"Large stream block validation failed: {e}")
            
    def test_block_caching_behavior(self):
        """Test block caching and optimization."""
        # Test repeated validation of same data
        test_data = {
            'name': 'Test Medicine',
            'strength': '500mg',
            'form': 'tablet'
        }
        
        medication_block = MedicationInfoStructBlock()
        
        # Multiple validations should be consistent
        for _ in range(10):
            try:
                cleaned_data = medication_block.clean(test_data)
                self.assertEqual(cleaned_data['name'], 'Test Medicine')
            except Exception as e:
                self.fail(f"Repeated block validation failed: {e}")


class BlockIntegrationTestCase(TestCase):
    """Integration tests for blocks with other system components."""
    
    def setUp(self):
        """Set up integration test data."""
        self.stream_block = MedicationContentStreamBlock()
        
    @patch('medications.blocks.Image')
    def test_block_with_image_integration(self, mock_image):
        """Test block integration with Wagtail images."""
        # Mock image instance
        mock_image_instance = Mock()
        mock_image_instance.id = 1
        mock_image_instance.title = 'Test Image'
        mock_image.objects.get.return_value = mock_image_instance
        
        # Test image block with mocked image
        image_block = MedicationImageBlock()
        test_data = {
            'image': 1,
            'caption': 'Test medication image',
            'alt_text': 'Alternative text for accessibility'
        }
        
        try:
            cleaned_data = image_block.clean(test_data)
            self.assertEqual(cleaned_data['caption'], 'Test medication image')
        except Exception as e:
            self.fail(f"Image block integration failed: {e}")
            
    def test_block_with_page_chooser_integration(self):
        """Test block integration with page choosers."""
        # This would test blocks that reference other pages
        # Implementation depends on specific page chooser blocks
        pass
        
    def test_block_search_integration(self):
        """Test block content is properly indexed for search."""
        # Test that block content can be searched
        test_data = [
            {
                'type': 'medication_info',
                'value': {
                    'name': 'Searchable Medicine',
                    'description': 'This medicine should be searchable'
                }
            }
        ]
        
        try:
            # Test block content extraction for search
            rendered = self.stream_block.render(test_data)
            self.assertIn('Searchable Medicine', rendered)
            self.assertIn('searchable', rendered.lower())
        except Exception as e:
            self.fail(f"Block search integration failed: {e}")


@pytest.mark.django_db
class BlockDatabaseIntegrationTestCase(TestCase):
    """Database integration tests for blocks."""
    
    def test_block_data_persistence(self):
        """Test block data persists correctly in database."""
        # This would test saving and retrieving block data
        # through actual page models that use the blocks
        pass
        
    def test_block_migration_compatibility(self):
        """Test block structure changes don't break existing data."""
        # This would test backward compatibility
        # when block structures change
        pass
