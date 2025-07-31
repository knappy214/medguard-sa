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

logger = logging.getLogger(__name__)

from .models import (
    Medication, MedicationSchedule, MedicationLog, StockAlert, 
    StockAnalytics, PharmacyIntegration, StockTransaction,
    PrescriptionRenewal, StockVisualization
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
    PharmacyIntegrationSerializer
)
from .services import IntelligentStockService, StockAnalyticsService, MedicationCacheService


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
