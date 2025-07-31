#!/usr/bin/env python
"""
Test script for the Intelligent Stock Tracking System.

This script tests all major components of the intelligent stock tracking system:
- Stock transaction recording
- Predictive analytics
- Usage pattern analysis
- Pharmacy integration
- Prescription renewal management
- Stock visualizations
- Background tasks

Usage:
    python test_intelligent_stock_system.py
"""

import os
import sys
import django
from datetime import datetime, timedelta, date
from decimal import Decimal
import logging

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

from medications.models import (
    Medication, StockTransaction, StockAnalytics, PharmacyIntegration,
    PrescriptionRenewal, StockVisualization, MedicationLog
)
from medications.services import IntelligentStockService, StockAnalyticsService
from medications.tasks import (
    update_stock_analytics_task, predict_stock_depletion_task,
    check_prescription_renewals_task, monitor_stock_levels_task
)

User = get_user_model()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntelligentStockSystemTester:
    """Test class for the intelligent stock tracking system."""
    
    def __init__(self):
        self.stock_service = IntelligentStockService()
        self.analytics_service = StockAnalyticsService()
        self.test_results = {}
        
    def run_all_tests(self):
        """Run all tests and return results."""
        logger.info("Starting Intelligent Stock Tracking System Tests...")
        
        try:
            # Test 1: Basic stock transaction recording
            self.test_stock_transaction_recording()
            
            # Test 2: Predictive analytics
            self.test_predictive_analytics()
            
            # Test 3: Usage pattern analysis
            self.test_usage_pattern_analysis()
            
            # Test 4: Pharmacy integration
            self.test_pharmacy_integration()
            
            # Test 5: Prescription renewal management
            self.test_prescription_renewal_management()
            
            # Test 6: Stock visualization
            self.test_stock_visualization()
            
            # Test 7: Background tasks
            self.test_background_tasks()
            
            # Test 8: Stock analytics service
            self.test_stock_analytics_service()
            
            # Print results
            self.print_test_results()
            
        except Exception as e:
            logger.error(f"Test failed with error: {e}")
            raise
    
    def test_stock_transaction_recording(self):
        """Test stock transaction recording functionality."""
        logger.info("Testing stock transaction recording...")
        
        try:
            # Create test medication
            medication = self._create_test_medication("Test Medication", 100)
            
            # Create test user
            user = self._create_test_user("testuser", "Test User")
            
            # Record dose taken
            initial_stock = medication.pill_count
            transaction_record = self.stock_service.record_dose_taken(
                patient=user,
                medication=medication,
                dosage_amount=Decimal('1.0'),
                notes="Test dose taken"
            )
            
            # Verify transaction was created
            assert transaction_record is not None
            assert transaction_record.quantity == -1
            assert transaction_record.transaction_type == StockTransaction.TransactionType.DOSE_TAKEN
            
            # Verify stock was decremented
            medication.refresh_from_db()
            assert medication.pill_count == initial_stock - 1
            
            # Verify medication log was created
            log_entry = MedicationLog.objects.filter(
                patient=user,
                medication=medication
            ).first()
            assert log_entry is not None
            assert log_entry.status == MedicationLog.Status.TAKEN
            
            self.test_results['stock_transaction_recording'] = 'PASS'
            logger.info("✓ Stock transaction recording test passed")
            
        except Exception as e:
            self.test_results['stock_transaction_recording'] = f'FAIL: {e}'
            logger.error(f"✗ Stock transaction recording test failed: {e}")
    
    def test_predictive_analytics(self):
        """Test predictive analytics functionality."""
        logger.info("Testing predictive analytics...")
        
        try:
            # Create test medication with some transaction history
            medication = self._create_test_medication("Analytics Test Medication", 50)
            self._create_sample_transactions(medication, days=30)
            
            # Test stock depletion prediction
            prediction = self.stock_service.predict_stock_depletion(medication, days_ahead=90)
            
            # Verify prediction structure
            assert 'days_until_stockout' in prediction
            assert 'predicted_stockout_date' in prediction
            assert 'recommended_order_quantity' in prediction
            assert 'confidence_level' in prediction
            
            # Test analytics update
            analytics = self.stock_service.update_stock_analytics(medication)
            assert analytics is not None
            assert analytics.medication == medication
            
            self.test_results['predictive_analytics'] = 'PASS'
            logger.info("✓ Predictive analytics test passed")
            
        except Exception as e:
            self.test_results['predictive_analytics'] = f'FAIL: {e}'
            logger.error(f"✗ Predictive analytics test failed: {e}")
    
    def test_usage_pattern_analysis(self):
        """Test usage pattern analysis functionality."""
        logger.info("Testing usage pattern analysis...")
        
        try:
            # Create test medication with transaction history
            medication = self._create_test_medication("Pattern Test Medication", 100)
            self._create_sample_transactions(medication, days=60)
            
            # Analyze usage patterns
            analysis = self.stock_service.analyze_usage_patterns(medication, days=60)
            
            # Verify analysis structure
            assert 'statistics' in analysis
            assert 'daily_pattern' in analysis
            assert 'weekly_pattern' in analysis
            assert 'monthly_pattern' in analysis
            
            # Verify statistics
            stats = analysis['statistics']
            assert 'mean_daily_usage' in stats
            assert 'total_transactions' in stats
            
            self.test_results['usage_pattern_analysis'] = 'PASS'
            logger.info("✓ Usage pattern analysis test passed")
            
        except Exception as e:
            self.test_results['usage_pattern_analysis'] = f'FAIL: {e}'
            logger.error(f"✗ Usage pattern analysis test failed: {e}")
    
    def test_pharmacy_integration(self):
        """Test pharmacy integration functionality."""
        logger.info("Testing pharmacy integration...")
        
        try:
            # Create test medication
            medication = self._create_test_medication("Pharmacy Test Medication", 10)
            
            # Create pharmacy integration
            pharmacy_integration = PharmacyIntegration.objects.create(
                name="Test Pharmacy",
                pharmacy_name="Test Pharmacy Inc",
                integration_type=PharmacyIntegration.IntegrationType.MANUAL,
                status=PharmacyIntegration.Status.ACTIVE,
                auto_order_enabled=True,
                order_threshold=15,
                order_lead_time_days=3
            )
            
            # Test integration
            success = self.stock_service.integrate_with_pharmacy(medication, pharmacy_integration)
            
            # Verify integration worked
            assert success is True
            
            # Verify transaction was created
            transaction = StockTransaction.objects.filter(
                medication=medication,
                transaction_type=StockTransaction.TransactionType.PURCHASE
            ).first()
            assert transaction is not None
            
            self.test_results['pharmacy_integration'] = 'PASS'
            logger.info("✓ Pharmacy integration test passed")
            
        except Exception as e:
            self.test_results['pharmacy_integration'] = f'FAIL: {e}'
            logger.error(f"✗ Pharmacy integration test failed: {e}")
    
    def test_prescription_renewal_management(self):
        """Test prescription renewal management functionality."""
        logger.info("Testing prescription renewal management...")
        
        try:
            # Create test medication and user
            medication = self._create_test_medication("Renewal Test Medication", 50)
            patient = self._create_test_user("testpatient", "Test Patient", user_type='PATIENT')
            
            # Create prescription renewal
            renewal = PrescriptionRenewal.objects.create(
                patient=patient,
                medication=medication,
                prescription_number="RX001",
                prescribed_by="Dr. Test Physician",
                prescribed_date=timezone.now().date() - timedelta(days=60),
                expiry_date=timezone.now().date() + timedelta(days=25),  # Expiring soon
                status=PrescriptionRenewal.Status.ACTIVE,
                priority=PrescriptionRenewal.Priority.MEDIUM,
                reminder_days_before=30
            )
            
            # Test renewal check
            renewals_needed = self.stock_service.check_prescription_renewals()
            
            # Verify renewal was found
            assert len(renewals_needed) > 0
            assert any(r.medication == medication for r in renewals_needed)
            
            # Test renewal
            new_expiry_date = timezone.now().date() + timedelta(days=90)
            renewal.renew(new_expiry_date)
            
            # Verify renewal
            assert renewal.status == PrescriptionRenewal.Status.RENEWED
            assert renewal.renewed_date == timezone.now().date()
            assert renewal.new_expiry_date == new_expiry_date
            
            self.test_results['prescription_renewal_management'] = 'PASS'
            logger.info("✓ Prescription renewal management test passed")
            
        except Exception as e:
            self.test_results['prescription_renewal_management'] = f'FAIL: {e}'
            logger.error(f"✗ Prescription renewal management test failed: {e}")
    
    def test_stock_visualization(self):
        """Test stock visualization functionality."""
        logger.info("Testing stock visualization...")
        
        try:
            # Create test medication with transaction history
            medication = self._create_test_medication("Visualization Test Medication", 75)
            self._create_sample_transactions(medication, days=30)
            
            # Generate visualization
            visualization = self.stock_service.generate_stock_visualization(
                medication, 
                chart_type='line',
                days=30
            )
            
            # Verify visualization was created
            assert visualization is not None
            assert visualization.medication == medication
            assert visualization.chart_type == StockVisualization.ChartType.LINE
            assert visualization.is_active is True
            
            # Verify chart data
            assert 'chart_data' in visualization.__dict__ or hasattr(visualization, 'chart_data')
            
            self.test_results['stock_visualization'] = 'PASS'
            logger.info("✓ Stock visualization test passed")
            
        except Exception as e:
            self.test_results['stock_visualization'] = f'FAIL: {e}'
            logger.error(f"✗ Stock visualization test failed: {e}")
    
    def test_background_tasks(self):
        """Test background task functionality."""
        logger.info("Testing background tasks...")
        
        try:
            # Create test medication
            medication = self._create_test_medication("Task Test Medication", 60)
            
            # Test analytics update task
            result = update_stock_analytics_task.delay(medication_id=medication.id)
            assert result is not None
            
            # Test prediction task
            result = predict_stock_depletion_task.delay(medication_id=medication.id)
            assert result is not None
            
            # Test renewal check task
            result = check_prescription_renewals_task.delay()
            assert result is not None
            
            # Test monitoring task
            result = monitor_stock_levels_task.delay()
            assert result is not None
            
            self.test_results['background_tasks'] = 'PASS'
            logger.info("✓ Background tasks test passed")
            
        except Exception as e:
            self.test_results['background_tasks'] = f'FAIL: {e}'
            logger.error(f"✗ Background tasks test failed: {e}")
    
    def test_stock_analytics_service(self):
        """Test stock analytics service functionality."""
        logger.info("Testing stock analytics service...")
        
        try:
            # Create test medications
            medications = []
            for i in range(3):
                medication = self._create_test_medication(f"Analytics Test Medication {i+1}", 50 + i*10)
                self._create_sample_transactions(medication, days=30)
                medications.append(medication)
            
            # Generate stock report
            start_date = timezone.now().date() - timedelta(days=30)
            end_date = timezone.now().date()
            report = self.analytics_service.generate_stock_report(start_date, end_date)
            
            # Verify report structure
            assert 'summary' in report
            assert 'medications' in report
            assert 'alerts' in report
            assert 'recommendations' in report
            
            # Verify summary
            summary = report['summary']
            assert 'total_medications' in summary
            assert 'total_transactions' in summary
            
            # Verify medications data
            assert len(report['medications']) >= 3
            
            self.test_results['stock_analytics_service'] = 'PASS'
            logger.info("✓ Stock analytics service test passed")
            
        except Exception as e:
            self.test_results['stock_analytics_service'] = f'FAIL: {e}'
            logger.error(f"✗ Stock analytics service test failed: {e}")
    
    def _create_test_medication(self, name, pill_count):
        """Create a test medication."""
        return Medication.objects.create(
            name=name,
            generic_name=f"Generic {name}",
            strength="500mg",
            dosage_unit="mg",
            pill_count=pill_count,
            low_stock_threshold=10,
            description=f"Test medication: {name}",
            manufacturer="Test Manufacturer"
        )
    
    def _create_test_user(self, username, full_name, user_type='HEALTHCARE_PROVIDER'):
        """Create a test user."""
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f"{username}@test.com",
                'first_name': full_name.split()[0],
                'last_name': full_name.split()[-1] if len(full_name.split()) > 1 else "",
                'user_type': user_type,
                'is_active': True
            }
        )
        return user
    
    def _create_sample_transactions(self, medication, days=30):
        """Create sample transaction data for testing."""
        import random
        
        users = list(User.objects.filter(is_staff=True)[:3])
        if not users:
            users = [self._create_test_user("testuser", "Test User")]
        
        for i in range(days):
            transaction_date = timezone.now() - timedelta(days=i)
            
            # Random transaction type
            transaction_types = [
                StockTransaction.TransactionType.DOSE_TAKEN,
                StockTransaction.TransactionType.PURCHASE,
                StockTransaction.TransactionType.ADJUSTMENT,
            ]
            
            transaction_type = random.choice(transaction_types)
            
            # Random quantity
            if transaction_type == StockTransaction.TransactionType.DOSE_TAKEN:
                quantity = -random.randint(1, 3)
            elif transaction_type == StockTransaction.TransactionType.PURCHASE:
                quantity = random.randint(10, 30)
            else:
                quantity = random.randint(-5, 5)
            
            # Create transaction
            StockTransaction.objects.create(
                medication=medication,
                user=random.choice(users),
                transaction_type=transaction_type,
                quantity=quantity,
                unit_price=Decimal('10.00') if quantity > 0 else None,
                total_amount=Decimal('10.00') * abs(quantity) if quantity > 0 else None,
                notes=f"Test {transaction_type} transaction",
                reference_number=f"TEST_{transaction_date.strftime('%Y%m%d')}_{i}",
                created_at=transaction_date
            )
    
    def print_test_results(self):
        """Print test results summary."""
        logger.info("\n" + "="*60)
        logger.info("INTELLIGENT STOCK TRACKING SYSTEM TEST RESULTS")
        logger.info("="*60)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.test_results.items():
            if result == 'PASS':
                logger.info(f"✓ {test_name}: PASS")
                passed += 1
            else:
                logger.error(f"✗ {test_name}: {result}")
                failed += 1
        
        logger.info("-"*60)
        logger.info(f"Total Tests: {len(self.test_results)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed == 0:
            logger.info("\n🎉 ALL TESTS PASSED! Intelligent Stock Tracking System is working correctly.")
        else:
            logger.error(f"\n❌ {failed} test(s) failed. Please check the errors above.")
        
        logger.info("="*60)


def main():
    """Main function to run the tests."""
    try:
        tester = IntelligentStockSystemTester()
        tester.run_all_tests()
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 