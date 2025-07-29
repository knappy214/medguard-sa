"""
Django management command to set up the intelligent stock tracking system.

This command:
- Creates initial stock analytics for existing medications
- Sets up pharmacy integrations
- Creates sample stock visualizations
- Configures initial prescription renewals
- Runs initial analytics calculations
"""

import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from medications.models import (
    Medication, StockTransaction, StockAnalytics, PharmacyIntegration,
    PrescriptionRenewal, StockVisualization
)
from medications.services import IntelligentStockService, StockAnalyticsService

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Set up the intelligent stock tracking system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force setup even if system is already configured',
        )
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Create sample transaction data for testing',
        )
        parser.add_argument(
            '--medication-id',
            type=int,
            help='Set up system for specific medication ID only',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up Intelligent Stock Tracking System...')
        )

        try:
            with transaction.atomic():
                if options['medication_id']:
                    medications = [Medication.objects.get(id=options['medication_id'])]
                else:
                    medications = Medication.objects.all()

                # Initialize services
                stock_service = IntelligentStockService()
                analytics_service = StockAnalyticsService()

                # Step 1: Create stock analytics for medications
                self.stdout.write('Creating stock analytics...')
                analytics_created = self._create_stock_analytics(medications, stock_service)

                # Step 2: Set up pharmacy integrations
                self.stdout.write('Setting up pharmacy integrations...')
                integrations_created = self._setup_pharmacy_integrations()

                # Step 3: Create sample prescription renewals
                self.stdout.write('Setting up prescription renewals...')
                renewals_created = self._setup_prescription_renewals(medications)

                # Step 4: Create stock visualizations
                self.stdout.write('Creating stock visualizations...')
                visualizations_created = self._create_stock_visualizations(medications, stock_service)

                # Step 5: Create sample transaction data if requested
                if options['create_sample_data']:
                    self.stdout.write('Creating sample transaction data...')
                    sample_data_created = self._create_sample_transaction_data(medications)

                # Step 6: Run initial analytics calculations
                self.stdout.write('Running initial analytics calculations...')
                calculations_completed = self._run_initial_calculations(medications, stock_service)

                # Summary
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nIntelligent Stock Tracking System setup completed successfully!\n'
                        f'• Stock Analytics: {analytics_created} created\n'
                        f'• Pharmacy Integrations: {integrations_created} created\n'
                        f'• Prescription Renewals: {renewals_created} created\n'
                        f'• Stock Visualizations: {visualizations_created} created\n'
                        f'• Analytics Calculations: {calculations_completed} completed'
                    )
                )

                if options['create_sample_data']:
                    self.stdout.write(
                        self.style.SUCCESS(f'• Sample Transaction Data: {sample_data_created} created')
                    )

        except Exception as e:
            raise CommandError(f'Error setting up intelligent stock system: {e}')

    def _create_stock_analytics(self, medications, stock_service):
        """Create stock analytics for medications."""
        created_count = 0
        
        for medication in medications:
            try:
                # Check if analytics already exist
                if hasattr(medication, 'stock_analytics'):
                    if not self.options['force']:
                        continue
                    # Update existing analytics
                    analytics = medication.stock_analytics
                else:
                    # Create new analytics
                    analytics = StockAnalytics.objects.create(
                        medication=medication,
                        calculation_window_days=90
                    )
                    created_count += 1

                # Run initial calculation
                stock_service.update_stock_analytics(medication)
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error creating analytics for {medication.name}: {e}')
                )
                continue

        return created_count

    def _setup_pharmacy_integrations(self):
        """Set up sample pharmacy integrations."""
        integrations_data = [
            {
                'name': 'Local Pharmacy API',
                'pharmacy_name': 'MedPharm Local',
                'integration_type': PharmacyIntegration.IntegrationType.API,
                'status': PharmacyIntegration.Status.INACTIVE,
                'api_endpoint': 'https://api.medpharm.local/v1',
                'auto_order_enabled': False,
                'order_threshold': 10,
                'order_lead_time_days': 3,
            },
            {
                'name': 'National Pharmacy Webhook',
                'pharmacy_name': 'PharmaNet National',
                'integration_type': PharmacyIntegration.IntegrationType.WEBHOOK,
                'status': PharmacyIntegration.Status.INACTIVE,
                'webhook_url': 'https://webhook.pharmanet.com/orders',
                'auto_order_enabled': False,
                'order_threshold': 15,
                'order_lead_time_days': 5,
            },
            {
                'name': 'Manual Pharmacy Integration',
                'pharmacy_name': 'Manual Pharmacy',
                'integration_type': PharmacyIntegration.IntegrationType.MANUAL,
                'status': PharmacyIntegration.Status.ACTIVE,
                'auto_order_enabled': True,
                'order_threshold': 20,
                'order_lead_time_days': 7,
            },
        ]

        created_count = 0
        for data in integrations_data:
            try:
                integration, created = PharmacyIntegration.objects.get_or_create(
                    name=data['name'],
                    defaults=data
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created pharmacy integration: {integration.name}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error creating pharmacy integration {data["name"]}: {e}')
                )

        return created_count

    def _setup_prescription_renewals(self, medications):
        """Set up sample prescription renewals."""
        created_count = 0
        
        # Get sample patients
        patients = User.objects.filter(user_type=User.UserType.PATIENT)[:5]
        if not patients:
            self.stdout.write(
                self.style.WARNING('No patients found. Skipping prescription renewals setup.')
            )
            return 0

        for medication in medications[:3]:  # Limit to first 3 medications
            for patient in patients:
                try:
                    # Create prescription renewal
                    renewal = PrescriptionRenewal.objects.create(
                        patient=patient,
                        medication=medication,
                        prescription_number=f'RX{medication.id:04d}{patient.id:04d}',
                        prescribed_by='Dr. Sample Physician',
                        prescribed_date=timezone.now().date() - timedelta(days=60),
                        expiry_date=timezone.now().date() + timedelta(days=30),
                        status=PrescriptionRenewal.Status.ACTIVE,
                        priority=PrescriptionRenewal.Priority.MEDIUM,
                        reminder_days_before=30,
                        notes=f'Sample prescription for {medication.name}'
                    )
                    created_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Error creating prescription renewal: {e}')
                    )
                    continue

        return created_count

    def _create_stock_visualizations(self, medications, stock_service):
        """Create stock visualizations for medications."""
        created_count = 0
        
        for medication in medications:
            try:
                # Create line chart visualization
                visualization = StockVisualization.objects.create(
                    medication=medication,
                    chart_type=StockVisualization.ChartType.LINE,
                    title=f'Stock Level Trend - {medication.name}',
                    description=f'Stock level trend over the last 30 days for {medication.name}',
                    start_date=timezone.now().date() - timedelta(days=30),
                    end_date=timezone.now().date(),
                    is_active=True,
                    auto_refresh=True,
                    refresh_interval_hours=24
                )
                created_count += 1
                
                # Generate initial chart data
                stock_service.generate_stock_visualization(medication, days=30)
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error creating visualization for {medication.name}: {e}')
                )
                continue

        return created_count

    def _create_sample_transaction_data(self, medications):
        """Create sample transaction data for testing."""
        created_count = 0
        
        # Get sample users
        users = User.objects.filter(is_staff=True)[:3]
        if not users:
            users = [User.objects.first()]

        for medication in medications:
            try:
                # Create sample transactions over the last 30 days
                for i in range(30):
                    transaction_date = timezone.now() - timedelta(days=i)
                    
                    # Random transaction type
                    import random
                    transaction_types = [
                        StockTransaction.TransactionType.DOSE_TAKEN,
                        StockTransaction.TransactionType.PURCHASE,
                        StockTransaction.TransactionType.ADJUSTMENT,
                    ]
                    
                    transaction_type = random.choice(transaction_types)
                    
                    # Random quantity
                    if transaction_type == StockTransaction.TransactionType.DOSE_TAKEN:
                        quantity = -random.randint(1, 3)  # Negative for consumption
                    elif transaction_type == StockTransaction.TransactionType.PURCHASE:
                        quantity = random.randint(10, 50)  # Positive for purchase
                    else:
                        quantity = random.randint(-5, 5)  # Mixed for adjustments

                    # Create transaction
                    transaction = StockTransaction.objects.create(
                        medication=medication,
                        user=random.choice(users),
                        transaction_type=transaction_type,
                        quantity=quantity,
                        unit_price=Decimal('10.00') if quantity > 0 else None,
                        total_amount=Decimal('10.00') * abs(quantity) if quantity > 0 else None,
                        notes=f'Sample {transaction_type} transaction',
                        reference_number=f'SAMPLE_{transaction_date.strftime("%Y%m%d")}_{i}',
                        created_at=transaction_date
                    )
                    created_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error creating sample data for {medication.name}: {e}')
                )
                continue

        return created_count

    def _run_initial_calculations(self, medications, stock_service):
        """Run initial analytics calculations."""
        completed_count = 0
        
        for medication in medications:
            try:
                # Predict stock depletion
                stock_service.predict_stock_depletion(medication)
                
                # Analyze usage patterns
                stock_service.analyze_usage_patterns(medication)
                
                # Update analytics
                stock_service.update_stock_analytics(medication)
                
                completed_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error running calculations for {medication.name}: {e}')
                )
                continue

        return completed_count 