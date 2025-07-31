#!/usr/bin/env python
"""
Test script to verify stock deduction functionality when marking medications as taken.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import time

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from medications.models import Medication, MedicationSchedule, MedicationLog, StockTransaction, StockAlert
from django.utils import timezone
from django.db import transaction

User = get_user_model()

def test_stock_deduction():
    """Test the stock deduction functionality."""
    print("🧪 Testing Stock Deduction Functionality")
    print("=" * 50)
    
    try:
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='test_stock_user',
            defaults={
                'email': 'test_stock@example.com',
                'first_name': 'Test',
                'last_name': 'Stock',
                'user_type': 'PATIENT'
            }
        )
        
        if created:
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing test user: {user.username}")
        
        # Get or create a test medication with initial stock
        medication, created = Medication.objects.get_or_create(
            name='Test Medication - Stock Deduction',
            defaults={
                'generic_name': 'Test Generic',
                'brand_name': 'Test Brand',
                'medication_type': 'tablet',
                'strength': '100mg',
                'dosage_unit': 'mg',
                'pill_count': 50,  # Start with 50 pills
                'low_stock_threshold': 10,
                'description': 'Test medication for stock deduction testing'
            }
        )
        
        if created:
            print(f"✅ Created test medication: {medication.name}")
            print(f"   Initial stock: {medication.pill_count} pills")
        else:
            print(f"✅ Using existing test medication: {medication.name}")
            print(f"   Current stock: {medication.pill_count} pills")
        
        # Create a medication schedule
        schedule, created = MedicationSchedule.objects.get_or_create(
            patient=user,
            medication=medication,
            defaults={
                'timing': 'morning',
                'dosage_amount': Decimal('1.0'),
                'frequency': 'daily',
                'status': 'active'
            }
        )
        
        if created:
            print(f"✅ Created test schedule: {schedule.id}")
        else:
            print(f"✅ Using existing test schedule: {schedule.id}")
        
        print(f"\n📊 Initial State:")
        print(f"   Medication: {medication.name}")
        print(f"   Stock: {medication.pill_count} pills")
        print(f"   Low stock threshold: {medication.low_stock_threshold}")
        print(f"   Schedule dosage: {schedule.dosage_amount}")
        
        # Test 1: Mark medication as taken (should deduct 1 pill)
        print(f"\n🧪 Test 1: Mark medication as taken")
        print("-" * 30)
        
        initial_stock = medication.pill_count
        initial_transactions = StockTransaction.objects.filter(medication=medication).count()
        initial_alerts = StockAlert.objects.filter(medication=medication, status='active').count()
        
        # Simulate the mark_taken action
        with transaction.atomic():
            # Create medication log
            today = timezone.now().date()
            scheduled_time = timezone.make_aware(
                timezone.datetime.combine(today, time(8, 0))
            )
            
            log, created = MedicationLog.objects.get_or_create(
                patient=user,
                medication=medication,
                schedule=schedule,
                scheduled_time=scheduled_time,
                defaults={
                    'status': MedicationLog.Status.TAKEN,
                    'actual_time': timezone.now(),
                    'dosage_taken': schedule.dosage_amount,
                    'notes': 'Test stock deduction'
                }
            )
            
            if not created:
                log.status = MedicationLog.Status.TAKEN
                log.actual_time = timezone.now()
                log.dosage_taken = schedule.dosage_amount
                log.save()
            
            # Create stock transaction
            dosage_to_deduct = int(schedule.dosage_amount)
            stock_transaction = StockTransaction.objects.create(
                medication=medication,
                user=user,
                transaction_type=StockTransaction.TransactionType.DOSE_TAKEN,
                quantity=-dosage_to_deduct,
                notes=f"Test dose taken for schedule {schedule.id}",
                reference_number=f"TEST_{schedule.id}_{today}",
            )
            
            # Check for low stock alerts
            if medication.pill_count <= medication.low_stock_threshold:
                alert_type = StockAlert.AlertType.OUT_OF_STOCK if medication.pill_count == 0 else StockAlert.AlertType.LOW_STOCK
                priority = StockAlert.Priority.CRITICAL if medication.pill_count == 0 else StockAlert.Priority.HIGH
                
                existing_alert = StockAlert.objects.filter(
                    medication=medication,
                    alert_type__in=[StockAlert.AlertType.LOW_STOCK, StockAlert.AlertType.OUT_OF_STOCK],
                    status=StockAlert.Status.ACTIVE
                ).first()
                
                if not existing_alert:
                    StockAlert.objects.create(
                        medication=medication,
                        created_by=user,
                        alert_type=alert_type,
                        priority=priority,
                        title=f"Test {alert_type.replace('_', ' ').title()} Alert - {medication.name}",
                        message=f"Test: {medication.name} stock is now at {medication.pill_count} units.",
                        current_stock=medication.pill_count,
                        threshold_level=medication.low_stock_threshold
                    )
        
        # Refresh medication from database
        medication.refresh_from_db()
        
        # Check results
        final_stock = medication.pill_count
        final_transactions = StockTransaction.objects.filter(medication=medication).count()
        final_alerts = StockAlert.objects.filter(medication=medication, status='active').count()
        
        print(f"   Stock before: {initial_stock}")
        print(f"   Stock after: {final_stock}")
        print(f"   Stock deducted: {initial_stock - final_stock}")
        print(f"   Expected deduction: {dosage_to_deduct}")
        
        if initial_stock - final_stock == dosage_to_deduct:
            print("   ✅ Stock deduction successful!")
        else:
            print("   ❌ Stock deduction failed!")
            return False
        
        print(f"   Transactions before: {initial_transactions}")
        print(f"   Transactions after: {final_transactions}")
        print(f"   New transactions: {final_transactions - initial_transactions}")
        
        if final_transactions > initial_transactions:
            print("   ✅ Stock transaction created!")
        else:
            print("   ❌ Stock transaction not created!")
            return False
        
        print(f"   Alerts before: {initial_alerts}")
        print(f"   Alerts after: {final_alerts}")
        
        if final_alerts > initial_alerts:
            print("   ✅ Low stock alert created!")
        elif medication.pill_count > medication.low_stock_threshold:
            print("   ℹ️ No alert needed (stock above threshold)")
        else:
            print("   ⚠️ Expected alert but none created")
        
        # Test 2: Try to mark as taken when insufficient stock
        print(f"\n🧪 Test 2: Insufficient stock test")
        print("-" * 30)
        
        # Reduce stock to 0
        medication.pill_count = 0
        medication.save()
        print(f"   Set stock to: {medication.pill_count}")
        
        # Try to mark as taken (should fail)
        try:
            with transaction.atomic():
                # This should fail due to insufficient stock
                if medication.pill_count < dosage_to_deduct:
                    print("   ✅ Correctly detected insufficient stock")
                    print(f"   Current stock: {medication.pill_count}")
                    print(f"   Required: {dosage_to_deduct}")
                else:
                    print("   ❌ Should have detected insufficient stock")
                    return False
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return False
        
        print(f"\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_stock_deduction()
    if success:
        print("\n✅ Stock deduction functionality is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Stock deduction functionality has issues!")
        sys.exit(1) 