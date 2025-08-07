"""
Celery Tasks for Pharmacy Locator Plugin
Background tasks for pharmacy data sync, inventory management, and notifications.
"""
import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from django.utils import timezone

from .models import Pharmacy, MedicationInventory, PharmacyReview, PharmacySearchLog
from .services import PharmacyLocatorService
from .signals import (
    pharmacy_inventory_low,
    pharmacy_status_changed,
    medication_reservation_expired
)

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def update_pharmacy_ratings_task(self, pharmacy_id):
    """
    Update pharmacy average rating and review count.
    
    Args:
        pharmacy_id: ID of the pharmacy to update
    """
    try:
        pharmacy = Pharmacy.objects.get(id=pharmacy_id)
        
        # Calculate new ratings
        reviews = PharmacyReview.objects.filter(pharmacy=pharmacy)
        ratings_data = reviews.aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id')
        )
        
        old_rating = pharmacy.average_rating
        new_rating = ratings_data['avg_rating'] or 0.0
        
        # Update pharmacy
        pharmacy.average_rating = new_rating
        pharmacy.total_reviews = ratings_data['total_reviews']
        pharmacy.save(update_fields=['average_rating', 'total_reviews'])
        
        logger.info(f"Updated ratings for pharmacy {pharmacy_id}: {old_rating:.1f} -> {new_rating:.1f}")
        
        return {
            'success': True,
            'pharmacy_id': pharmacy_id,
            'old_rating': old_rating,
            'new_rating': new_rating,
            'total_reviews': ratings_data['total_reviews']
        }
        
    except Pharmacy.DoesNotExist:
        logger.error(f"Pharmacy {pharmacy_id} not found")
        return {'success': False, 'error': 'Pharmacy not found'}
    
    except Exception as exc:
        logger.error(f"Failed to update pharmacy ratings: {exc}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying rating update for pharmacy {pharmacy_id}")
            raise self.retry(countdown=60, exc=exc)
        
        return {'success': False, 'error': str(exc)}


@shared_task(bind=True, max_retries=3)
def sync_inventory_with_external_system_task(self, pharmacy_id, inventory_items=None):
    """
    Sync pharmacy inventory with external systems.
    
    Args:
        pharmacy_id: ID of the pharmacy
        inventory_items: Optional list of specific inventory item IDs to sync
    """
    try:
        pharmacy = Pharmacy.objects.get(id=pharmacy_id)
        
        if not pharmacy.api_endpoint:
            logger.warning(f"No API endpoint configured for pharmacy {pharmacy_id}")
            return {'success': False, 'error': 'No API endpoint configured'}
        
        logger.info(f"Syncing inventory for pharmacy {pharmacy_id}")
        
        # This would typically make API calls to external pharmacy systems
        # For now, we'll simulate the sync process
        
        # Get inventory items to sync
        if inventory_items:
            items_to_sync = MedicationInventory.objects.filter(
                id__in=inventory_items,
                pharmacy=pharmacy
            )
        else:
            items_to_sync = MedicationInventory.objects.filter(
                pharmacy=pharmacy,
                sync_enabled=True
            )
        
        synced_count = 0
        errors = []
        
        for inventory in items_to_sync:
            try:
                # Simulate API call to external system
                # In reality, this would be something like:
                # external_data = make_api_call(pharmacy.api_endpoint, inventory.external_inventory_id)
                
                # For simulation, we'll just update the last_updated timestamp
                inventory.last_updated = timezone.now()
                inventory.save(update_fields=['last_updated'])
                
                synced_count += 1
                logger.debug(f"Synced inventory item {inventory.id}")
                
            except Exception as e:
                error_msg = f"Failed to sync {inventory.medication_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"Inventory sync completed for pharmacy {pharmacy_id}: {synced_count} items synced")
        
        return {
            'success': True,
            'pharmacy_id': pharmacy_id,
            'synced_count': synced_count,
            'errors': errors
        }
        
    except Pharmacy.DoesNotExist:
        logger.error(f"Pharmacy {pharmacy_id} not found")
        return {'success': False, 'error': 'Pharmacy not found'}
    
    except Exception as exc:
        logger.error(f"Failed to sync inventory: {exc}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying inventory sync for pharmacy {pharmacy_id}")
            raise self.retry(countdown=120, exc=exc)
        
        return {'success': False, 'error': str(exc)}


