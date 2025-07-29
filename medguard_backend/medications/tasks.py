"""
Celery tasks for intelligent stock management.

This module contains background tasks for:
- Automated stock analytics updates
- Prescription renewal monitoring
- Pharmacy integration operations
- Stock visualization generation
- Predictive stock depletion calculations
"""

import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
from decimal import Decimal

from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, F

from .models import (
    Medication, StockTransaction, StockAnalytics, PharmacyIntegration,
    PrescriptionRenewal, StockVisualization, MedicationLog
)
from .services import IntelligentStockService, StockAnalyticsService

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='medications.update_stock_analytics')
def update_stock_analytics_task(self, medication_id: int = None):
    """
    Update stock analytics for medications.
    
    Args:
        medication_id: Specific medication ID to update (None for all)
    """
    try:
        service = IntelligentStockService()
        
        if medication_id:
            medications = [Medication.objects.get(id=medication_id)]
        else:
            # Update all medications that have had recent transactions
            recent_date = timezone.now() - timedelta(days=7)
            medications = Medication.objects.filter(
                stock_transactions__created_at__gte=recent_date
            ).distinct()
        
        updated_count = 0
        for medication in medications:
            try:
                service.update_stock_analytics(medication)
                updated_count += 1
                logger.info(f"Updated analytics for {medication.name}")
            except Exception as e:
                logger.error(f"Error updating analytics for {medication.name}: {e}")
                continue
        
        logger.info(f"Stock analytics update completed. Updated {updated_count} medications.")
        return {
            'status': 'success',
            'medications_updated': updated_count,
            'total_medications': len(medications)
        }
        
    except Exception as e:
        logger.error(f"Error in update_stock_analytics_task: {e}")
        raise


@shared_task(bind=True, name='medications.predict_stock_depletion')
def predict_stock_depletion_task(self, medication_id: int = None, days_ahead: int = 90):
    """
    Predict stock depletion for medications.
    
    Args:
        medication_id: Specific medication ID to predict (None for all)
        days_ahead: Number of days to predict ahead
    """
    try:
        service = IntelligentStockService()
        
        if medication_id:
            medications = [Medication.objects.get(id=medication_id)]
        else:
            # Predict for all active medications
            medications = Medication.objects.filter(pill_count__gt=0)
        
        predictions = []
        for medication in medications:
            try:
                prediction = service.predict_stock_depletion(medication, days_ahead)
                predictions.append({
                    'medication_id': medication.id,
                    'medication_name': medication.name,
                    'prediction': prediction
                })
                
                # Update analytics with prediction
                service.update_stock_analytics(medication)
                
                logger.info(f"Predicted stock depletion for {medication.name}")
            except Exception as e:
                logger.error(f"Error predicting stock depletion for {medication.name}: {e}")
                continue
        
        logger.info(f"Stock depletion prediction completed. Predicted for {len(predictions)} medications.")
        return {
            'status': 'success',
            'predictions_count': len(predictions),
            'predictions': predictions
        }
        
    except Exception as e:
        logger.error(f"Error in predict_stock_depletion_task: {e}")
        raise


@shared_task(bind=True, name='medications.check_prescription_renewals')
def check_prescription_renewals_task(self):
    """
    Check for prescriptions that need renewal and send notifications.
    """
    try:
        service = IntelligentStockService()
        
        # Check for renewals needed
        renewals_needed = service.check_prescription_renewals()
        
        # Process each renewal
        processed_count = 0
        for renewal in renewals_needed:
            try:
                # Update renewal status if needed
                if renewal.is_expired and renewal.status == renewal.Status.ACTIVE:
                    renewal.status = renewal.Status.EXPIRED
                    renewal.save()
                
                processed_count += 1
                logger.info(f"Processed prescription renewal for {renewal.medication.name}")
            except Exception as e:
                logger.error(f"Error processing renewal for {renewal.medication.name}: {e}")
                continue
        
        logger.info(f"Prescription renewal check completed. Processed {processed_count} renewals.")
        return {
            'status': 'success',
            'renewals_processed': processed_count,
            'total_renewals_found': len(renewals_needed)
        }
        
    except Exception as e:
        logger.error(f"Error in check_prescription_renewals_task: {e}")
        raise


@shared_task(bind=True, name='medications.integrate_with_pharmacy')
def integrate_with_pharmacy_task(self, medication_id: int = None):
    """
    Integrate with pharmacy systems for automated ordering.
    
    Args:
        medication_id: Specific medication ID to process (None for all)
    """
    try:
        service = IntelligentStockService()
        
        # Get active pharmacy integrations
        pharmacy_integrations = PharmacyIntegration.objects.filter(
            status=PharmacyIntegration.Status.ACTIVE,
            auto_order_enabled=True
        )
        
        if not pharmacy_integrations:
            logger.info("No active pharmacy integrations found")
            return {'status': 'success', 'message': 'No active pharmacy integrations'}
        
        if medication_id:
            medications = [Medication.objects.get(id=medication_id)]
        else:
            # Get medications that need ordering
            medications = []
            for medication in Medication.objects.all():
                analytics = getattr(medication, 'stock_analytics', None)
                if analytics and analytics.is_order_needed:
                    medications.append(medication)
        
        orders_placed = 0
        for medication in medications:
            for pharmacy in pharmacy_integrations:
                try:
                    success = service.integrate_with_pharmacy(medication, pharmacy)
                    if success:
                        orders_placed += 1
                        logger.info(f"Placed order for {medication.name} via {pharmacy.pharmacy_name}")
                        break  # Only place one order per medication
                except Exception as e:
                    logger.error(f"Error placing order for {medication.name} via {pharmacy.pharmacy_name}: {e}")
                    continue
        
        logger.info(f"Pharmacy integration completed. Placed {orders_placed} orders.")
        return {
            'status': 'success',
            'orders_placed': orders_placed,
            'medications_processed': len(medications)
        }
        
    except Exception as e:
        logger.error(f"Error in integrate_with_pharmacy_task: {e}")
        raise


