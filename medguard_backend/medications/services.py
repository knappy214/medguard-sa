"""
Intelligent Stock Management Service

This module provides advanced stock management capabilities including:
- Predictive stock depletion calculations
- Usage pattern analysis
- Automated stock operations
- Integration with pharmacy systems
- Real-time monitoring and alerts
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
import logging
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum, Avg, Count, F
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from PIL import Image, ImageOps
import io
import os
from celery import shared_task

from .models import (
    Medication, StockTransaction, StockAnalytics, PharmacyIntegration,
    PrescriptionRenewal, StockVisualization, MedicationLog, MedicationSchedule
)
from medguard_notifications.services import NotificationService

User = get_user_model()
logger = logging.getLogger(__name__)


class IntelligentStockService:
    """
    Intelligent stock management service with predictive analytics.
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def record_dose_taken(self, patient: User, medication: Medication, 
                         dosage_amount: Decimal, schedule: Optional[MedicationSchedule] = None,
                         notes: str = "") -> StockTransaction:
        """
        Record when a dose is taken and automatically decrement stock.
        
        Args:
            patient: The patient who took the dose
            medication: The medication taken
            dosage_amount: Amount of medication taken
            schedule: Optional medication schedule
            notes: Additional notes
            
        Returns:
            StockTransaction: The created transaction record
        """
        try:
            with transaction.atomic():
                # Create stock transaction for dose taken
                transaction_record = StockTransaction.objects.create(
                    medication=medication,
                    user=patient,
                    transaction_type=StockTransaction.TransactionType.DOSE_TAKEN,
                    quantity=-int(dosage_amount),  # Negative for removal
                    notes=f"Dose taken by {patient.get_full_name()}. {notes}".strip(),
                    reference_number=f"DOSE_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                )
                
                # Create medication log entry
                MedicationLog.objects.create(
                    patient=patient,
                    medication=medication,
                    schedule=schedule,
                    scheduled_time=timezone.now(),
                    actual_time=timezone.now(),
                    status=MedicationLog.Status.TAKEN,
                    dosage_taken=dosage_amount,
                    notes=notes
                )
                
                # Update analytics
                self.update_stock_analytics(medication)
                
                # Check for low stock and send alerts
                if medication.is_low_stock:
                    self._send_low_stock_alert(medication)
                
                logger.info(f"Dose taken recorded: {medication.name} - {dosage_amount} by {patient.username}")
                return transaction_record
                
        except Exception as e:
            logger.error(f"Error recording dose taken: {e}")
            raise
    
    def predict_stock_depletion(self, medication: Medication, 
                               days_ahead: int = 90) -> Dict[str, Any]:
        """
        Predict stock depletion using time series analysis.
        
        Args:
            medication: The medication to analyze
            days_ahead: Number of days to predict ahead
            
        Returns:
            Dict containing prediction results
        """
        try:
            # Get historical transaction data
            transactions = self._get_historical_transactions(medication, days=90)
            
            if len(transactions) < 7:  # Need at least a week of data
                return self._get_basic_prediction(medication, days_ahead)
            
            # Convert to pandas DataFrame for analysis
            df = pd.DataFrame(transactions)
            df['date'] = pd.to_datetime(df['created_at']).dt.date
            df = df.groupby('date')['quantity'].sum().reset_index()
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            
            # Resample to daily frequency and fill missing values
            df_daily = df.resample('D').sum().fillna(0)
            
            # Calculate usage patterns
            daily_usage = abs(df_daily['quantity'].mean())
            usage_std = df_daily['quantity'].std()
            
            # Calculate seasonal patterns (weekly)
            df_daily['day_of_week'] = df_daily.index.dayofweek
            weekly_pattern = df_daily.groupby('day_of_week')['quantity'].mean()
            
            # Predict future usage
            current_stock = medication.pill_count
            days_until_stockout = int(current_stock / daily_usage) if daily_usage > 0 else float('inf')
            
            # Calculate confidence interval
            confidence = self._calculate_prediction_confidence(df_daily, daily_usage)
            
            # Generate prediction dates
            predicted_stockout_date = timezone.now().date() + timedelta(days=days_until_stockout)
            
            # Calculate recommended order quantity
            safety_stock = max(7 * daily_usage, medication.low_stock_threshold)
            recommended_quantity = int(safety_stock * 1.5)  # 50% buffer
            
            # Calculate recommended order date
            lead_time_days = 3  # Default lead time
            order_date = predicted_stockout_date - timedelta(days=lead_time_days)
            
            return {
                'current_stock': current_stock,
                'daily_usage_rate': daily_usage,
                'usage_volatility': usage_std,
                'days_until_stockout': days_until_stockout,
                'predicted_stockout_date': predicted_stockout_date,
                'recommended_order_quantity': recommended_quantity,
                'recommended_order_date': order_date,
                'confidence_level': confidence,
                'weekly_pattern': weekly_pattern.to_dict(),
                'data_points': len(df_daily),
                'prediction_method': 'time_series_analysis'
            }
            
        except Exception as e:
            logger.error(f"Error predicting stock depletion for {medication.name}: {e}")
            return self._get_basic_prediction(medication, days_ahead)
    
    def analyze_usage_patterns(self, medication: Medication, 
                              days: int = 90) -> Dict[str, Any]:
        """
        Analyze historical usage patterns for a medication.
        
        Args:
            medication: The medication to analyze
            days: Number of days to analyze
            
        Returns:
            Dict containing usage pattern analysis
        """
        try:
            transactions = self._get_historical_transactions(medication, days)
            
            if not transactions:
                return {'error': 'No transaction data available'}
            
            df = pd.DataFrame(transactions)
            df['date'] = pd.to_datetime(df['created_at'])
            df['day_of_week'] = df['date'].dt.dayofweek
            df['hour'] = df['date'].dt.hour
            df['month'] = df['date'].dt.month
            
            # Daily patterns
            daily_usage = abs(df.groupby(df['date'].dt.date)['quantity'].sum())
            
            # Weekly patterns
            weekly_usage = abs(df.groupby('day_of_week')['quantity'].sum())
            
            # Hourly patterns
            hourly_usage = abs(df.groupby('hour')['quantity'].sum())
            
            # Monthly patterns
            monthly_usage = abs(df.groupby('month')['quantity'].sum())
            
            # Statistical measures
            stats = {
                'mean_daily_usage': daily_usage.mean(),
                'median_daily_usage': daily_usage.median(),
                'std_daily_usage': daily_usage.std(),
                'min_daily_usage': daily_usage.min(),
                'max_daily_usage': daily_usage.max(),
                'total_transactions': len(df),
                'unique_days': len(daily_usage),
                'avg_transactions_per_day': len(df) / len(daily_usage) if len(daily_usage) > 0 else 0
            }
            
            return {
                'daily_pattern': daily_usage.to_dict(),
                'weekly_pattern': weekly_usage.to_dict(),
                'hourly_pattern': hourly_usage.to_dict(),
                'monthly_pattern': monthly_usage.to_dict(),
                'statistics': stats,
                'analysis_period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error analyzing usage patterns for {medication.name}: {e}")
            return {'error': str(e)}
    
    def update_stock_analytics(self, medication: Medication) -> StockAnalytics:
        """
        Update stock analytics for a medication.
        
        Args:
            medication: The medication to update analytics for
            
        Returns:
            StockAnalytics: Updated analytics object
        """
        try:
            # Get prediction data
            prediction = self.predict_stock_depletion(medication)
            
            # Get or create analytics object
            analytics, created = StockAnalytics.objects.get_or_create(
                medication=medication,
                defaults={
                    'daily_usage_rate': 0.0,
                    'weekly_usage_rate': 0.0,
                    'monthly_usage_rate': 0.0,
                    'calculation_window_days': 90
                }
            )
            
            # Update analytics with prediction data
            analytics.daily_usage_rate = prediction.get('daily_usage_rate', 0.0)
            analytics.weekly_usage_rate = prediction.get('daily_usage_rate', 0.0) * 7
            analytics.monthly_usage_rate = prediction.get('daily_usage_rate', 0.0) * 30
            analytics.days_until_stockout = prediction.get('days_until_stockout')
            analytics.predicted_stockout_date = prediction.get('predicted_stockout_date')
            analytics.recommended_order_quantity = prediction.get('recommended_order_quantity', 0)
            analytics.recommended_order_date = prediction.get('recommended_order_date')
            analytics.usage_volatility = prediction.get('usage_volatility', 0.0)
            analytics.stockout_confidence = prediction.get('confidence_level', 0.0)
            analytics.last_calculated = timezone.now()
            
            analytics.save()
            
            logger.info(f"Updated stock analytics for {medication.name}")
            return analytics
            
        except Exception as e:
            logger.error(f"Error updating stock analytics for {medication.name}: {e}")
            raise
    
    def generate_stock_visualization(self, medication: Medication, 
                                   chart_type: str = 'line',
                                   days: int = 30) -> StockVisualization:
        """
        Generate stock visualization data for charts.
        
        Args:
            medication: The medication to visualize
            chart_type: Type of chart to generate
            days: Number of days to include
            
        Returns:
            StockVisualization: Generated visualization object
        """
        try:
            # Get transaction data
            transactions = self._get_historical_transactions(medication, days)
            
            if not transactions:
                return None
            
            df = pd.DataFrame(transactions)
            df['date'] = pd.to_datetime(df['created_at'])
            df = df.sort_values('date')
            
            # Calculate cumulative stock levels
            df['cumulative_quantity'] = df['quantity'].cumsum()
            df['stock_level'] = medication.pill_count - df['cumulative_quantity']
            
            # Prepare chart data
            chart_data = {
                'labels': df['date'].dt.strftime('%Y-%m-%d').tolist(),
                'datasets': [{
                    'label': 'Stock Level',
                    'data': df['stock_level'].tolist(),
                    'borderColor': '#2563EB',
                    'backgroundColor': 'rgba(37, 99, 235, 0.1)',
                    'fill': True
                }]
            }
            
            # Chart options
            chart_options = {
                'responsive': True,
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': 'Stock Level'
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Date'
                        }
                    }
                },
                'plugins': {
                    'title': {
                        'display': True,
                        'text': f'Stock Level Trend - {medication.name}'
                    }
                }
            }
            
            # Create or update visualization
            visualization, created = StockVisualization.objects.get_or_create(
                medication=medication,
                chart_type=chart_type,
                defaults={
                    'title': f'Stock Level Trend - {medication.name}',
                    'description': f'Stock level trend over the last {days} days',
                    'start_date': timezone.now().date() - timedelta(days=days),
                    'end_date': timezone.now().date(),
                    'chart_data': chart_data,
                    'chart_options': chart_options
                }
            )
            
            if not created:
                visualization.chart_data = chart_data
                visualization.chart_options = chart_options
                visualization.last_generated = timezone.now()
                visualization.save()
            
            return visualization
            
        except Exception as e:
            logger.error(f"Error generating visualization for {medication.name}: {e}")
            return None
    
    def check_prescription_renewals(self) -> List[PrescriptionRenewal]:
        """
        Check for prescriptions that need renewal.
        
        Returns:
            List of prescriptions needing renewal
        """
        try:
            today = timezone.now().date()
            
            # Find prescriptions that need renewal
            renewals_needed = PrescriptionRenewal.objects.filter(
                status=PrescriptionRenewal.Status.ACTIVE,
                expiry_date__lte=today + timedelta(days=30),  # Expiring within 30 days
                expiry_date__gt=today  # Not yet expired
            ).order_by('expiry_date')
            
            # Send notifications for urgent renewals
            for renewal in renewals_needed:
                if renewal.days_until_expiry <= 7:
                    self._send_prescription_renewal_alert(renewal, priority='high')
                elif renewal.days_until_expiry <= 14:
                    self._send_prescription_renewal_alert(renewal, priority='medium')
                elif renewal.days_until_expiry <= 30:
                    self._send_prescription_renewal_alert(renewal, priority='low')
            
            return list(renewals_needed)
            
        except Exception as e:
            logger.error(f"Error checking prescription renewals: {e}")
            return []
    
    def integrate_with_pharmacy(self, medication: Medication, 
                              pharmacy_integration: PharmacyIntegration) -> bool:
        """
        Integrate with external pharmacy system for automated ordering.
        
        Args:
            medication: The medication to order
            pharmacy_integration: The pharmacy integration to use
            
        Returns:
            bool: Success status
        """
        try:
            # Check if auto-ordering is enabled
            if not pharmacy_integration.auto_order_enabled:
                logger.info(f"Auto-ordering not enabled for {pharmacy_integration.name}")
                return False
            
            # Get analytics
            analytics = medication.stock_analytics
            
            if not analytics or not analytics.is_order_needed:
                logger.info(f"No order needed for {medication.name}")
                return False
            
            # Prepare order data
            order_data = {
                'medication_name': medication.name,
                'quantity': analytics.recommended_order_quantity,
                'strength': medication.strength,
                'unit_price': self._get_estimated_unit_price(medication),
                'total_amount': analytics.recommended_order_quantity * self._get_estimated_unit_price(medication),
                'order_date': timezone.now().date(),
                'expected_delivery': analytics.recommended_order_date + timedelta(days=pharmacy_integration.order_lead_time_days)
            }
            
            # Send order based on integration type
            if pharmacy_integration.integration_type == PharmacyIntegration.IntegrationType.API:
                success = self._send_api_order(pharmacy_integration, order_data)
            elif pharmacy_integration.integration_type == PharmacyIntegration.IntegrationType.WEBHOOK:
                success = self._send_webhook_order(pharmacy_integration, order_data)
            else:
                success = self._create_manual_order(pharmacy_integration, order_data)
            
            if success:
                # Update integration status
                pharmacy_integration.last_sync = timezone.now()
                pharmacy_integration.save()
                
                # Send notification
                self._send_order_confirmation(medication, order_data)
                
                logger.info(f"Successfully placed order for {medication.name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error integrating with pharmacy for {medication.name}: {e}")
            return False
    
    def _get_historical_transactions(self, medication: Medication, days: int) -> List[Dict]:
        """Get historical transaction data for analysis."""
        start_date = timezone.now() - timedelta(days=days)
        
        transactions = StockTransaction.objects.filter(
            medication=medication,
            created_at__gte=start_date
        ).values('quantity', 'created_at', 'transaction_type')
        
        return list(transactions)
    
    def _get_basic_prediction(self, medication: Medication, days_ahead: int) -> Dict[str, Any]:
        """Get basic prediction when insufficient data is available."""
        current_stock = medication.pill_count
        estimated_daily_usage = 1.0  # Default estimate
        
        days_until_stockout = int(current_stock / estimated_daily_usage) if estimated_daily_usage > 0 else float('inf')
        predicted_stockout_date = timezone.now().date() + timedelta(days=days_until_stockout)
        
        return {
            'current_stock': current_stock,
            'daily_usage_rate': estimated_daily_usage,
            'usage_volatility': 0.0,
            'days_until_stockout': days_until_stockout,
            'predicted_stockout_date': predicted_stockout_date,
            'recommended_order_quantity': medication.low_stock_threshold * 2,
            'recommended_order_date': predicted_stockout_date - timedelta(days=7),
            'confidence_level': 0.3,  # Low confidence for basic prediction
            'prediction_method': 'basic_estimate'
        }
    
    def _calculate_prediction_confidence(self, df: pd.DataFrame, daily_usage: float) -> float:
        """Calculate confidence level for prediction."""
        if len(df) < 7:
            return 0.3
        
        # Calculate coefficient of variation
        cv = df['quantity'].std() / abs(df['quantity'].mean()) if df['quantity'].mean() != 0 else 1.0
        
        # Higher CV means lower confidence
        confidence = max(0.1, 1.0 - cv)
        
        # Adjust based on data points
        data_factor = min(1.0, len(df) / 30)  # More data = higher confidence
        
        return confidence * data_factor
    
    def _send_low_stock_alert(self, medication: Medication):
        """Send low stock alert notification."""
        try:
            self.notification_service.send_stock_alert(
                medication=medication,
                alert_type='low_stock',
                priority='medium',
                title=f"Low Stock Alert - {medication.name}",
                message=f"Stock level for {medication.name} is low ({medication.pill_count} units remaining)."
            )
        except Exception as e:
            logger.error(f"Error sending low stock alert: {e}")
    
    def _send_prescription_renewal_alert(self, renewal: PrescriptionRenewal, priority: str = 'medium'):
        """Send prescription renewal alert."""
        try:
            self.notification_service.send_notification(
                user=renewal.patient,
                title=f"Prescription Renewal Required - {renewal.medication.name}",
                content=f"Your prescription for {renewal.medication.name} expires on {renewal.expiry_date}. Please contact your doctor for renewal.",
                notification_type='medication',
                priority=priority
            )
        except Exception as e:
            logger.error(f"Error sending prescription renewal alert: {e}")
    
    def _get_estimated_unit_price(self, medication: Medication) -> Decimal:
        """Get estimated unit price for medication."""
        # Get recent purchase transactions
        recent_purchases = StockTransaction.objects.filter(
            medication=medication,
            transaction_type=StockTransaction.TransactionType.PURCHASE,
            unit_price__isnull=False
        ).order_by('-created_at')[:5]
        
        if recent_purchases:
            avg_price = recent_purchases.aggregate(avg_price=Avg('unit_price'))['avg_price']
            return avg_price
        
        return Decimal('0.00')  # Default price
    
    def _send_api_order(self, pharmacy_integration: PharmacyIntegration, order_data: Dict) -> bool:
        """Send order via API."""
        # Implementation would depend on specific pharmacy API
        logger.info(f"API order sent to {pharmacy_integration.pharmacy_name}: {order_data}")
        return True
    
    def _send_webhook_order(self, pharmacy_integration: PharmacyIntegration, order_data: Dict) -> bool:
        """Send order via webhook."""
        # Implementation would depend on specific webhook format
        logger.info(f"Webhook order sent to {pharmacy_integration.pharmacy_name}: {order_data}")
        return True
    
    def _create_manual_order(self, pharmacy_integration: PharmacyIntegration, order_data: Dict) -> bool:
        """Create manual order record."""
        # Create a transaction record for the order
        StockTransaction.objects.create(
            medication=order_data['medication'],
            user=User.objects.filter(is_staff=True).first(),  # Staff user
            transaction_type=StockTransaction.TransactionType.PURCHASE,
            quantity=order_data['quantity'],
            unit_price=order_data['unit_price'],
            total_amount=order_data['total_amount'],
            notes=f"Manual order via {pharmacy_integration.pharmacy_name}",
            reference_number=f"ORDER_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        )
        return True
    
    def _send_order_confirmation(self, medication: Medication, order_data: Dict):
        """Send order confirmation notification."""
        try:
            self.notification_service.send_notification(
                title=f"Order Placed - {medication.name}",
                content=f"Order placed for {order_data['quantity']} units of {medication.name}. Expected delivery: {order_data['expected_delivery']}.",
                notification_type='stock',
                priority='medium'
            )
        except Exception as e:
            logger.error(f"Error sending order confirmation: {e}")


class StockAnalyticsService:
    """
    Service for advanced stock analytics and reporting.
    """
    
    def __init__(self):
        self.stock_service = IntelligentStockService()
    
    def generate_stock_report(self, start_date: date, end_date: date, 
                            medications: Optional[List[Medication]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive stock report.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            medications: List of medications to include (None for all)
            
        Returns:
            Dict containing report data
        """
        try:
            if medications is None:
                medications = Medication.objects.all()
            
            report_data = {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'days': (end_date - start_date).days
                },
                'summary': {},
                'medications': [],
                'alerts': [],
                'recommendations': []
            }
            
            total_transactions = 0
            total_value = Decimal('0.00')
            
            for medication in medications:
                # Get medication data
                medication_data = self._get_medication_report_data(medication, start_date, end_date)
                report_data['medications'].append(medication_data)
                
                total_transactions += medication_data['total_transactions']
                total_value += medication_data['total_value']
                
                # Check for alerts
                if medication_data['is_low_stock']:
                    report_data['alerts'].append({
                        'type': 'low_stock',
                        'medication': medication.name,
                        'current_stock': medication.pill_count,
                        'threshold': medication.low_stock_threshold
                    })
                
                if medication_data['is_expiring_soon']:
                    report_data['alerts'].append({
                        'type': 'expiring_soon',
                        'medication': medication.name,
                        'expiry_date': medication.expiration_date
                    })
            
            # Summary statistics
            report_data['summary'] = {
                'total_medications': len(medications),
                'total_transactions': total_transactions,
                'total_value': total_value,
                'low_stock_count': len([m for m in medications if m.is_low_stock]),
                'expiring_soon_count': len([m for m in medications if m.is_expiring_soon])
            }
            
            # Generate recommendations
            report_data['recommendations'] = self._generate_recommendations(report_data)
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating stock report: {e}")
            return {'error': str(e)}
    
    def _get_medication_report_data(self, medication: Medication, 
                                  start_date: date, end_date: date) -> Dict[str, Any]:
        """Get report data for a specific medication."""
        transactions = StockTransaction.objects.filter(
            medication=medication,
            created_at__date__range=[start_date, end_date]
        )
        
        # Calculate metrics
        total_quantity = transactions.aggregate(total=Sum('quantity'))['total'] or 0
        total_value = transactions.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Usage by type
        usage_by_type = {}
        for transaction_type, _ in StockTransaction.TransactionType.choices:
            type_transactions = transactions.filter(transaction_type=transaction_type)
            usage_by_type[transaction_type] = {
                'count': type_transactions.count(),
                'quantity': type_transactions.aggregate(total=Sum('quantity'))['total'] or 0,
                'value': type_transactions.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            }
        
        return {
            'id': medication.id,
            'name': medication.name,
            'current_stock': medication.pill_count,
            'low_stock_threshold': medication.low_stock_threshold,
            'is_low_stock': medication.is_low_stock,
            'is_expiring_soon': medication.is_expiring_soon,
            'expiration_date': medication.expiration_date,
            'total_transactions': transactions.count(),
            'total_quantity': total_quantity,
            'total_value': total_value,
            'usage_by_type': usage_by_type,
            'analytics': self._get_analytics_summary(medication)
        }
    
    def _get_analytics_summary(self, medication: Medication) -> Dict[str, Any]:
        """Get analytics summary for medication."""
        analytics = getattr(medication, 'stock_analytics', None)
        
        if not analytics:
            return {}
        
        return {
            'daily_usage_rate': analytics.daily_usage_rate,
            'days_until_stockout': analytics.days_until_stockout,
            'predicted_stockout_date': analytics.predicted_stockout_date,
            'recommended_order_quantity': analytics.recommended_order_quantity,
            'recommended_order_date': analytics.recommended_order_date,
            'confidence_level': analytics.stockout_confidence
        }
    
    def _generate_recommendations(self, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on report data."""
        recommendations = []
        
        # Low stock recommendations
        low_stock_alerts = [alert for alert in report_data['alerts'] if alert['type'] == 'low_stock']
        if low_stock_alerts:
            recommendations.append({
                'type': 'order_medications',
                'priority': 'high',
                'title': 'Order Low Stock Medications',
                'description': f"Order {len(low_stock_alerts)} medications that are low in stock",
                'medications': [alert['medication'] for alert in low_stock_alerts]
            })
        
        # Expiring medications
        expiring_alerts = [alert for alert in report_data['alerts'] if alert['type'] == 'expiring_soon']
        if expiring_alerts:
            recommendations.append({
                'type': 'check_expiring_medications',
                'priority': 'medium',
                'title': 'Check Expiring Medications',
                'description': f"Review {len(expiring_alerts)} medications that are expiring soon",
                'medications': [alert['medication'] for alert in expiring_alerts]
            })
        
        # Usage pattern recommendations
        if report_data['summary']['total_transactions'] > 0:
            recommendations.append({
                'type': 'review_usage_patterns',
                'priority': 'low',
                'title': 'Review Usage Patterns',
                'description': 'Analyze usage patterns to optimize stock levels',
                'action': 'run_usage_analysis'
            })
        
        return recommendations 


class ImageOptimizationService:
    """
    Service for optimizing medication images.
    
    Provides methods for:
    - Creating thumbnails
    - Converting to WebP format
    - Compressing images
    - Generating alt text
    """
    
    THUMBNAIL_SIZE = (150, 150)
    WEBP_QUALITY = 85
    MAX_IMAGE_SIZE = (800, 800)
    
    @classmethod
    def optimize_medication_image(cls, medication):
        """
        Optimize medication image by creating thumbnails and WebP versions.
        
        Args:
            medication: Medication instance with image
        """
        if not medication.medication_image:
            return False
            
        try:
            # Update processing status
            medication.image_processing_status = 'processing'
            medication.save(update_fields=['image_processing_status'])
            
            # Open original image
            with Image.open(medication.medication_image.path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                thumbnail = cls._create_thumbnail(img)
                if thumbnail:
                    # Save thumbnail
                    thumbnail_path = f'medications/thumbnails/{os.path.basename(medication.medication_image.name)}'
                    thumbnail.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
                    medication.medication_image_thumbnail = thumbnail_path
                
                # Create WebP version
                webp_path = f'medications/webp/{os.path.splitext(os.path.basename(medication.medication_image.name))[0]}.webp'
                img.save(webp_path, 'WEBP', quality=cls.WEBP_QUALITY, optimize=True)
                medication.medication_image_webp = webp_path
                
                # Generate alt text if not provided
                if not medication.image_alt_text:
                    medication.image_alt_text = cls._generate_alt_text(medication)
                
                # Update status
                medication.image_processing_status = 'completed'
                medication.save()
                
                logger.info(f"Successfully optimized image for medication {medication.id}")
                return True
                
        except Exception as e:
            logger.error(f"Error optimizing image for medication {medication.id}: {str(e)}")
            medication.image_processing_status = 'failed'
            medication.save(update_fields=['image_processing_status'])
            return False
    
    @classmethod
    def _create_thumbnail(cls, img):
        """Create a thumbnail from the original image."""
        try:
            # Resize while maintaining aspect ratio
            img.thumbnail(cls.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            return img
        except Exception as e:
            logger.error(f"Error creating thumbnail: {str(e)}")
            return None
    
    @classmethod
    def _generate_alt_text(cls, medication):
        """Generate alt text for medication image."""
        return f"Image of {medication.name} {medication.strength} {medication.medication_type}"


class MedicationCacheService:
    """
    Service for caching medication data efficiently.
    """
    
    CACHE_TIMEOUT = 1800  # 30 minutes
    CACHE_PREFIX = 'medication'
    
    @classmethod
    def get_medication_list(cls, filters: Dict[str, Any] = None) -> List[Dict]:
        """
        Get cached medication list with optional filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            List of medication dictionaries
        """
        cache_key = cls._get_cache_key('list', filters)
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            from .models import Medication
            queryset = Medication.objects.all()
            
            if filters:
                queryset = cls._apply_filters(queryset, filters)
            
            cached_data = list(queryset.values())
            cache.set(cache_key, cached_data, cls.CACHE_TIMEOUT)
        
        return cached_data
    
    @classmethod
    def get_medication_detail(cls, medication_id: int) -> Optional[Dict]:
        """
        Get cached medication detail.
        
        Args:
            medication_id: Medication ID
            
        Returns:
            Medication dictionary or None
        """
        cache_key = cls._get_cache_key('detail', medication_id)
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            from .models import Medication
            try:
                medication = Medication.objects.get(id=medication_id)
                cached_data = {
                    'id': medication.id,
                    'name': medication.name,
                    'generic_name': medication.generic_name,
                    'brand_name': medication.brand_name,
                    'medication_type': medication.medication_type,
                    'prescription_type': medication.prescription_type,
                    'strength': medication.strength,
                    'dosage_unit': medication.dosage_unit,
                    'pill_count': medication.pill_count,
                    'low_stock_threshold': medication.low_stock_threshold,
                    'manufacturer': medication.manufacturer,
                    'description': medication.description,
                    'active_ingredients': medication.active_ingredients,
                    'side_effects': medication.side_effects,
                    'contraindications': medication.contraindications,
                    'storage_instructions': medication.storage_instructions,
                    'expiration_date': medication.expiration_date.isoformat() if medication.expiration_date else None,
                    'is_low_stock': medication.is_low_stock,
                    'is_expired': medication.is_expired,
                    'is_expiring_soon': medication.is_expiring_soon,
                    'image_url': medication.medication_image.url if medication.medication_image else None,
                    'thumbnail_url': medication.medication_image_thumbnail.url if medication.medication_image_thumbnail else None,
                    'webp_url': medication.medication_image_webp.url if medication.medication_image_webp else None,
                    'image_alt_text': medication.image_alt_text,
                    'created_at': medication.created_at.isoformat(),
                    'updated_at': medication.updated_at.isoformat(),
                }
                cache.set(cache_key, cached_data, cls.CACHE_TIMEOUT)
            except Medication.DoesNotExist:
                return None
        
        return cached_data
    
    @classmethod
    def invalidate_medication_cache(cls, medication_id: int = None):
        """
        Invalidate medication cache.
        
        Args:
            medication_id: Specific medication ID or None for all
        """
        if medication_id:
            # Invalidate specific medication
            cache.delete(cls._get_cache_key('detail', medication_id))
        else:
            # Invalidate all medication caches
            cache.delete_pattern(f"{cls.CACHE_PREFIX}:*")
    
    @classmethod
    def _get_cache_key(cls, key_type: str, identifier: Any) -> str:
        """Generate cache key."""
        return f"{cls.CACHE_PREFIX}:{key_type}:{identifier}"
    
    @classmethod
    def _apply_filters(cls, queryset, filters: Dict[str, Any]):
        """Apply filters to queryset."""
        if 'medication_type' in filters:
            queryset = queryset.filter(medication_type=filters['medication_type'])
        
        if 'prescription_type' in filters:
            queryset = queryset.filter(prescription_type=filters['prescription_type'])
        
        if 'manufacturer' in filters:
            queryset = queryset.filter(manufacturer__icontains=filters['manufacturer'])
        
        if 'search' in filters:
            queryset = queryset.filter(
                Q(name__icontains=filters['search']) |
                Q(generic_name__icontains=filters['search']) |
                Q(description__icontains=filters['search'])
            )
        
        if 'low_stock' in filters and filters['low_stock']:
            queryset = queryset.filter(pill_count__lte=F('low_stock_threshold'))
        
        if 'expiring_soon' in filters and filters['expiring_soon']:
            thirty_days_from_now = timezone.now().date() + timedelta(days=30)
            queryset = queryset.filter(
                expiration_date__lte=thirty_days_from_now,
                expiration_date__gte=timezone.now().date()
            )
        
        return queryset


@shared_task
def optimize_medication_images():
    """
    Background task to optimize medication images.
    """
    from .models import Medication
    
    medications = Medication.objects.filter(
        medication_image__isnull=False,
        image_processing_status__in=['pending', 'failed']
    )
    
    for medication in medications:
        ImageOptimizationService.optimize_medication_image(medication)


@shared_task
def cleanup_old_medication_images():
    """
    Background task to cleanup old medication images.
    """
    from .models import Medication
    from django.core.files.storage import default_storage
    
    # Find medications with old images that need cleanup
    cutoff_date = timezone.now() - timedelta(days=30)
    old_medications = Medication.objects.filter(
        updated_at__lt=cutoff_date,
        medication_image__isnull=False
    )
    
    for medication in old_medications:
        # Cleanup old image files
        if medication.medication_image:
            try:
                default_storage.delete(medication.medication_image.path)
            except Exception as e:
                logger.error(f"Error deleting old image for medication {medication.id}: {str(e)}")
        
        if medication.medication_image_thumbnail:
            try:
                default_storage.delete(medication.medication_image_thumbnail.path)
            except Exception as e:
                logger.error(f"Error deleting old thumbnail for medication {medication.id}: {str(e)}")
        
        if medication.medication_image_webp:
            try:
                default_storage.delete(medication.medication_image_webp.path)
            except Exception as e:
                logger.error(f"Error deleting old WebP for medication {medication.id}: {str(e)}") 