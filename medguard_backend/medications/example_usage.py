"""
Example usage of enhanced medication views functionality.

This script demonstrates how to use the new batch creation, prescription upload,
and stock management features.
"""

import json
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Medication, MedicationSchedule, StockTransaction, PrescriptionRenewal

User = get_user_model()


def example_bulk_create_from_prescription():
    """
    Example of bulk creating medications from prescription data.
    """
    print("=== Example: Bulk Create from Prescription ===")
    
    # Sample prescription data
    prescription_data = {
        "medications": [
            {
                "name": "Paracetamol",
                "generic_name": "Acetaminophen",
                "strength": "500mg",
                "medication_type": "tablet",
                "prescription_type": "prescription",
                "initial_stock": 30,
                "schedule_data": {
                    "timing": "morning",
                    "dosage_amount": 1,
                    "frequency": "daily",
                    "start_date": timezone.now().date(),
                    "instructions": "Take with food"
                }
            },
            {
                "name": "Ibuprofen",
                "generic_name": "Ibuprofen",
                "strength": "400mg",
                "medication_type": "tablet",
                "prescription_type": "prescription",
                "initial_stock": 20,
                "schedule_data": {
                    "timing": "noon",
                    "dosage_amount": 1,
                    "frequency": "twice_daily",
                    "start_date": timezone.now().date(),
                    "instructions": "Take as needed for pain"
                }
            }
        ],
        "patient_id": 1,  # Assuming patient with ID 1 exists
        "prescription_number": "RX123456",
        "prescribed_by": "Dr. Smith",
        "prescribed_date": "2024-01-01"
    }
    
    print("Prescription Data:")
    print(json.dumps(prescription_data, indent=2, default=str))
    
    # Expected API call:
    # POST /api/medications/bulk_create_from_prescription/
    # Headers: {"Authorization": "Bearer <token>", "Content-Type": "application/json"}
    # Body: prescription_data
    
    print("\nExpected Response:")
    expected_response = {
        "message": "Successfully created 2 medications",
        "created_medications": [
            {
                "id": 1,
                "name": "Paracetamol",
                "initial_stock": 30
            },
            {
                "id": 2,
                "name": "Ibuprofen",
                "initial_stock": 20
            }
        ],
        "created_schedules": 2,
        "created_transactions": 2,
        "prescription_number": "RX123456",
        "patient": {
            "id": 1,
            "name": "John Doe"
        }
    }
    print(json.dumps(expected_response, indent=2))


def example_prescription_upload():
    """
    Example of uploading OCR-processed prescription data.
    """
    print("\n=== Example: Prescription Upload (OCR) ===")
    
    # Sample OCR data
    ocr_data = {
        "ocr_data": {
            "medications": [
                {
                    "name": "Amoxicillin",
                    "strength": "500mg",
                    "instructions": "Take one capsule three times daily",
                    "quantity": 21
                },
                {
                    "name": "Omeprazole",
                    "strength": "20mg",
                    "instructions": "Take one tablet daily",
                    "quantity": 30
                }
            ],
            "prescription_info": {
                "prescription_number": "RX789012",
                "prescribed_by": "Dr. Johnson",
                "prescribed_date": "2024-01-15"
            }
        },
        "patient_id": 1,
        "confidence_score": 0.85
    }
    
    print("OCR Data:")
    print(json.dumps(ocr_data, indent=2, default=str))
    
    # Expected API call:
    # POST /api/medications/prescription_upload/
    # Headers: {"Authorization": "Bearer <token>", "Content-Type": "application/json"}
    # Body: ocr_data
    
    print("\nExpected Response:")
    expected_response = {
        "message": "Prescription processed successfully",
        "confidence_score": 0.85,
        "processed_medications": 2,
        "enrichment_results": [
            {
                "name": "Amoxicillin",
                "strength": "500mg",
                "medication_type": "capsule",
                "generic_name": "amoxicillin",
                "description": "Prescription medication: Amoxicillin 500mg",
                "active_ingredients": "",
                "manufacturer": "",
                "side_effects": "",
                "contraindications": "",
                "storage_instructions": "Store at room temperature. Keep out of reach of children."
            },
            {
                "name": "Omeprazole",
                "strength": "20mg",
                "medication_type": "tablet",
                "generic_name": "omeprazole",
                "description": "Prescription medication: Omeprazole 20mg",
                "active_ingredients": "",
                "manufacturer": "",
                "side_effects": "",
                "contraindications": "",
                "storage_instructions": "Store at room temperature. Keep out of reach of children."
            }
        ],
        "bulk_creation_result": {
            "created_medications": 2,
            "created_schedules": 2,
            "created_transactions": 2
        }
    }
    print(json.dumps(expected_response, indent=2))


def example_add_stock():
    """
    Example of adding stock to an existing medication.
    """
    print("\n=== Example: Add Stock ===")
    
    # Sample stock data
    stock_data = {
        "quantity": 30,
        "unit_price": 15.50,
        "batch_number": "BATCH123",
        "expiry_date": "2025-12-31",
        "notes": "Restocked from pharmacy"
    }
    
    print("Stock Data:")
    print(json.dumps(stock_data, indent=2))
    
    # Expected API call:
    # POST /api/medications/{medication_id}/add_stock/
    # Headers: {"Authorization": "Bearer <token>", "Content-Type": "application/json"}
    # Body: stock_data
    
    print("\nExpected Response:")
    expected_response = {
        "message": "Successfully added 30 units to Test Medication",
        "medication_id": 1,
        "medication_name": "Test Medication",
        "new_stock": 40,
        "transaction_id": 5,
        "batch_number": "BATCH123",
        "expiry_date": "2025-12-31"
    }
    print(json.dumps(expected_response, indent=2))