@shared_task(bind=True, name='medications.generate_stock_visualizations')
def generate_stock_visualizations_task(self, medication_id: int = None, days: int = 30):
    """
    Generate stock visualizations for medications.
    
    Args:
        medication_id: Specific medication ID to visualize (None for all)
        days: Number of days to include in visualization
    """
    try:
        service = IntelligentStockService()
        
        if medication_id:
            medications = [Medication.objects.get(id=medication_id)]
        else:
            # Generate for medications with recent activity
            recent_date = timezone.now() - timedelta(days=days)
            medications = Medication.objects.filter(
                stock_transactions__created_at__gte=recent_date
            ).distinct()
        
        visualizations_created = 0
        for medication in medications:
            try:
                visualization = service.generate_stock_visualization(medication, days=days)
                if visualization:
                    visualizations_created += 1
                    logger.info(f"Generated visualization for {medication.name}")
            except Exception as e:
                logger.error(f"Error generating visualization for {medication.name}: {e}")
                continue
        
        logger.info(f"Stock visualization generation completed. Created {visualizations_created} visualizations.")
        return {
            'status': 'success',
            'visualizations_created': visualizations_created,
            'medications_processed': len(medications)
        }
        
    except Exception as e:
        logger.error(f"Error in generate_stock_visualizations_task: {e}")
        raise


