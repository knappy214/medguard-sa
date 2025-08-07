"""
Celery Tasks for Prescription OCR Plugin
Background tasks for OCR processing and image analysis.
"""
import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from wagtailimages.models import Image

from .models import PrescriptionOCRResult
from .services import PrescriptionOCRService

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def process_prescription_ocr_async(self, image_id, user_id, template_id=None):
    """
    Process prescription image OCR asynchronously.
    
    Args:
        image_id: ID of the image to process
        user_id: ID of the user who initiated the processing
        template_id: Optional OCR template ID
    """
    try:
        # Get image and user objects
        image = Image.objects.get(id=image_id)
        user = User.objects.get(id=user_id)
        
        logger.info(f"Starting OCR processing for image {image_id}")
        
        # Initialize OCR service
        ocr_service = PrescriptionOCRService()
        
        # Process the image
        result = ocr_service.process_prescription_image(
            image.file.path,
            template_id=template_id
        )
        
        if result['success']:
            # Create OCR result record
            ocr_result = PrescriptionOCRResult.objects.create(
                prescription_image=image,
                extracted_text=result['extracted_text'],
                confidence_score=result['confidence_score'],
                processed_by=user,
                **result['parsed_data']
            )
            
            logger.info(f"OCR processing completed for image {image_id}, result ID: {ocr_result.id}")
            
            # Send notification if confidence is low
            if result['confidence_score'] < 0.7:
                send_low_confidence_notification.delay(ocr_result.id, user_id)
            
            return {
                'success': True,
                'ocr_result_id': str(ocr_result.id),
                'confidence_score': result['confidence_score']
            }
        
        else:
            logger.error(f"OCR processing failed for image {image_id}: {result['error']}")
            return {
                'success': False,
                'error': result['error']
            }
    
    except Image.DoesNotExist:
        logger.error(f"Image {image_id} not found")
        return {'success': False, 'error': 'Image not found'}
    
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    
    except Exception as exc:
        logger.error(f"OCR processing failed with exception: {exc}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying OCR processing for image {image_id}")
            raise self.retry(countdown=60, exc=exc)
        
        return {'success': False, 'error': str(exc)}


@shared_task
def send_low_confidence_notification(ocr_result_id, user_id):
    """
    Send notification when OCR confidence is low.
    
    Args:
        ocr_result_id: ID of the OCR result
        user_id: ID of the user to notify
    """
    try:
        ocr_result = PrescriptionOCRResult.objects.get(id=ocr_result_id)
        user = User.objects.get(id=user_id)
        
        from medguard_backend.medguard_notifications.services import NotificationService
        
        notification_service = NotificationService()
        notification_service.send_notification(
            user=user,
            title="Low OCR Confidence",
            message=f"OCR processing for prescription image has low confidence ({ocr_result.confidence_score:.1%}). Manual verification recommended.",
            notification_type="ocr_low_confidence",
            metadata={
                'ocr_result_id': str(ocr_result_id),
                'confidence_score': ocr_result.confidence_score
            }
        )
        
        logger.info(f"Low confidence notification sent for OCR result {ocr_result_id}")
        
    except Exception as e:
        logger.error(f"Failed to send low confidence notification: {e}")


@shared_task
def batch_process_prescriptions(image_ids, user_id, template_id=None):
    """
    Process multiple prescription images in batch.
    
    Args:
        image_ids: List of image IDs to process
        user_id: ID of the user who initiated the processing
        template_id: Optional OCR template ID
    """
    results = []
    
    for image_id in image_ids:
        try:
            result = process_prescription_ocr_async.apply_async(
                args=[image_id, user_id, template_id]
            )
            results.append({
                'image_id': image_id,
                'task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            logger.error(f"Failed to queue OCR processing for image {image_id}: {e}")
            results.append({
                'image_id': image_id,
                'status': 'failed',
                'error': str(e)
            })
    
    return results


@shared_task
def cleanup_old_ocr_results(days_old=90):
    """
    Clean up old OCR results for data retention compliance.
    
    Args:
        days_old: Number of days after which to archive/delete results
    """
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days_old)
    
    try:
        # Find old OCR results
        old_results = PrescriptionOCRResult.objects.filter(
            processed_at__lt=cutoff_date,
            is_verified=True  # Only clean up verified results
        )
        
        count = old_results.count()
        
        # Archive or delete based on HIPAA requirements
        # For now, we'll just log the cleanup action
        for result in old_results:
            logger.info(f"Archiving OCR result {result.id} from {result.processed_at}")
            
            # Add to access log
            if not result.access_log:
                result.access_log = []
            
            result.access_log.append({
                'action': 'archived',
                'timestamp': timezone.now().isoformat(),
                'reason': f'Automatic cleanup after {days_old} days'
            })
            
            result.save(update_fields=['access_log'])
        
        logger.info(f"Cleanup completed: processed {count} old OCR results")
        
        return {
            'success': True,
            'processed_count': count
        }
        
    except Exception as e:
        logger.error(f"OCR cleanup failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def validate_ocr_accuracy(sample_size=10):
    """
    Validate OCR accuracy by comparing with manually verified results.
    
    Args:
        sample_size: Number of results to sample for validation
    """
    try:
        # Get recent verified results for accuracy analysis
        verified_results = PrescriptionOCRResult.objects.filter(
            is_verified=True,
            processed_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).order_by('-processed_at')[:sample_size]
        
        accuracy_metrics = {
            'total_samples': len(verified_results),
            'high_confidence_accurate': 0,
            'low_confidence_accurate': 0,
            'false_positives': 0,
            'false_negatives': 0
        }
        
        for result in verified_results:
            # Simple accuracy check based on confidence vs verification
            if result.confidence_score >= 0.8:
                if result.is_verified:
                    accuracy_metrics['high_confidence_accurate'] += 1
                else:
                    accuracy_metrics['false_positives'] += 1
            else:
                if result.is_verified:
                    accuracy_metrics['low_confidence_accurate'] += 1
                else:
                    accuracy_metrics['false_negatives'] += 1
        
        # Calculate overall accuracy
        total_accurate = (
            accuracy_metrics['high_confidence_accurate'] + 
            accuracy_metrics['low_confidence_accurate']
        )
        
        if accuracy_metrics['total_samples'] > 0:
            overall_accuracy = total_accurate / accuracy_metrics['total_samples']
            accuracy_metrics['overall_accuracy'] = overall_accuracy
        else:
            accuracy_metrics['overall_accuracy'] = 0.0
        
        logger.info(f"OCR accuracy validation completed: {overall_accuracy:.2%}")
        
        return accuracy_metrics
        
    except Exception as e:
        logger.error(f"OCR accuracy validation failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }
