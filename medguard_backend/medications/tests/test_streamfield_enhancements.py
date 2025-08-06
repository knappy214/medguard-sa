"""
Tests for Wagtail 7.0.2 StreamField enhancements in medications models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from wagtail.blocks import StreamValue
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file

from medications.models import (
    Medication, MedicationIndexPage, MedicationDetailPage,
    MedicationContentStreamBlock, MedicationDosageBlock,
    MedicationSideEffectBlock, MedicationInteractionBlock
)

User = get_user_model()


class StreamFieldEnhancementsTestCase(TestCase):
    """Test case for StreamField enhancements."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test image
        self.test_image = Image.objects.create(
            title="Test Medication Image",
            file=get_test_image_file()
        )
    
    def test_medication_dosage_block_creation(self):
        """Test creating a medication dosage block."""
        dosage_data = {
            'amount': '500',
            'unit': 'mg',
            'frequency': 'once_daily',
            'instructions': 'Take with food'
        }
        
        dosage_block = MedicationDosageBlock()
        cleaned_value = dosage_block.clean(dosage_data)
        
        self.assertEqual(cleaned_value['amount'], 500.0)
        self.assertEqual(cleaned_value['unit'], 'mg')
        self.assertEqual(cleaned_value['frequency'], 'once_daily')
        self.assertEqual(cleaned_value['instructions'], 'Take with food')
    
    def test_medication_side_effect_block_creation(self):
        """Test creating a medication side effect block."""
        side_effect_data = {
            'effect_name': 'Stomach upset',
            'severity': 'mild',
            'frequency': 'common',
            'description': 'May cause mild stomach discomfort'
        }
        
        side_effect_block = MedicationSideEffectBlock()
        cleaned_value = side_effect_block.clean(side_effect_data)
        
        self.assertEqual(cleaned_value['effect_name'], 'Stomach upset')
        self.assertEqual(cleaned_value['severity'], 'mild')
        self.assertEqual(cleaned_value['frequency'], 'common')
        self.assertEqual(cleaned_value['description'], 'May cause mild stomach discomfort')
    
    def test_medication_interaction_block_creation(self):
        """Test creating a medication interaction block."""
        interaction_data = {
            'interacting_medication': 'Warfarin',
            'interaction_type': 'major',
            'description': 'Increased risk of bleeding',
            'recommendation': 'Avoid combination'
        }
        
        interaction_block = MedicationInteractionBlock()
        cleaned_value = interaction_block.clean(interaction_data)
        
        self.assertEqual(cleaned_value['interacting_medication'], 'Warfarin')
        self.assertEqual(cleaned_value['interaction_type'], 'major')
        self.assertEqual(cleaned_value['description'], 'Increased risk of bleeding')
        self.assertEqual(cleaned_value['recommendation'], 'Avoid combination')
    
    def test_medication_with_streamfield_content(self):
        """Test creating a medication with StreamField content."""
        # Create StreamField content
        stream_data = [
            ('dosage', {
                'amount': '500',
                'unit': 'mg',
                'frequency': 'once_daily',
                'instructions': 'Take with food'
            }),
            ('side_effects', [
                {
                    'effect_name': 'Stomach upset',
                    'severity': 'mild',
                    'frequency': 'common',
                    'description': 'May cause mild stomach discomfort'
                }
            ]),
            ('interactions', [
                {
                    'interacting_medication': 'Warfarin',
                    'interaction_type': 'major',
                    'description': 'Increased risk of bleeding',
                    'recommendation': 'Avoid combination'
                }
            ])
        ]
        
        content = StreamValue(MedicationContentStreamBlock(), stream_data)
        
        # Create medication with StreamField content
        medication = Medication.objects.create(
            name="Test Aspirin",
            strength="500mg",
            dosage_unit="mg",
            content=content
        )
        
        self.assertEqual(medication.name, "Test Aspirin")
        self.assertEqual(medication.strength, "500mg")
        
        # Test StreamField content
        self.assertIsNotNone(medication.content)
        self.assertEqual(len(medication.content), 3)
        
        # Test dosage block
        dosage_block = medication.content[0]
        self.assertEqual(dosage_block.block_type, 'dosage')
        self.assertEqual(dosage_block.value['amount'], 500.0)
        self.assertEqual(dosage_block.value['unit'], 'mg')
        
        # Test side effects block
        side_effects_block = medication.content[1]
        self.assertEqual(side_effects_block.block_type, 'side_effects')
        self.assertEqual(len(side_effects_block.value), 1)
        self.assertEqual(side_effects_block.value[0]['effect_name'], 'Stomach upset')
        
        # Test interactions block
        interactions_block = medication.content[2]
        self.assertEqual(interactions_block.block_type, 'interactions')
        self.assertEqual(len(interactions_block.value), 1)
        self.assertEqual(interactions_block.value[0]['interacting_medication'], 'Warfarin')
    
    def test_medication_index_page_with_streamfield(self):
        """Test creating a medication index page with StreamField content."""
        # Create StreamField content for index page
        stream_data = [
            ('description', 'Welcome to our medication database'),
            ('instructions', 'Use the search and filter options to find medications')
        ]
        
        content = StreamValue(MedicationContentStreamBlock(), stream_data)
        
        # Create index page
        index_page = MedicationIndexPage.objects.create(
            title="Medications Index",
            slug="medications",
            intro="Find your medications here",
            content=content
        )
        
        self.assertEqual(index_page.title, "Medications Index")
        self.assertEqual(index_page.intro, "Find your medications here")
        
        # Test StreamField content
        self.assertIsNotNone(index_page.content)
        self.assertEqual(len(index_page.content), 2)
        
        description_block = index_page.content[0]
        self.assertEqual(description_block.block_type, 'description')
        self.assertEqual(description_block.value, 'Welcome to our medication database')
        
        instructions_block = index_page.content[1]
        self.assertEqual(instructions_block.block_type, 'instructions')
        self.assertEqual(instructions_block.value, 'Use the search and filter options to find medications')
    
    def test_medication_detail_page_with_streamfield(self):
        """Test creating a medication detail page with StreamField content."""
        # Create medication first
        medication = Medication.objects.create(
            name="Test Medication",
            strength="100mg",
            dosage_unit="mg"
        )
        
        # Create StreamField content for detail page
        stream_data = [
            ('description', 'Detailed information about the medication'),
            ('warnings', 'Important safety warnings')
        ]
        
        content = StreamValue(MedicationContentStreamBlock(), stream_data)
        
        # Create detail page
        detail_page = MedicationDetailPage.objects.create(
            title="Test Medication Detail",
            slug="test-medication-detail",
            medication=medication,
            content=content,
            additional_info="Additional information here"
        )
        
        self.assertEqual(detail_page.title, "Test Medication Detail")
        self.assertEqual(detail_page.medication, medication)
        self.assertEqual(detail_page.additional_info, "Additional information here")
        
        # Test StreamField content
        self.assertIsNotNone(detail_page.content)
        self.assertEqual(len(detail_page.content), 2)
        
        description_block = detail_page.content[0]
        self.assertEqual(description_block.block_type, 'description')
        self.assertEqual(description_block.value, 'Detailed information about the medication')
        
        warnings_block = detail_page.content[1]
        self.assertEqual(warnings_block.block_type, 'warnings')
        self.assertEqual(warnings_block.value, 'Important safety warnings')
    
    def test_streamfield_validation(self):
        """Test StreamField validation."""
        # Test invalid dosage amount
        invalid_dosage_data = {
            'amount': '-100',  # Negative amount should fail
            'unit': 'mg',
            'frequency': 'once_daily'
        }
        
        dosage_block = MedicationDosageBlock()
        
        with self.assertRaises(Exception):
            dosage_block.clean(invalid_dosage_data)
        
        # Test valid dosage amount
        valid_dosage_data = {
            'amount': '100',
            'unit': 'mg',
            'frequency': 'once_daily'
        }
        
        cleaned_value = dosage_block.clean(valid_dosage_data)
        self.assertEqual(cleaned_value['amount'], 100.0)
    
    def test_streamfield_serialization(self):
        """Test StreamField serialization and deserialization."""
        # Create StreamField content
        stream_data = [
            ('dosage', {
                'amount': '250',
                'unit': 'mg',
                'frequency': 'twice_daily',
                'instructions': 'Take morning and evening'
            })
        ]
        
        content = StreamValue(MedicationContentStreamBlock(), stream_data)
        
        # Create medication
        medication = Medication.objects.create(
            name="Test Medication",
            strength="250mg",
            dosage_unit="mg",
            content=content
        )
        
        # Save and retrieve from database
        medication.save()
        retrieved_medication = Medication.objects.get(id=medication.id)
        
        # Test that StreamField content is preserved
        self.assertIsNotNone(retrieved_medication.content)
        self.assertEqual(len(retrieved_medication.content), 1)
        
        dosage_block = retrieved_medication.content[0]
        self.assertEqual(dosage_block.block_type, 'dosage')
        self.assertEqual(dosage_block.value['amount'], 250.0)
        self.assertEqual(dosage_block.value['unit'], 'mg')
        self.assertEqual(dosage_block.value['frequency'], 'twice_daily')
        self.assertEqual(dosage_block.value['instructions'], 'Take morning and evening') 