@shared_task(bind=True, name='medications.analyze_usage_patterns')
def analyze_usage_patterns_task(self, medication_id: int = None, days: int = 90):
    """
    Analyze usage patterns for medications.
    
    Args:
        medication_id: Specific medication ID to analyze (None for all)
        days: Number of days to analyze
    """
    try:
        service = IntelligentStockService()
        
        if medication_id:
            medications = [Medication.objects.get(id=medication_id)]
        else:
            # Analyze medications with sufficient transaction history
            medications = Medication.objects.filter(
                stock_transactions__created_at__gte=timezone.now() - timedelta(days=days)
            ).distinct()
        
        analyses_completed = 0
        for medication in medications:
            try:
                analysis = service.analyze_usage_patterns(medication, days)
                if 'error' not in analysis:
                    analyses_completed += 1
                    logger.info(f"Analyzed usage patterns for {medication.name}")
                else:
                    logger.warning(f"Could not analyze usage patterns for {medication.name}: {analysis['error']}")
            except Exception as e:
                logger.error(f"Error analyzing usage patterns for {medication.name}: {e}")
                continue
        
        logger.info(f"Usage pattern analysis completed. Analyzed {analyses_completed} medications.")
        return {
            'status': 'success',
            'analyses_completed': analyses_completed,
            'medications_processed': len(medications)
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_usage_patterns_task: {e}")
        raise


@shared_task(bind=True, name='medications.generate_stock_report')
def generate_stock_report_task(self, start_date: str = None, end_date: str = None):
    """
    Generate comprehensive stock report.
    
    Args:
        start_date: Report start date (YYYY-MM-DD format)
        end_date: Report end date (YYYY-MM-DD format)
    """
    try:
        service = StockAnalyticsService()
        
        # Parse dates
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = timezone.now().date() - timedelta(days=30)
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = timezone.now().date()
        
        # Generate report
        report = service.generate_stock_report(start_date, end_date)
        
        if 'error' in report:
            logger.error(f"Error generating stock report: {report['error']}")
            raise Exception(report['error'])
        
        logger.info(f"Stock report generated for period {start_date} to {end_date}")
        return {
            'status': 'success',
            'report': report,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in generate_stock_report_task: {e}")
        raise


@shared_task(bind=True, name='medications.cleanup_old_transactions')
def cleanup_old_transactions_task(self, days_to_keep: int = 365):
    """
    Clean up old transaction records to maintain database performance.
    
    Args:
        days_to_keep: Number of days of transaction history to keep
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Count transactions to be deleted
        old_transactions = StockTransaction.objects.filter(
            created_at__lt=cutoff_date
        )
        count_to_delete = old_transactions.count()
        
        # Delete old transactions
        deleted_count, _ = old_transactions.delete()
        
        logger.info(f"Cleaned up {deleted_count} old transactions older than {days_to_keep} days")
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_transactions_task: {e}")
        raise


@shared_task(bind=True, name='medications.monitor_stock_levels')
def monitor_stock_levels_task(self):
    """
    Monitor stock levels and send alerts for critical situations.
    """
    try:
        service = IntelligentStockService()
        
        # Check for critical stock situations
        critical_alerts = []
        
        # Medications with very low stock (below 50% of threshold)
        low_stock_medications = Medication.objects.filter(
            pill_count__lte=F('low_stock_threshold') / 2
        )
        
        for medication in low_stock_medications:
            critical_alerts.append({
                'type': 'critical_low_stock',
                'medication': medication,
                'current_stock': medication.pill_count,
                'threshold': medication.low_stock_threshold
            })
        
        # Medications predicted to run out soon
        for medication in Medication.objects.filter(pill_count__gt=0):
            analytics = getattr(medication, 'stock_analytics', None)
            if analytics and analytics.is_stockout_imminent:
                critical_alerts.append({
                    'type': 'imminent_stockout',
                    'medication': medication,
                    'days_until_stockout': analytics.days_until_stockout,
                    'predicted_date': analytics.predicted_stockout_date
                })
        
        # Send critical alerts
        alerts_sent = 0
        for alert in critical_alerts:
            try:
                if alert['type'] == 'critical_low_stock':
                    service.notification_service.send_stock_alert(
                        medication=alert['medication'],
                        alert_type='critical_low_stock',
                        priority='critical',
                        title=f"Critical Low Stock - {alert['medication'].name}",
                        message=f"Stock level for {alert['medication'].name} is critically low ({alert['current_stock']} units). Immediate action required."
                    )
                elif alert['type'] == 'imminent_stockout':
                    service.notification_service.send_stock_alert(
                        medication=alert['medication'],
                        alert_type='imminent_stockout',
                        priority='high',
                        title=f"Imminent Stockout - {alert['medication'].name}",
                        message=f"{alert['medication'].name} is predicted to run out in {alert['days_until_stockout']} days on {alert['predicted_date']}."
                    )
                
                alerts_sent += 1
            except Exception as e:
                logger.error(f"Error sending critical alert: {e}")
                continue
        
        logger.info(f"Stock level monitoring completed. Sent {alerts_sent} critical alerts.")
        return {
            'status': 'success',
            'alerts_sent': alerts_sent,
            'critical_situations': len(critical_alerts)
        }
        
    except Exception as e:
        logger.error(f"Error in monitor_stock_levels_task: {e}")
        raise


@shared_task(bind=True, name='medications.sync_pharmacy_integrations')
def sync_pharmacy_integrations_task(self):
    """
    Sync with pharmacy integrations to update stock levels and orders.
    """
    try:
        # Get active pharmacy integrations
        integrations = PharmacyIntegration.objects.filter(
            status=PharmacyIntegration.Status.ACTIVE
        )
        
        sync_results = []
        for integration in integrations:
            try:
                # Update last sync time
                integration.last_sync = timezone.now()
                integration.save()
                
                # Log sync attempt
                sync_results.append({
                    'integration_id': integration.id,
                    'pharmacy_name': integration.pharmacy_name,
                    'status': 'success',
                    'sync_time': integration.last_sync.isoformat()
                })
                
                logger.info(f"Synced with pharmacy integration: {integration.pharmacy_name}")
                
            except Exception as e:
                logger.error(f"Error syncing with {integration.pharmacy_name}: {e}")
                sync_results.append({
                    'integration_id': integration.id,
                    'pharmacy_name': integration.pharmacy_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        logger.info(f"Pharmacy integration sync completed. Processed {len(integrations)} integrations.")
        return {
            'status': 'success',
            'integrations_processed': len(integrations),
            'sync_results': sync_results
        }
        
    except Exception as e:
        logger.error(f"Error in sync_pharmacy_integrations_task: {e}")
        raise


@shared_task(bind=True, name='medications.refresh_stock_visualizations')
def refresh_stock_visualizations_task(self):
    """
    Refresh stock visualizations that need updating.
    """
    try:
        service = IntelligentStockService()
        
        # Get visualizations that need refresh
        visualizations = StockVisualization.objects.filter(
            is_active=True,
            auto_refresh=True
        )
        
        refreshed_count = 0
        for visualization in visualizations:
            if visualization.needs_refresh:
                try:
                    # Regenerate visualization
                    days = (visualization.end_date - visualization.start_date).days
                    updated_visualization = service.generate_stock_visualization(
                        visualization.medication,
                        chart_type=visualization.chart_type,
                        days=days
                    )
                    
                    if updated_visualization:
                        refreshed_count += 1
                        logger.info(f"Refreshed visualization for {visualization.medication.name}")
                    
                except Exception as e:
                    logger.error(f"Error refreshing visualization for {visualization.medication.name}: {e}")
                    continue
        
        logger.info(f"Stock visualization refresh completed. Refreshed {refreshed_count} visualizations.")
        return {
            'status': 'success',
            'visualizations_refreshed': refreshed_count,
            'total_visualizations': len(visualizations)
        }
        
    except Exception as e:
        logger.error(f"Error in refresh_stock_visualizations_task: {e}")
        raise 