@shared_task
def send_low_stock_alert_task(inventory_id):
    """
    Send low stock alert for medication inventory.
    
    Args:
        inventory_id: ID of the inventory item with low stock
    """
    try:
        inventory = MedicationInventory.objects.select_related('pharmacy').get(id=inventory_id)
        
        logger.info(f"Sending low stock alert for {inventory.medication_name} at {inventory.pharmacy.name}")
        
        # Send signal for low stock
        pharmacy_inventory_low.send(
            sender=send_low_stock_alert_task,
            inventory_item=inventory
        )
        
        # Additional logic for automatic reordering could go here
        # For example, if the pharmacy has automatic reordering enabled:
        if hasattr(inventory.pharmacy, 'auto_reorder_enabled') and inventory.pharmacy.auto_reorder_enabled:
            logger.info(f"Triggering automatic reorder for {inventory.medication_name}")
            # trigger_automatic_reorder(inventory)
        
        return {
            'success': True,
            'inventory_id': inventory_id,
            'medication_name': inventory.medication_name,
            'pharmacy_name': inventory.pharmacy.name,
            'current_quantity': inventory.quantity_available
        }
        
    except MedicationInventory.DoesNotExist:
        logger.error(f"Inventory item {inventory_id} not found")
        return {'success': False, 'error': 'Inventory item not found'}
    
    except Exception as e:
        logger.error(f"Failed to send low stock alert: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def notify_patients_pharmacy_status_change_task(pharmacy_id, new_status):
    """
    Notify patients when their pharmacy status changes.
    
    Args:
        pharmacy_id: ID of the pharmacy
        new_status: New status of the pharmacy
    """
    try:
        pharmacy = Pharmacy.objects.get(id=pharmacy_id)
        
        logger.info(f"Notifying patients about pharmacy status change: {pharmacy.name} -> {new_status}")
        
        # This would require a relationship between patients and their preferred pharmacies
        # For now, we'll simulate finding affected patients
        
        # In a real implementation, you might have:
        # affected_patients = User.objects.filter(preferred_pharmacies=pharmacy)
        # or find patients through medication schedules, prescriptions, etc.
        
        # Send pharmacy status change signal
        pharmacy_status_changed.send(
            sender=notify_patients_pharmacy_status_change_task,
            pharmacy=pharmacy,
            old_status='active',  # We don't track old status in this simple example
            new_status=new_status
        )
        
        return {
            'success': True,
            'pharmacy_id': pharmacy_id,
            'new_status': new_status
        }
        
    except Pharmacy.DoesNotExist:
        logger.error(f"Pharmacy {pharmacy_id} not found")
        return {'success': False, 'error': 'Pharmacy not found'}
    
    except Exception as e:
        logger.error(f"Failed to notify patients: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_expired_reservations():
    """
    Clean up expired medication reservations.
    Runs every hour to check for and clean up expired reservations.
    """
    try:
        logger.info("Cleaning up expired medication reservations...")
        
        # This would typically query a reservations table
        # For now, we'll simulate finding expired reservations
        # In a real implementation, you would have a MedicationReservation model
        
        expired_count = 0
        
        # Simulate expired reservations data
        # expired_reservations = MedicationReservation.objects.filter(
        #     expiry_time__lt=timezone.now(),
        #     status='active'
        # )
        
        # For each expired reservation, send signal
        # for reservation in expired_reservations:
        #     medication_reservation_expired.send(
        #         sender=cleanup_expired_reservations,
        #         reservation_data={
        #             'inventory_id': reservation.inventory_id,
        #             'user_id': reservation.user_id,
        #             'quantity_reserved': reservation.quantity,
        #             'medication_name': reservation.inventory.medication_name,
        #             'pharmacy_name': reservation.inventory.pharmacy.name
        #         }
        #     )
        #     reservation.status = 'expired'
        #     reservation.save()
        #     expired_count += 1
        
        logger.info(f"Cleaned up {expired_count} expired reservations")
        
        return {
            'success': True,
            'expired_count': expired_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired reservations: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def update_pharmacy_analytics_task(pharmacy_id):
    """
    Update analytics data for a pharmacy.
    
    Args:
        pharmacy_id: ID of the pharmacy
    """
    try:
        pharmacy = Pharmacy.objects.get(id=pharmacy_id)
        
        logger.info(f"Updating analytics for pharmacy {pharmacy_id}")
        
        # Calculate various analytics metrics
        analytics_data = {}
        
        # Search analytics
        search_logs = PharmacySearchLog.objects.filter(
            pharmacies_found=pharmacy
        )
        
        analytics_data['total_searches'] = search_logs.count()
        analytics_data['searches_last_30_days'] = search_logs.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # Review analytics
        reviews = PharmacyReview.objects.filter(pharmacy=pharmacy)
        
        analytics_data['total_reviews'] = reviews.count()
        analytics_data['average_rating'] = reviews.aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0
        
        # Rating distribution
        rating_distribution = {}
        for rating in range(1, 6):
            rating_distribution[f'{rating}_star'] = reviews.filter(rating=rating).count()
        
        analytics_data['rating_distribution'] = rating_distribution
        
        # Inventory analytics
        inventory_items = MedicationInventory.objects.filter(pharmacy=pharmacy)
        
        analytics_data['total_medications'] = inventory_items.count()
        analytics_data['in_stock_medications'] = inventory_items.filter(
            status='in_stock'
        ).count()
        analytics_data['low_stock_medications'] = inventory_items.filter(
            quantity_available__lte=models.F('reorder_level')
        ).count()
        
        # Store analytics data (in a real implementation, you might store this in a separate model)
        # For now, we'll just log it
        logger.info(f"Analytics for pharmacy {pharmacy_id}: {analytics_data}")
        
        return {
            'success': True,
            'pharmacy_id': pharmacy_id,
            'analytics_data': analytics_data
        }
        
    except Pharmacy.DoesNotExist:
        logger.error(f"Pharmacy {pharmacy_id} not found")
        return {'success': False, 'error': 'Pharmacy not found'}
    
    except Exception as e:
        logger.error(f"Failed to update pharmacy analytics: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def sync_pharmacy_with_external_system_task(pharmacy_id):
    """
    Sync pharmacy information with external systems.
    
    Args:
        pharmacy_id: ID of the pharmacy to sync
    """
    try:
        pharmacy = Pharmacy.objects.get(id=pharmacy_id)
        
        if not pharmacy.api_endpoint or not pharmacy.external_id:
            logger.warning(f"Pharmacy {pharmacy_id} missing API endpoint or external ID")
            return {'success': False, 'error': 'Missing API configuration'}
        
        logger.info(f"Syncing pharmacy {pharmacy_id} with external system")
        
        # This would make actual API calls to external systems
        # For example:
        # - Pharmacy management systems
        # - Chain pharmacy databases
        # - Insurance provider networks
        # - Government health databases
        
        # Simulate external sync
        sync_data = {
            'pharmacy_id': str(pharmacy.id),
            'external_id': pharmacy.external_id,
            'last_sync': timezone.now().isoformat(),
            'status': 'synced'
        }
        
        # Update pharmacy sync timestamp
        pharmacy.updated_at = timezone.now()
        pharmacy.save(update_fields=['updated_at'])
        
        logger.info(f"External sync completed for pharmacy {pharmacy_id}")
        
        return {
            'success': True,
            'pharmacy_id': pharmacy_id,
            'sync_data': sync_data
        }
        
    except Pharmacy.DoesNotExist:
        logger.error(f"Pharmacy {pharmacy_id} not found")
        return {'success': False, 'error': 'Pharmacy not found'}
    
    except Exception as e:
        logger.error(f"Failed to sync pharmacy with external system: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def generate_pharmacy_reports():
    """
    Generate daily reports for pharmacy analytics.
    Runs daily to compile pharmacy statistics and insights.
    """
    try:
        logger.info("Generating pharmacy reports...")
        
        report_date = timezone.now().date()
        
        # Overall system statistics
        total_pharmacies = Pharmacy.objects.filter(status='active').count()
        total_inventory_items = MedicationInventory.objects.count()
        total_searches_today = PharmacySearchLog.objects.filter(
            created_at__date=report_date
        ).count()
        
        # Top searched medications
        top_medications = PharmacySearchLog.objects.filter(
            created_at__date=report_date,
            medication_searched__isnull=False
        ).exclude(
            medication_searched=''
        ).values('medication_searched').annotate(
            search_count=Count('id')
        ).order_by('-search_count')[:10]
        
        # Pharmacy performance metrics
        top_rated_pharmacies = Pharmacy.objects.filter(
            status='active',
            total_reviews__gte=5
        ).order_by('-average_rating')[:10]
        
        # Low stock alerts
        low_stock_count = MedicationInventory.objects.filter(
            quantity_available__lte=models.F('reorder_level')
        ).count()
        
        # Compile report data
        report_data = {
            'report_date': report_date.isoformat(),
            'system_stats': {
                'total_pharmacies': total_pharmacies,
                'total_inventory_items': total_inventory_items,
                'searches_today': total_searches_today,
                'low_stock_alerts': low_stock_count
            },
            'top_medications': list(top_medications),
            'top_rated_pharmacies': [
                {
                    'name': p.name,
                    'city': p.city,
                    'rating': p.average_rating,
                    'reviews': p.total_reviews
                }
                for p in top_rated_pharmacies
            ]
        }
        
        logger.info(f"Pharmacy report generated for {report_date}")
        
        # In a real implementation, you might save this to a reports table
        # or send it via email to administrators
        
        return {
            'success': True,
            'report_date': report_date.isoformat(),
            'report_data': report_data
        }
        
    except Exception as e:
        logger.error(f"Failed to generate pharmacy reports: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def update_pharmacy_locations():
    """
    Update pharmacy location coordinates using geocoding.
    Runs weekly to ensure location data is accurate.
    """
    try:
        logger.info("Updating pharmacy locations...")
        
        # Find pharmacies without location data
        pharmacies_without_location = Pharmacy.objects.filter(
            location__isnull=True,
            status='active'
        )
        
        locator_service = PharmacyLocatorService()
        updated_count = 0
        
        for pharmacy in pharmacies_without_location:
            try:
                # Geocode the pharmacy address
                full_address = pharmacy.get_full_address()
                geocoded = locator_service._geocode_address(full_address)
                
                if geocoded:
                    from django.contrib.gis.geos import Point
                    pharmacy.location = Point(
                        geocoded['longitude'],
                        geocoded['latitude']
                    )
                    pharmacy.save(update_fields=['location'])
                    updated_count += 1
                    
                    logger.info(f"Updated location for pharmacy {pharmacy.name}")
                
            except Exception as e:
                logger.error(f"Failed to update location for pharmacy {pharmacy.id}: {e}")
                continue
        
        logger.info(f"Updated locations for {updated_count} pharmacies")
        
        return {
            'success': True,
            'updated_count': updated_count
        }
        
    except Exception as e:
        logger.error(f"Failed to update pharmacy locations: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_old_search_logs(days_old=90):
    """
    Clean up old pharmacy search logs for data retention.
    
    Args:
        days_old: Number of days after which to delete search logs
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        logger.info(f"Cleaning up pharmacy search logs older than {days_old} days...")
        
        # Delete old search logs
        deleted_count, _ = PharmacySearchLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Deleted {deleted_count} old search logs")
        
        return {
            'success': True,
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup search logs: {e}")
        return {'success': False, 'error': str(e)}