def example_audit_trail():
    """
    Example of retrieving audit trail for a medication.
    """
    print("\n=== Example: Audit Trail ===")
    
    # Expected API call:
    # GET /api/medications/{medication_id}/audit_trail/
    # Headers: {"Authorization": "Bearer <token>"}
    
    print("Expected Response:")
    expected_response = {
        "medication": {
            "id": 1,
            "name": "Test Medication",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z"
        },
        "transactions": [
            {
                "id": 1,
                "type": "purchase",
                "quantity": 30,
                "user": "Admin User",
                "timestamp": "2024-01-01T10:00:00Z",
                "notes": "Initial stock",
                "reference": "STOCK_20240101_100000"
            },
            {
                "id": 2,
                "type": "purchase",
                "quantity": 20,
                "user": "Admin User",
                "timestamp": "2024-01-02T14:30:00Z",
                "notes": "Additional stock",
                "reference": "STOCK_20240102_143000"
            }
        ],
        "logs": [
            {
                "id": 1,
                "status": "taken",
                "patient": "John Doe",
                "scheduled_time": "2024-01-01T08:00:00Z",
                "actual_time": "2024-01-01T08:15:00Z",
                "dosage_taken": 1,
                "notes": ""
            }
        ],
        "alerts": [
            {
                "id": 1,
                "type": "low_stock",
                "priority": "medium",
                "status": "active",
                "created_by": "Admin User",
                "created_at": "2024-01-01T10:00:00Z",
                "title": "Low Stock Alert",
                "message": "Medication running low"
            }
        ]
    }
    print(json.dumps(expected_response, indent=2))


def example_complete_workflow():
    """
    Example of a complete prescription workflow.
    """
    print("\n=== Example: Complete Prescription Workflow ===")
    
    workflow_steps = [
        {
            "step": 1,
            "action": "Upload prescription via OCR",
            "endpoint": "POST /api/medications/prescription_upload/",
            "description": "Process prescription image and extract medication data"
        },
        {
            "step": 2,
            "action": "Verify created medications",
            "endpoint": "GET /api/medications/",
            "description": "Check that medications were created with correct data"
        },
        {
            "step": 3,
            "action": "Add additional stock",
            "endpoint": "POST /api/medications/{id}/add_stock/",
            "description": "Add more stock if needed"
        },
        {
            "step": 4,
            "action": "Check audit trail",
            "endpoint": "GET /api/medications/{id}/audit_trail/",
            "description": "Review all activities for the medication"
        },
        {
            "step": 5,
            "action": "Monitor stock levels",
            "endpoint": "GET /api/medications/{id}/analytics/",
            "description": "Track stock analytics and predictions"
        }
    ]
    
    print("Workflow Steps:")
    for step in workflow_steps:
        print(f"\n{step['step']}. {step['action']}")
        print(f"   Endpoint: {step['endpoint']}")
        print(f"   Description: {step['description']}")


def example_error_handling():
    """
    Example of error handling scenarios.
    """
    print("\n=== Example: Error Handling ===")
    
    error_scenarios = [
        {
            "scenario": "Invalid medication data",
            "error": "ValidationError",
            "cause": "Empty medication name",
            "response": {
                "error": "Failed to create medication at index 0: This field cannot be blank."
            }
        },
        {
            "scenario": "Patient not found",
            "error": "404 Not Found",
            "cause": "Non-existent patient ID",
            "response": {
                "error": "Patient not found"
            }
        },
        {
            "scenario": "Invalid stock quantity",
            "error": "400 Bad Request",
            "cause": "Negative quantity",
            "response": {
                "error": "Quantity must be greater than 0"
            }
        },
        {
            "scenario": "Invalid expiry date format",
            "error": "400 Bad Request",
            "cause": "Wrong date format",
            "response": {
                "error": "Invalid expiry date format. Use YYYY-MM-DD"
            }
        }
    ]
    
    print("Error Scenarios:")
    for scenario in error_scenarios:
        print(f"\n{scenario['scenario']}:")
        print(f"  Error: {scenario['error']}")
        print(f"  Cause: {scenario['cause']}")
        print(f"  Response: {json.dumps(scenario['response'], indent=4)}")


def main():
    """
    Run all examples.
    """
    print("Enhanced Medication Views - Usage Examples")
    print("=" * 50)
    
    example_bulk_create_from_prescription()
    example_prescription_upload()
    example_add_stock()
    example_audit_trail()
    example_complete_workflow()
    example_error_handling()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nTo use these endpoints:")
    print("1. Ensure you have proper authentication")
    print("2. Use the correct HTTP methods and endpoints")
    print("3. Include proper headers (Content-Type: application/json)")
    print("4. Handle responses and errors appropriately")
    print("5. Test thoroughly before production use")


if __name__ == "__main__":
    main() 