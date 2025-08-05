"""
Views for medications app.

This module contains API views for managing medications, schedules, logs, and alerts.
"""

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, F, Sum, Prefetch
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from django.core.cache import cache
from rest_framework import viewsets, permissions, status, filters
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta, date, time
from decimal import Decimal
import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import (
    Medication, MedicationSchedule, MedicationLog, StockAlert, 
    StockAnalytics, PharmacyIntegration, StockTransaction,
    PrescriptionRenewal, StockVisualization, User
)
from .serializers import (
    MedicationSerializer,
    MedicationDetailSerializer,
    MedicationScheduleSerializer,
    MedicationScheduleDetailSerializer,
    MedicationLogSerializer,
    MedicationLogDetailSerializer,
    StockAlertSerializer,
    StockAlertDetailSerializer,
    MedicationStatsSerializer,
    StockAnalyticsSerializer,
    StockVisualizationSerializer,
    PharmacyIntegrationSerializer,
    PrescriptionParser
)
from .services import IntelligentStockService, StockAnalyticsService, MedicationCacheService


logger = logging.getLogger(__name__)


class OptimizedPagination(PageNumberPagination):
    """
    Optimized pagination for large datasets.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'


class MedicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing medications.
    
    Provides CRUD operations for medication management with filtering and search capabilities.
    """
    
    queryset = Medication.objects.select_related().prefetch_related(
        'schedules',
        'logs',
        'stock_alerts',
        'stock_transactions'
    )
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['medication_type', 'prescription_type', 'manufacturer']
    search_fields = ['name', 'generic_name', 'brand_name', 'description', 'active_ingredients']
    ordering_fields = ['name', 'created_at', 'updated_at', 'pill_count']
    ordering = ['name']
    pagination_class = OptimizedPagination
    
    def get_queryset(self):
        """
        Optimize queryset with select_related and prefetch_related.
        """
        queryset = super().get_queryset()
        
        # Apply lazy loading optimizations
        if self.action == 'list':
            # For list view, only fetch essential fields
            queryset = queryset.only(
                'id', 'name', 'generic_name', 'medication_type', 
                'prescription_type', 'strength', 'pill_count', 
                'low_stock_threshold', 'manufacturer', 'created_at'
            )
        elif self.action == 'retrieve':
            # For detail view, fetch all related data
            queryset = queryset.select_related().prefetch_related(
                Prefetch('schedules', queryset=MedicationSchedule.objects.filter(status='active')),
                Prefetch('logs', queryset=MedicationLog.objects.order_by('-scheduled_time')[:10]),
                Prefetch('stock_alerts', queryset=StockAlert.objects.filter(status='active')),
                'stock_transactions'
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return MedicationDetailSerializer
        return MedicationSerializer
    
    # Temporarily comment out custom actions to debug POST issue
    # @action(detail=False, methods=['get'])
    # def low_stock(self, request):
    #     """Get medications with low stock."""
    #     cache_key = f"medications_low_stock_{request.user.id}"
    #     cached_data = cache.get(cache_key)
    #     
    #     if cached_data is None:
    #         medications = self.get_queryset().filter(
    #             pill_count__lte=F('low_stock_threshold')
    #         ).only('id', 'name', 'pill_count', 'low_stock_threshold')
    #         
    #         serializer = self.get_serializer(medications, many=True)
    #         cached_data = serializer.data
    #         cache.set(cache_key, cached_data, 300)  # Cache for 5 minutes
    #     
    #     return Response(cached_data)
    
    # @cache_page(60 * 30)  # Cache for 30 minutes
    # @action(detail=False, methods=['get'])
    # def expiring_soon(self, request):
    #     """Get medications expiring soon (within 30 days)."""
    #     cache_key = f"medications_expiring_soon_{request.user.id}"
    #     cached_data = cache.get(cache_key)
    #     
    #     if cached_data is None:
    #         thirty_days_from_now = timezone.now().date() + timedelta(days=30)
    #         medications = self.get_queryset().filter(
    #             expiration_date__lte=thirty_days_from_now,
    #             expiration_date__gte=timezone.now().date()
    #         ).only('id', 'name', 'expiration_date', 'pill_count')
    #         
    #         serializer = self.get_serializer(medications, many=True)
    #         cached_data = serializer.data
    #         cache.set(cache_key, cached_data, 600)  # Cache for 10 minutes
    #     
    #     return Response(cached_data)
    
    # @cache_page(60 * 60)  # Cache for 1 hour
    # @action(detail=False, methods=['get'])
    # def expired(self, request):
    #     """Get expired medications."""
    #     cache_key = f"medications_expired_{request.user.id}"
    #     cached_data = cache.get(cache_key)
    #     
    #     if cached_data is None:
    #         medications = self.get_queryset().filter(
    #             expiration_date__lt=timezone.now().date()
    #         ).only('id', 'name', 'expiration_date', 'pill_count')
    #         
    #         serializer = self.get_serializer(medications, many=True)
    #         cached_data = serializer.data
    #         cache.set(cache_key, cached_data, 1800)  # Cache for 30 minutes
    #     
    #     return Response(cached_data)
    
    # @action(detail=False, methods=['get'])
    # def stats(self, request):
    #     """Get medication statistics with lazy loading."""
    #     cache_key = f"medication_stats_{request.user.id}"
    #     cached_stats = cache.get(cache_key)
    #     
    #     if cached_stats is None:
    #         # Use lazy loading for statistics
    #         total_medications = self.get_queryset().count()
    #         low_stock_count = self.get_queryset().filter(
    #             pill_count__lte=F('low_stock_threshold')
    #         ).count()
    #         expiring_soon_count = self.get_queryset().filter(
    #             expiration_date__lte=timezone.now().date() + timedelta(days=30),
    #             expiration_date__gte=timezone.now().date()
    #         ).count()
    #         
    #         cached_stats = {
    #             'total_medications': total_medications,
    #             'low_stock_count': low_stock_count,
    #             'expiring_soon_count': expiring_soon_count,
    #             'last_updated': timezone.now().isoformat()
    #         }
    #         cache.set(cache_key, cached_stats, 900)  # Cache for 15 minutes
    #     
    #     return Response(cached_stats)
    
    # @action(detail=True, methods=['get'])
    # def schedules(self, request, pk=None):
    #     """Get all schedules for a specific medication with lazy loading."""
    #     medication = self.get_object()
    #     
    #     # Use lazy loading for schedules
    #     schedules = MedicationSchedule.objects.filter(
    #         medication=medication
    #     ).select_related('patient').only(
    #         'id', 'timing', 'status', 'start_date', 'end_date',
    #         'patient__id', 'patient__first_name', 'patient__last_name'
    #     )
    #     
    #     # Paginate schedules
    #     paginator = Paginator(schedules, 10)
    #     page_number = request.GET.get('page', 1)
    #     page_obj = paginator.get_page(page_number)
    #     
    #     serializer = MedicationScheduleSerializer(page_obj, many=True)
    #     return Response({
    #         'results': serializer.data,
    #         'count': paginator.count,
    #         'next': page_obj.has_next(),
    #         'previous': page_obj.has_previous(),
    #     })
    
    # @action(detail=True, methods=['get'])
    # def logs(self, request, pk=None):
    #     """Get all logs for a specific medication with lazy loading."""
    #     medication = self.get_object()
    #     
    #     # Use lazy loading for logs
    #     logs = MedicationLog.objects.filter(
    #         medication=medication
    #     ).select_related('patient').only(
    #         'id', 'scheduled_time', 'actual_time', 'status', 'dosage_taken',
    #         'patient__id', 'patient__first_name', 'patient__last_name'
    #     ).order_by('-scheduled_time')
    #     
    #     # Paginate logs
    #     paginator = Paginator(logs, 20)
    #     page_number = request.GET.get('page', 1)
    #     page_obj = paginator.get_page(page_number)
    #     
    #     serializer = MedicationLogSerializer(page_obj, many=True)
    #     return Response({
    #         'results': serializer.data,
    #         'count': paginator.count,
    #         'next': page_obj.has_next(),
    #         'previous': page_obj.has_previous(),
    #     })
    
    # @action(detail=True, methods=['get'])
    # def alerts(self, request, pk=None):
    #     """Get all alerts for a specific medication with lazy loading."""
    #     medication = self.get_object()
    #     
    #     # Use lazy loading for alerts
    #     alerts = StockAlert.objects.filter(
    #         medication=medication
    #     ).select_related('created_by').only(
    #         'id', 'alert_type', 'priority', 'status', 'created_at',
    #         'created_by__id', 'created_by__first_name', 'created_by__last_name'
    #     ).order_by('-created_at')
    #     
    #     # Paginate alerts
    #     paginator = Paginator(alerts, 10)
    #     page_number = request.GET.get('page', 1)
    #     page_obj = paginator.get_page(page_number)
    #     
    #     serializer = StockAlertSerializer(page_obj, many=True)
    #     return Response({
    #         'results': serializer.data,
    #         'count': paginator.count,
    #         'next': page_obj.has_next(),
    #         'previous': page_obj.has_previous(),
    #     })

    # @action(detail=True, methods=['get'])
    # def analytics(self, request, pk=None):
    #     """
    #     Get stock analytics for a specific medication with caching.
    #     """
    #     try:
    #         medication = self.get_object()
    #         cache_key = f"medication_analytics_{medication.id}"
    #         cached_analytics = cache.get(cache_key)
    #         
    #         if cached_analytics is None:
    #             service = IntelligentStockService()
    #             
    #             # Get or create stock analytics
    #             analytics, created = StockAnalytics.objects.get_or_create(
    #                 medication=medication,
    #                 defaults={
    #                     'daily_usage_rate': 0.0,
    #                     'weekly_usage_rate': 0.0,
    #                     'monthly_usage_rate': 0.0,
    #                     'calculation_window_days': 90
    #                 }
    #             )
    #             
    #             # Update analytics if needed (older than 24 hours)
    #             if created or not analytics.last_calculated or \
    #                (timezone.now() - analytics.last_calculated).days > 0:
    #                 service.update_stock_analytics(medication)
    #                 analytics.refresh_from_db()
    #             
    #             serializer = StockAnalyticsSerializer(analytics)
    #             cached_analytics = serializer.data
    #             cache.set(cache_key, cached_analytics, 3600)  # Cache for 1 hour
    #         
    #         return Response(cached_analytics)
    #         
    #     except Exception as e:
    #         return Response(
    #             {'error': str(e)},
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #         )
    
    # @action(detail=True, methods=['post'])
    # def predict_stockout(self, request, pk=None):
    #     """
    #     Get stock depletion prediction for a medication.
    #     """
    #     try:
    #         medication = self.get_object()
    #         cache_key = f"stockout_prediction_{medication.id}"
    #         cached_prediction = cache.get(cache_key)
    #         
    #         if cached_prediction is None:
    #             service = IntelligentStockService()
    #             prediction = service.predict_stock_depletion(medication)
    #             cached_prediction = prediction
    #             cache.set(cache_key, cached_prediction, 1800)  # Cache for 30 minutes
    #         
    #         return Response(cached_prediction)
    #         
    #     except Exception as e:
    #         return Response(
    #             {'error': str(e)},
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #         )

    # @action(detail=True, methods=['get'])
    # def stock_visualization(self, request, pk=None):
    #     """
    #     Get stock visualization data for a medication.
    #     """
    #     try:
    #         medication = self.get_object()
    #         cache_key = f"stock_visualization_{medication.id}"
    #         cached_visualization = cache.get(cache_key)
    #         
    #         if cached_visualization is None:
    #             visualization, created = StockVisualization.objects.get_or_create(
    #                 medication=medication,
    #                 defaults={'chart_data': {}, 'last_updated': timezone.now()}
    #             )
    #             
    #             if created or (timezone.now() - visualization.last_updated).hours > 4:
    #                 # Update visualization data
    #                 from .tasks import generate_stock_visualizations
    #                 generate_stock_visualizations.delay(medication.id)
    #                 visualization.refresh_from_db()
    #             
    #             serializer = StockVisualizationSerializer(visualization)
    #             cached_visualization = serializer.data
    #             cache.set(cache_key, cached_visualization, 14400)  # Cache for 4 hours
    #         
    #         return Response(cached_visualization)
    #         
    #     except Exception as e:
    #         return Response(
    #             {'error': str(e)},
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #         )
    
    # @action(detail=True, methods=['post'])
    # def record_dose(self, request, pk=None):
    #     """
    #     Record a dose taken and update stock accordingly.
    #     """
    #     try:
    #         medication = self.get_object()
    #         dosage_amount = Decimal(request.data.get('dosage_amount', 1))
    #         notes = request.data.get('notes', '')
    #         schedule_id = request.data.get('schedule_id')
    #         
    #         service = IntelligentStockService()
    #         
    #         # Get schedule if provided
    #         schedule = None
    #         if schedule_id:
    #             try:
    #                 schedule = MedicationSchedule.objects.get(id=schedule_id)
    #             except MedicationSchedule.DoesNotExist:
    #                 pass
    #         
    #         # Record the dose
    #         transaction = service.record_dose_taken(
    #             patient=request.user,
    #             medication=medication,
    #             dosage_amount=dosage_amount,
    #             schedule=schedule,
    #             notes=notes
    #         )
    #         
    #         return Response({
    #             'message': 'Dose recorded successfully',
    #             'transaction_id': transaction.id,
    #             'new_stock': medication.pill_count
    #         })
    #         
    #     except Exception as e:
    #         return Response(
    #             {'error': str(e)},
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #         )
    
    # @action(detail=True, methods=['get'])
    # def usage_patterns(self, request, pk=None):
    #     """
    #     Get usage pattern analysis for a medication.
    #     """
    #     try:
    #         medication = self.get_object()
    #         days = int(request.query_params.get('days', 90))
    #         
    #         service = IntelligentStockService()
    #         patterns = service.analyze_usage_patterns(medication, days)
    #         
    #         return Response(patterns)
    #         
    #     except Exception as e:
    #         return Response(
    #             {'error': str(e)},
    #             status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #         )

    @action(detail=False, methods=['post'])
    def bulk_create_from_prescription(self, request):
        """
        Create multiple medications from prescription data with schedules.
        
        Expected payload:
        {
            "medications": [
                {
                    "name": "Medication Name",
                    "generic_name": "Generic Name",
                    "strength": "500mg",
                    "medication_type": "tablet",
                    "prescription_type": "prescription",
                    "initial_stock": 30,
                    "schedule_data": {
                        "timing": "morning",
                        "dosage_amount": 1,
                        "frequency": "daily",
                        "start_date": "2024-01-01",
                        "instructions": "Take with food"
                    }
                }
            ],
            "patient_id": 1,
            "prescription_number": "RX123456",
            "prescribed_by": "Dr. Smith",
            "prescribed_date": "2024-01-01"
        }
        """
        try:
            medications_data = request.data.get('medications', [])
            patient_id = request.data.get('patient_id')
            prescription_number = request.data.get('prescription_number', '')
            prescribed_by = request.data.get('prescribed_by', '')
            prescribed_date = request.data.get('prescribed_date')
            
            if not medications_data:
                return Response(
                    {'error': 'No medications provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not patient_id:
                return Response(
                    {'error': 'Patient ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get patient
            try:
                patient = User.objects.get(id=patient_id, user_type='PATIENT')
            except User.DoesNotExist:
                return Response(
                    {'error': 'Patient not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            created_medications = []
            created_schedules = []
            created_transactions = []
            errors = []
            
            # Use database transaction for rollback on failure
            with transaction.atomic():
                for i, med_data in enumerate(medications_data):
                    try:
                        # Extract schedule data
                        schedule_data = med_data.pop('schedule_data', {})
                        initial_stock = med_data.pop('initial_stock', 0)
                        
                        # Create medication
                        medication = Medication.objects.create(
                            **med_data,
                            pill_count=initial_stock
                        )
                        created_medications.append(medication)
                        
                        # Create stock transaction for initial stock
                        if initial_stock > 0:
                            stock_transaction = StockTransaction.objects.create(
                                medication=medication,
                                user=request.user,
                                transaction_type=StockTransaction.TransactionType.PURCHASE,
                                quantity=initial_stock,
                                notes=f"Initial stock from prescription {prescription_number}",
                                reference_number=f"INIT_{prescription_number}_{medication.id}",
                                batch_number=f"BATCH_{prescription_number}_{i+1}"
                            )
                            created_transactions.append(stock_transaction)
                        
                        # Create schedule if provided
                        if schedule_data:
                            schedule = MedicationSchedule.objects.create(
                                patient=patient,
                                medication=medication,
                                **schedule_data
                            )
                            created_schedules.append(schedule)
                        
                        # Log the creation
                        logger.info(
                            f"Medication created from prescription: {medication.name} "
                            f"(ID: {medication.id}, Stock: {initial_stock}) "
                            f"by user {request.user.username}"
                        )
                        
                    except Exception as e:
                        errors.append({
                            'index': i,
                            'medication_name': med_data.get('name', 'Unknown'),
                            'error': str(e)
                        })
                        # Rollback the entire transaction if any medication fails
                        raise ValidationError(f"Failed to create medication at index {i}: {str(e)}")
                
                # Create prescription renewal record if prescription data provided
                if prescription_number and prescribed_by and prescribed_date:
                    for medication in created_medications:
                        PrescriptionRenewal.objects.create(
                            patient=patient,
                            medication=medication,
                            prescription_number=prescription_number,
                            prescribed_by=prescribed_by,
                            prescribed_date=prescribed_date,
                            expiry_date=prescribed_date + timedelta(days=365)  # Default 1 year
                        )
            
            # Prepare response data
            response_data = {
                'message': f'Successfully created {len(created_medications)} medications',
                'created_medications': [
                    {
                        'id': med.id,
                        'name': med.name,
                        'initial_stock': med.pill_count
                    } for med in created_medications
                ],
                'created_schedules': len(created_schedules),
                'created_transactions': len(created_transactions),
                'prescription_number': prescription_number,
                'patient': {
                    'id': patient.id,
                    'name': patient.get_full_name()
                }
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in bulk_create_from_prescription: {e}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def prescription_upload(self, request):
        """
        Handle OCR-processed prescription data upload.
        
        Expected payload:
        {
            "ocr_data": {
                "medications": [
                    {
                        "name": "Extracted medication name",
                        "strength": "500mg",
                        "instructions": "Take one tablet daily",
                        "quantity": 30
                    }
                ],
                "prescription_info": {
                    "prescription_number": "RX123456",
                    "prescribed_by": "Dr. Smith",
                    "prescribed_date": "2024-01-01"
                }
            },
            "patient_id": 1,
            "confidence_score": 0.85
        }
        """
        try:
            ocr_data = request.data.get('ocr_data', {})
            patient_id = request.data.get('patient_id')
            confidence_score = request.data.get('confidence_score', 0.0)
            
            if not ocr_data:
                return Response(
                    {'error': 'No OCR data provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not patient_id:
                return Response(
                    {'error': 'Patient ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get patient
            try:
                patient = User.objects.get(id=patient_id, user_type='PATIENT')
            except User.DoesNotExist:
                return Response(
                    {'error': 'Patient not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            medications_data = ocr_data.get('medications', [])
            prescription_info = ocr_data.get('prescription_info', {})
            
            processed_medications = []
            enrichment_results = []
            
            for med_data in medications_data:
                try:
                    # Enrich medication data using external APIs
                    enriched_data = self._enrich_medication_data(med_data)
                    enrichment_results.append(enriched_data)
                    
                    # Prepare medication data for creation
                    medication_data = {
                        'name': enriched_data.get('name', med_data.get('name')),
                        'generic_name': enriched_data.get('generic_name', ''),
                        'strength': enriched_data.get('strength', med_data.get('strength', '')),
                        'medication_type': enriched_data.get('medication_type', 'tablet'),
                        'prescription_type': 'prescription',
                        'pill_count': med_data.get('quantity', 0),
                        'description': enriched_data.get('description', ''),
                        'active_ingredients': enriched_data.get('active_ingredients', ''),
                        'manufacturer': enriched_data.get('manufacturer', ''),
                        'side_effects': enriched_data.get('side_effects', ''),
                        'contraindications': enriched_data.get('contraindications', ''),
                        'storage_instructions': enriched_data.get('storage_instructions', '')
                    }
                    
                    # Parse prescription instructions
                    instructions = med_data.get('instructions', '')
                    if instructions:
                        parsed = PrescriptionParser.parse_instructions(instructions)
                        if parsed:
                            medication_data['schedule_data'] = {
                                'timing': parsed.get('timing', 'morning'),
                                'dosage_amount': parsed.get('dosage_amount', 1),
                                'frequency': parsed.get('frequency', 'daily'),
                                'start_date': timezone.now().date(),
                                'instructions': instructions
                            }
                    
                    processed_medications.append(medication_data)
                    
                except Exception as e:
                    logger.error(f"Error processing OCR medication data: {e}")
                    continue
            
            # Create medications using bulk_create_from_prescription logic
            if processed_medications:
                bulk_data = {
                    'medications': processed_medications,
                    'patient_id': patient_id,
                    'prescription_number': prescription_info.get('prescription_number', ''),
                    'prescribed_by': prescription_info.get('prescribed_by', ''),
                    'prescribed_date': prescription_info.get('prescribed_date')
                }
                
                # Create medications using the same logic as bulk_create_from_prescription
                created_medications = []
                created_schedules = []
                created_transactions = []
                
                with transaction.atomic():
                    for i, med_data in enumerate(processed_medications):
                        # Extract schedule data
                        schedule_data = med_data.pop('schedule_data', {})
                        initial_stock = med_data.pop('pill_count', 0)
                        
                        # Create medication
                        medication = Medication.objects.create(
                            **med_data,
                            pill_count=initial_stock
                        )
                        created_medications.append(medication)
                        
                        # Create stock transaction for initial stock
                        if initial_stock > 0:
                            stock_transaction = StockTransaction.objects.create(
                                medication=medication,
                                user=request.user,
                                transaction_type=StockTransaction.TransactionType.PURCHASE,
                                quantity=initial_stock,
                                notes=f"Initial stock from OCR prescription",
                                reference_number=f"OCR_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{i+1}",
                                batch_number=f"OCR_BATCH_{i+1}"
                            )
                            created_transactions.append(stock_transaction)
                        
                        # Create schedule if provided
                        if schedule_data:
                            schedule = MedicationSchedule.objects.create(
                                patient=patient,
                                medication=medication,
                                **schedule_data
                            )
                            created_schedules.append(schedule)
                
                bulk_creation_result = {
                    'created_medications': len(created_medications),
                    'created_schedules': len(created_schedules),
                    'created_transactions': len(created_transactions)
                }
                
                response_data = {
                    'message': 'Prescription processed successfully',
                    'confidence_score': confidence_score,
                    'processed_medications': len(processed_medications),
                    'enrichment_results': enrichment_results,
                    'bulk_creation_result': bulk_creation_result
                }
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'No valid medications found in OCR data'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error in prescription_upload: {e}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _enrich_medication_data(self, med_data):
        """
        Enrich medication data using external APIs (prepare for Perplexity integration).
        
        Args:
            med_data: Raw medication data from OCR
            
        Returns:
            Dict: Enriched medication data
        """
        try:
            name = med_data.get('name', '')
            strength = med_data.get('strength', '')
            
            # TODO: Integrate with Perplexity API for medication enrichment
            # For now, return basic enrichment based on common patterns
            
            enriched_data = {
                'name': name,
                'strength': strength,
                'medication_type': self._detect_medication_type(name, strength),
                'generic_name': self._extract_generic_name(name),
                'description': f"Prescription medication: {name} {strength}",
                'active_ingredients': '',
                'manufacturer': '',
                'side_effects': '',
                'contraindications': '',
                'storage_instructions': 'Store at room temperature. Keep out of reach of children.'
            }
            
            # Log enrichment attempt
            logger.info(f"Medication enrichment attempted for: {name}")
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"Error enriching medication data: {e}")
            return med_data

    def _detect_medication_type(self, name, strength):
        """Detect medication type based on name and strength patterns."""
        name_lower = name.lower()
        strength_lower = strength.lower()
        
        if any(word in name_lower for word in ['tablet', 'tab']):
            return 'tablet'
        elif any(word in name_lower for word in ['capsule', 'cap']):
            return 'capsule'
        elif any(word in name_lower for word in ['liquid', 'syrup', 'suspension']):
            return 'liquid'
        elif any(word in name_lower for word in ['inhaler', 'puff']):
            return 'inhaler'
        elif any(word in name_lower for word in ['cream', 'ointment']):
            return 'cream'
        elif 'ml' in strength_lower or 'drops' in name_lower:
            return 'drops'
        else:
            return 'tablet'  # Default

    def _extract_generic_name(self, name):
        """Extract generic name from medication name."""
        # Simple extraction - in production, use a comprehensive drug database
        common_generics = {
            'paracetamol': 'acetaminophen',
            'acetaminophen': 'acetaminophen',
            'ibuprofen': 'ibuprofen',
            'aspirin': 'acetylsalicylic acid',
            'amoxicillin': 'amoxicillin',
            'omeprazole': 'omeprazole',
            'metformin': 'metformin',
            'atorvastatin': 'atorvastatin',
            'lisinopril': 'lisinopril',
            'amlodipine': 'amlodipine'
        }
        
        name_lower = name.lower()
        for generic, standard_name in common_generics.items():
            if generic in name_lower:
                return standard_name
        
        return ''

    @action(detail=True, methods=['post'])
    def add_stock(self, request, pk=None):
        """
        Add stock to a medication and create stock transaction.
        
        Expected payload:
        {
            "quantity": 30,
            "unit_price": 15.50,
            "batch_number": "BATCH123",
            "expiry_date": "2025-12-31",
            "notes": "Restocked from pharmacy"
        }
        """
        try:
            medication = self.get_object()
            quantity = request.data.get('quantity', 0)
            unit_price = request.data.get('unit_price')
            batch_number = request.data.get('batch_number', '')
            expiry_date = request.data.get('expiry_date')
            notes = request.data.get('notes', '')
            
            if quantity <= 0:
                return Response(
                    {'error': 'Quantity must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate total amount
            total_amount = None
            if unit_price:
                total_amount = Decimal(str(unit_price)) * quantity
            
            # Parse expiry date
            parsed_expiry_date = None
            if expiry_date:
                try:
                    parsed_expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                except ValueError:
                    return Response(
                        {'error': 'Invalid expiry date format. Use YYYY-MM-DD'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            with transaction.atomic():
                # Record stock before addition
                stock_before = medication.pill_count
                
                # Create stock transaction
                stock_transaction = StockTransaction.objects.create(
                    medication=medication,
                    user=request.user,
                    transaction_type=StockTransaction.TransactionType.PURCHASE,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_amount=total_amount,
                    stock_before=stock_before,
                    stock_after=stock_before + quantity,
                    reference_number=f"STOCK_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                    batch_number=batch_number,
                    expiry_date=parsed_expiry_date,
                    notes=notes
                )
                
                # Update medication stock
                medication.pill_count = stock_before + quantity
                if parsed_expiry_date and (not medication.expiration_date or parsed_expiry_date > medication.expiration_date):
                    medication.expiration_date = parsed_expiry_date
                medication.save()
                
                # Update analytics
                service = IntelligentStockService()
                service.update_stock_analytics(medication)
                
                # Log the transaction
                logger.info(
                    f"Stock added to {medication.name}: {quantity} units "
                    f"(Total: {medication.pill_count}) by {request.user.username}"
                )
            
            return Response({
                'message': f'Successfully added {quantity} units to {medication.name}',
                'medication_id': medication.id,
                'medication_name': medication.name,
                'new_stock': medication.pill_count,
                'transaction_id': stock_transaction.id,
                'batch_number': batch_number,
                'expiry_date': parsed_expiry_date
            })
            
        except Exception as e:
            logger.error(f"Error adding stock to medication {pk}: {e}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def audit_trail(self, request, pk=None):
        """
        Get audit trail for medication creation and modifications.
        """
        try:
            medication = self.get_object()
            
            # Get stock transactions
            transactions = StockTransaction.objects.filter(
                medication=medication
            ).select_related('user').order_by('-created_at')
            
            # Get medication logs
            logs = MedicationLog.objects.filter(
                medication=medication
            ).select_related('patient', 'schedule').order_by('-created_at')
            
            # Get stock alerts
            alerts = StockAlert.objects.filter(
                medication=medication
            ).select_related('created_by', 'acknowledged_by').order_by('-created_at')
            
            audit_data = {
                'medication': {
                    'id': medication.id,
                    'name': medication.name,
                    'created_at': medication.created_at,
                    'updated_at': medication.updated_at
                },
                'transactions': [
                    {
                        'id': t.id,
                        'type': t.transaction_type,
                        'quantity': t.quantity,
                        'user': t.user.get_full_name(),
                        'timestamp': t.created_at,
                        'notes': t.notes,
                        'reference': t.reference_number
                    } for t in transactions
                ],
                'logs': [
                    {
                        'id': l.id,
                        'status': l.status,
                        'patient': l.patient.get_full_name(),
                        'scheduled_time': l.scheduled_time,
                        'actual_time': l.actual_time,
                        'dosage_taken': l.dosage_taken,
                        'notes': l.notes
                    } for l in logs
                ],
                'alerts': [
                    {
                        'id': a.id,
                        'type': a.alert_type,
                        'priority': a.priority,
                        'status': a.status,
                        'created_by': a.created_by.get_full_name(),
                        'created_at': a.created_at,
                        'title': a.title,
                        'message': a.message
                    } for a in alerts
                ]
            }
            
            return Response(audit_data)
            
        except Exception as e:
            logger.error(f"Error getting audit trail for medication {pk}: {e}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MedicationScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing medication schedules.
    """
    
    serializer_class = MedicationScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['timing', 'status', 'medication', 'patient']
    search_fields = ['instructions', 'frequency']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']
    
    def get_queryset(self):
        """Filter schedules based on user type and permissions."""
        user = self.request.user
        if user.user_type == 'PATIENT':
            return MedicationSchedule.objects.filter(patient=user)
        elif user.user_type == 'CAREGIVER':
            # Caregivers can see schedules for patients they care for
            return MedicationSchedule.objects.filter(patient__caregiver=user)
        else:
            # Staff and admins can see all schedules
            return MedicationSchedule.objects.all()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return MedicationScheduleDetailSerializer
        return MedicationScheduleSerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active medication schedules."""
        schedules = self.get_queryset().filter(status=MedicationSchedule.Status.ACTIVE)
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get schedules that should be taken today with today's log status."""
        today = timezone.now().date()
        weekday = today.strftime('%A').lower()
        
        schedules = self.get_queryset().filter(
            Q(status=MedicationSchedule.Status.ACTIVE) &
            Q(start_date__lte=today) &
            (Q(end_date__isnull=True) | Q(end_date__gte=today))
        )
        
        # Filter by day of week
        if weekday == 'monday':
            schedules = schedules.filter(monday=True)
        elif weekday == 'tuesday':
            schedules = schedules.filter(tuesday=True)
        elif weekday == 'wednesday':
            schedules = schedules.filter(wednesday=True)
        elif weekday == 'thursday':
            schedules = schedules.filter(thursday=True)
        elif weekday == 'friday':
            schedules = schedules.filter(friday=True)
        elif weekday == 'saturday':
            schedules = schedules.filter(saturday=True)
        elif weekday == 'sunday':
            schedules = schedules.filter(sunday=True)
        
        # Get today's logs for these schedules
        from .models import MedicationLog
        today_logs = MedicationLog.objects.filter(
            patient=request.user,
            schedule__in=schedules,
            scheduled_time__date=today
        ).select_related('schedule')
        
        # Create a map of schedule_id to log status
        log_status_map = {}
        for log in today_logs:
            log_status_map[log.schedule.id] = log.status
        
        # Serialize schedules and add log status
        serializer = self.get_serializer(schedules, many=True)
        schedule_data = serializer.data
        
        # Add today's log status to each schedule
        for schedule in schedule_data:
            schedule_id = schedule['id']
            if schedule_id in log_status_map:
                schedule['today_log_status'] = log_status_map[schedule_id]
            else:
                schedule['today_log_status'] = None
        
        return Response(schedule_data)
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a medication schedule."""
        schedule = self.get_object()
        schedule.status = MedicationSchedule.Status.PAUSED
        schedule.save()
        serializer = self.get_serializer(schedule)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume a paused medication schedule."""
        schedule = self.get_object()
        schedule.status = MedicationSchedule.Status.ACTIVE
        schedule.save()
        serializer = self.get_serializer(schedule)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a medication schedule as completed."""
        schedule = self.get_object()
        schedule.status = MedicationSchedule.Status.COMPLETED
        schedule.save()
        serializer = self.get_serializer(schedule)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_taken(self, request, pk=None):
        """Mark a medication schedule as taken and update stock."""
        schedule = self.get_object()
        
        # Import required models
        from .models import MedicationLog, StockTransaction, StockAlert
        from django.utils import timezone
        from django.db import transaction
        
        # Get the scheduled time for today
        today = timezone.now().date()
        
        # Handle custom time or use default timing
        if schedule.custom_time:
            scheduled_time = timezone.make_aware(
                timezone.datetime.combine(today, schedule.custom_time)
            )
        else:
            # Use timing to create a reasonable time
            time_map = {
                'morning': time(8, 0),  # 8:00 AM
                'noon': time(12, 0),    # 12:00 PM
                'night': time(20, 0),   # 8:00 PM
            }
            default_time = time_map.get(schedule.timing, time(8, 0))
            scheduled_time = timezone.make_aware(
                timezone.datetime.combine(today, default_time)
            )
        
        # Use database transaction to ensure data consistency
        with transaction.atomic():
            # Check if we already have a log entry for this schedule today
            log, created = MedicationLog.objects.get_or_create(
                patient=request.user,
                medication=schedule.medication,
                schedule=schedule,
                scheduled_time=scheduled_time,
                defaults={
                    'status': MedicationLog.Status.TAKEN,
                    'actual_time': timezone.now(),
                    'dosage_taken': schedule.dosage_amount,
                    'notes': request.data.get('notes', '')
                }
            )
            
            if not created:
                # Update existing log
                log.status = MedicationLog.Status.TAKEN
                log.actual_time = timezone.now()
                log.dosage_taken = schedule.dosage_amount
                if 'notes' in request.data:
                    log.notes = request.data['notes']
                log.save()
            
            # Only create stock transaction if this is a new log entry or if the status changed
            if created or log.status == MedicationLog.Status.TAKEN:
                # Calculate dosage to deduct (convert Decimal to int for pill count)
                dosage_to_deduct = int(schedule.dosage_amount)
                
                # Check if we have enough stock
                if schedule.medication.pill_count < dosage_to_deduct:
                    return Response({
                        'error': 'Insufficient stock',
                        'message': f'Only {schedule.medication.pill_count} pills available, but {dosage_to_deduct} required',
                        'current_stock': schedule.medication.pill_count,
                        'required': dosage_to_deduct
                    }, status=400)
                
                # Create stock transaction for dose taken
                stock_transaction = StockTransaction.objects.create(
                    medication=schedule.medication,
                    user=request.user,
                    transaction_type=StockTransaction.TransactionType.DOSE_TAKEN,
                    quantity=-dosage_to_deduct,  # Negative for removal
                    notes=f"Dose taken for schedule {schedule.id} - {schedule.medication.name}",
                    reference_number=f"SCH_{schedule.id}_{today}",
                )
                
                # Check for low stock alerts after stock deduction
                medication = schedule.medication
                if medication.pill_count <= medication.low_stock_threshold:
                    # Create or update low stock alert
                    alert_type = StockAlert.AlertType.OUT_OF_STOCK if medication.pill_count == 0 else StockAlert.AlertType.LOW_STOCK
                    priority = StockAlert.Priority.CRITICAL if medication.pill_count == 0 else StockAlert.Priority.HIGH
                    
                    # Check if there's already an active alert for this medication
                    existing_alert = StockAlert.objects.filter(
                        medication=medication,
                        alert_type__in=[StockAlert.AlertType.LOW_STOCK, StockAlert.AlertType.OUT_OF_STOCK],
                        status=StockAlert.Status.ACTIVE
                    ).first()
                    
                    if not existing_alert:
                        StockAlert.objects.create(
                            medication=medication,
                            created_by=request.user,
                            alert_type=alert_type,
                            priority=priority,
                            title=f"{alert_type.replace('_', ' ').title()} Alert - {medication.name}",
                            message=f"{medication.name} stock is now at {medication.pill_count} units. Threshold is {medication.low_stock_threshold}.",
                            current_stock=medication.pill_count,
                            threshold_level=medication.low_stock_threshold
                        )
        
        serializer = self.get_serializer(schedule)
        return Response({
            'message': 'Medication marked as taken successfully',
            'schedule': serializer.data,
            'stock_deducted': int(schedule.dosage_amount),
            'remaining_stock': schedule.medication.pill_count,
            'low_stock_alert': schedule.medication.pill_count <= schedule.medication.low_stock_threshold
        })

    @action(detail=True, methods=['post'])
    def mark_missed(self, request, pk=None):
        """Mark a medication schedule as missed."""
        schedule = self.get_object()
        
        # Create a medication log entry
        from .models import MedicationLog
        from django.utils import timezone
        
        # Get the scheduled time for today
        today = timezone.now().date()
        
        # Handle custom time or use default timing
        if schedule.custom_time:
            scheduled_time = timezone.make_aware(
                timezone.datetime.combine(today, schedule.custom_time)
            )
        else:
            # Use timing to create a reasonable time
            time_map = {
                'morning': time(8, 0),  # 8:00 AM
                'noon': time(12, 0),    # 12:00 PM
                'night': time(20, 0),   # 8:00 PM
            }
            default_time = time_map.get(schedule.timing, time(8, 0))
            scheduled_time = timezone.make_aware(
                timezone.datetime.combine(today, default_time)
            )
        
        # Create or update the log entry
        log, created = MedicationLog.objects.get_or_create(
            patient=request.user,
            medication=schedule.medication,
            schedule=schedule,
            scheduled_time=scheduled_time,
            defaults={
                'status': MedicationLog.Status.MISSED,
                'dosage_taken': 0,
                'notes': request.data.get('notes', '')
            }
        )
        
        if not created:
            # Update existing log
            log.status = MedicationLog.Status.MISSED
            log.dosage_taken = 0
            if 'notes' in request.data:
                log.notes = request.data['notes']
            log.save()
        
        serializer = self.get_serializer(schedule)
        return Response(serializer.data)


class MedicationLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing medication logs.
    """
    
    serializer_class = MedicationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'medication', 'patient', 'schedule']
    search_fields = ['notes', 'side_effects']
    ordering_fields = ['scheduled_time', 'actual_time', 'created_at']
    ordering = ['-scheduled_time']
    
    def get_queryset(self):
        """Filter logs based on user type and permissions."""
        user = self.request.user
        if user.user_type == 'PATIENT':
            return MedicationLog.objects.filter(patient=user)
        elif user.user_type == 'CAREGIVER':
            return MedicationLog.objects.filter(patient__caregiver=user)
        else:
            return MedicationLog.objects.all()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return MedicationLogDetailSerializer
        return MedicationLogSerializer
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get logs for today."""
        today = timezone.now().date()
        logs = self.get_queryset().filter(
            scheduled_time__date=today
        )
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def missed(self, request):
        """Get missed medication logs."""
        logs = self.get_queryset().filter(status=MedicationLog.Status.MISSED)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def adherence_stats(self, request):
        """Get medication adherence statistics."""
        user = request.user
        if user.user_type == user.UserType.PATIENT:
            logs = self.get_queryset().filter(patient=user)
        elif user.user_type == user.UserType.CAREGIVER:
            logs = self.get_queryset().filter(patient__caregiver=user)
        else:
            logs = self.get_queryset()
        
        # Calculate adherence statistics
        total_logs = logs.count()
        taken_logs = logs.filter(status=MedicationLog.Status.TAKEN).count()
        missed_logs = logs.filter(status=MedicationLog.Status.MISSED).count()
        
        adherence_rate = (taken_logs / total_logs * 100) if total_logs > 0 else 0
        
        stats = {
            'total_logs': total_logs,
            'taken_logs': taken_logs,
            'missed_logs': missed_logs,
            'adherence_rate': round(adherence_rate, 2)
        }
        
        return Response(stats)


class StockAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing stock alerts.
    """
    
    queryset = StockAlert.objects.all()
    serializer_class = StockAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['alert_type', 'priority', 'status', 'medication']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return StockAlertDetailSerializer
        return StockAlertSerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active alerts."""
        alerts = self.get_queryset().filter(status=StockAlert.Status.ACTIVE)
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def critical(self, request):
        """Get critical priority alerts."""
        alerts = self.get_queryset().filter(
            priority=StockAlert.Priority.CRITICAL,
            status=StockAlert.Status.ACTIVE
        )
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert."""
        alert = self.get_object()
        alert.acknowledge(request.user)
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert."""
        alert = self.get_object()
        notes = request.data.get('notes', '')
        alert.resolve(notes)
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Dismiss an alert."""
        alert = self.get_object()
        alert.dismiss()
        serializer = self.get_serializer(alert)
        return Response(serializer.data)


class PharmacyIntegrationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing pharmacy integrations.
    """
    queryset = PharmacyIntegration.objects.all()
    serializer_class = PharmacyIntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter integrations based on user permissions."""
        if self.request.user.is_staff:
            return PharmacyIntegration.objects.all()
        return PharmacyIntegration.objects.filter(status='active')
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """
        Test the connection to a pharmacy integration.
        """
        try:
            integration = self.get_object()
            service = IntelligentStockService()
            
            # Test the integration
            success = service.integrate_with_pharmacy(None, integration)
            
            if success:
                integration.status = 'active'
                integration.last_sync = timezone.now()
                integration.save()
                
                return Response({
                    'message': 'Connection test successful',
                    'status': 'active'
                })
            else:
                integration.status = 'error'
                integration.save()
                
                return Response({
                    'message': 'Connection test failed',
                    'status': 'error'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def sync_stock(self, request, pk=None):
        """
        Sync stock levels with pharmacy integration.
        """
        try:
            integration = self.get_object()
            medication_ids = request.data.get('medication_ids', [])
            
            service = IntelligentStockService()
            synced_count = 0
            
            if medication_ids:
                medications = Medication.objects.filter(id__in=medication_ids)
            else:
                medications = Medication.objects.all()
            
            for medication in medications:
                try:
                    success = service.integrate_with_pharmacy(medication, integration)
                    if success:
                        synced_count += 1
                except Exception as e:
                    logger.error(f"Failed to sync medication {medication.id}: {e}")
                    continue
            
            integration.last_sync = timezone.now()
            integration.save()
            
            return Response({
                'message': f'Successfully synced {synced_count} medications',
                'synced_count': synced_count,
                'total_count': len(medications)
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StockAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for stock analytics data.
    """
    queryset = StockAnalytics.objects.all()
    serializer_class = StockAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Get dashboard analytics summary.
        """
        try:
            analytics_service = StockAnalyticsService()
            
            # Get date range from query params
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            if 'start_date' in request.query_params:
                start_date = datetime.strptime(
                    request.query_params['start_date'], '%Y-%m-%d'
                ).date()
            
            if 'end_date' in request.query_params:
                end_date = datetime.strptime(
                    request.query_params['end_date'], '%Y-%m-%d'
                ).date()
            
            # Generate comprehensive report
            report = analytics_service.generate_stock_report(
                start_date, end_date
            )
            
            return Response(report)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def low_stock_alerts(self, request):
        """
        Get medications with low stock alerts.
        """
        try:
            medications = Medication.objects.filter(
                pill_count__lte=F('low_stock_threshold')
            ).select_related('stock_analytics')
            
            data = []
            for medication in medications:
                analytics = getattr(medication, 'stock_analytics', None)
                data.append({
                    'medication': MedicationSerializer(medication).data,
                    'analytics': StockAnalyticsSerializer(analytics).data if analytics else None,
                    'days_until_stockout': analytics.days_until_stockout if analytics else None
                })
            
            return Response(data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """
        Get medications expiring soon.
        """
        try:
            days_threshold = int(request.query_params.get('days', 30))
            threshold_date = date.today() + timedelta(days=days_threshold)
            
            medications = Medication.objects.filter(
                expiration_date__lte=threshold_date,
                expiration_date__gte=date.today()
            ).order_by('expiration_date')
            
            serializer = MedicationSerializer(medications, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Legacy views for backward compatibility
def test_i18n(request):
    """Test internationalization functionality."""
    return render(request, 'medications/test_i18n.html')

@csrf_exempt
def set_language_ajax(request):
    """Set language via AJAX."""
    if request.method == 'POST':
        language = request.POST.get('language')
        if language:
            request.session['django_language'] = language
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

from django.shortcuts import render
from django.utils.translation import activate, gettext as _
from django.http import JsonResponse

def working_i18n_test(request):
    """Working i18n test view."""
    
    # Test translations
    activate('af-ZA')
    
    translations = {
        'Medications': _('Medications'),
        'Medication Schedules': _('Medication Schedules'),
        'Medication Logs': _('Medication Logs'),
        'Stock Alerts': _('Stock Alerts'),
        'Language': _('Language'),
        'Current': _('Current')
    }
    
    context = {
        'translations': translations,
        'current_language': 'af-ZA',
        'test_strings': [
            'Medications',
            'Medication Schedules', 
            'Medication Logs',
            'Stock Alerts',
            'Language',
            'Current'
        ]
    }
    
    return render(request, 'medications/working_i18n_test.html', context)

def api_i18n_test(request):
    """API endpoint for i18n testing."""
    activate('af-ZA')
    
    translations = {
        'Medications': _('Medications'),
        'Medication Schedules': _('Medication Schedules'),
        'Medication Logs': _('Medication Logs'),
        'Stock Alerts': _('Stock Alerts'),
        'Language': _('Language'),
        'Current': _('Current')
    }
    
    return JsonResponse({
        'success': True,
        'language': 'af-ZA',
        'translations': translations
    })

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def test_cors(request):
    """
    Test endpoint to verify CORS configuration is working
    """
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Security-Level, X-Client-Version, X-Request-Timestamp'
        return response
    
    # Return test data
    return Response({
        'message': 'CORS test successful',
        'method': request.method,
        'headers': dict(request.headers),
        'timestamp': timezone.now().isoformat()
    })

@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([AllowAny])
def test_medication_auth(request):
    """
    Test endpoint to verify medication authentication and debug 405 errors
    """
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Security-Level, X-Client-Version, X-Request-Timestamp'
        return response
    
    # Return authentication and request information
    return Response({
        'message': 'Medication auth test successful',
        'method': request.method,
        'user': {
            'authenticated': request.user.is_authenticated,
            'username': request.user.username if request.user.is_authenticated else None,
            'user_type': getattr(request.user, 'user_type', None) if request.user.is_authenticated else None,
        },
        'headers': dict(request.headers),
        'timestamp': timezone.now().isoformat()
    })
