"""
Image processing tasks for medication images using Pillow.

This module contains Celery tasks for:
- Optimizing medication images in multiple formats
- Creating thumbnails and different sizes
- Converting to modern formats (WebP, AVIF, JPEG XL)
- Image metadata extraction and storage
- Batch image processing with priority handling
"""

import logging
import os
import json
from io import BytesIO
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from celery import shared_task
from django.core.files import File
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from PIL.Image import Resampling

from .models import Medication

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='medications.optimize_medication_images')
def optimize_medication_images_task(self, medication_id: int = None):
    """
    Optimize medication images for all medications or a specific one.
    
    Args:
        medication_id: Specific medication ID to optimize (None for all)
    """
    try:
        if medication_id:
            medications = [Medication.objects.get(id=medication_id)]
        else:
            # Get medications with pending image processing
            medications = Medication.objects.filter(
                image_processing_status='pending'
            ).order_by('-image_processing_priority', 'created_at')
        
        processed_count = 0
        for medication in medications:
            try:
                process_medication_image.delay(medication.id)
                processed_count += 1
                logger.info(f"Queued image processing for {medication.name}")
            except Exception as e:
                logger.error(f"Error queuing image processing for {medication.name}: {e}")
                continue
        
        logger.info(f"Image optimization queued for {processed_count} medications.")
        return {
            'status': 'success',
            'medications_queued': processed_count,
            'total_medications': len(medications)
        }
        
    except Exception as e:
        logger.error(f"Error in optimize_medication_images_task: {e}")
        raise


@shared_task(bind=True, name='medications.process_medication_image')
def process_medication_image(self, medication_id: int):
    """
    Process a single medication image with optimization.
    
    Args:
        medication_id: Medication ID to process
    """
    try:
        medication = Medication.objects.get(id=medication_id)
        
        # Update processing status
        medication.image_processing_status = 'processing'
        medication.image_processing_last_attempt = timezone.now()
        medication.image_processing_attempts += 1
        medication.save()
        
        # Get the source image
        source_image = medication.medication_image or medication.medication_image_original
        
        if not source_image:
            logger.warning(f"No source image found for medication {medication.name}")
            medication.image_processing_status = 'failed'
            medication.image_processing_error = 'No source image found'
            medication.save()
            return
        
        # Process the image
        result = process_image_with_pillow(source_image, medication)
        
        if result['success']:
            medication.image_processing_status = 'completed'
            medication.image_processing_error = ''
            medication.image_metadata = result['metadata']
            medication.image_optimization_level = result['optimization_level']
            medication.save()
            
            logger.info(f"Successfully processed image for {medication.name}")
        else:
            medication.image_processing_status = 'failed'
            medication.image_processing_error = result['error']
            medication.save()
            
            logger.error(f"Failed to process image for {medication.name}: {result['error']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in process_medication_image for medication {medication_id}: {e}")
        
        # Update medication status
        try:
            medication = Medication.objects.get(id=medication_id)
            medication.image_processing_status = 'failed'
            medication.image_processing_error = str(e)
            medication.save()
        except:
            pass
        
        raise


@shared_task(bind=True, name='medications.process_urgent_images')
def process_urgent_images_task(self):
    """Process high-priority medication images."""
    medications = Medication.objects.filter(
        image_processing_status='pending',
        image_processing_priority='urgent'
    ).order_by('created_at')
    
    for medication in medications:
        process_medication_image.delay(medication.id)
    
    return {'status': 'success', 'urgent_images_queued': len(medications)}


@shared_task(bind=True, name='medications.process_high_priority_images')
def process_high_priority_images_task(self):
    """Process high-priority medication images."""
    medications = Medication.objects.filter(
        image_processing_status='pending',
        image_processing_priority='high'
    ).order_by('created_at')
    
    for medication in medications:
        process_medication_image.delay(medication.id)
    
    return {'status': 'success', 'high_priority_images_queued': len(medications)}


@shared_task(bind=True, name='medications.process_standard_images')
def process_standard_images_task(self):
    """Process standard priority medication images."""
    medications = Medication.objects.filter(
        image_processing_status='pending',
        image_processing_priority='medium'
    ).order_by('created_at')
    
    for medication in medications:
        process_medication_image.delay(medication.id)
    
    return {'status': 'success', 'standard_images_queued': len(medications)}


@shared_task(bind=True, name='medications.process_low_priority_images')
def process_low_priority_images_task(self):
    """Process low priority medication images."""
    medications = Medication.objects.filter(
        image_processing_status='pending',
        image_processing_priority='low'
    ).order_by('created_at')
    
    for medication in medications:
        process_medication_image.delay(medication.id)
    
    return {'status': 'success', 'low_priority_images_queued': len(medications)}


@shared_task(bind=True, name='medications.cleanup_old_medication_images')
def cleanup_old_medication_images_task(self, days_to_keep: int = 90):
    """
    Clean up old medication images that are no longer needed.
    
    Args:
        days_to_keep: Number of days to keep old images
    """
    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=days_to_keep)
        
        # Find medications with old images that haven't been updated
        old_medications = Medication.objects.filter(
            updated_at__lt=cutoff_date,
            medication_image_original__isnull=False
        )
        
        cleaned_count = 0
        for medication in old_medications:
            try:
                # Keep only the optimized versions, remove original
                if medication.medication_image_webp and medication.medication_image_thumbnail:
                    # Remove original image file
                    if medication.medication_image_original:
                        medication.medication_image_original.delete(save=False)
                        medication.medication_image_original = None
                    
                    cleaned_count += 1
                    logger.info(f"Cleaned up old images for {medication.name}")
            except Exception as e:
                logger.error(f"Error cleaning up images for {medication.name}: {e}")
                continue
        
        logger.info(f"Cleaned up old images for {cleaned_count} medications.")
        return {
            'status': 'success',
            'medications_cleaned': cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_medication_images_task: {e}")
        raise


def process_image_with_pillow(source_image, medication: Medication) -> Dict[str, Any]:
    """
    Process medication image using Pillow with optimization.
    
    Args:
        source_image: Source image field
        medication: Medication instance
    
    Returns:
        Dictionary with processing results
    """
    try:
        # Open the image
        with Image.open(source_image.path) as img:
            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            # Extract metadata
            metadata = {
                'original_format': img.format,
                'original_mode': img.mode,
                'original_size': img.size,
                'original_width': img.width,
                'original_height': img.height,
                'processed_at': timezone.now().isoformat(),
            }
            
            # Determine optimization level based on priority
            optimization_level = medication.image_processing_priority
            if optimization_level == 'urgent':
                quality_settings = {'quality': 85, 'optimize': True}
                resize_factor = 0.8
            elif optimization_level == 'high':
                quality_settings = {'quality': 90, 'optimize': True}
                resize_factor = 0.9
            elif optimization_level == 'medium':
                quality_settings = {'quality': 85, 'optimize': True}
                resize_factor = 0.8
            else:  # low
                quality_settings = {'quality': 80, 'optimize': True}
                resize_factor = 0.7
            
            # Create optimized versions
            results = {}
            
            # 1. Create thumbnail (150x150)
            thumbnail = create_thumbnail(img, (150, 150))
            if thumbnail:
                thumbnail_path = save_image_to_field(thumbnail, medication, 'medication_image_thumbnail', 'JPEG', quality_settings)
                results['thumbnail'] = thumbnail_path
            
            # 2. Create WebP version
            webp_image = img.copy()
            webp_path = save_image_to_field(webp_image, medication, 'medication_image_webp', 'WEBP', quality_settings)
            results['webp'] = webp_path
            
            # 3. Create optimized JPEG
            optimized_jpeg = img.copy()
            if resize_factor < 1.0:
                new_size = (int(img.width * resize_factor), int(img.height * resize_factor))
                optimized_jpeg = optimized_jpeg.resize(new_size, Resampling.LANCZOS)
            
            # Apply basic enhancements
            optimized_jpeg = enhance_image(optimized_jpeg, optimization_level)
            
            jpeg_path = save_image_to_field(optimized_jpeg, medication, 'medication_image', 'JPEG', quality_settings)
            results['jpeg'] = jpeg_path
            
            # 4. Try to create AVIF (if supported)
            try:
                avif_path = save_image_to_field(img, medication, 'medication_image_avif', 'AVIF', quality_settings)
                results['avif'] = avif_path
            except Exception as e:
                logger.warning(f"AVIF not supported: {e}")
                results['avif'] = None
            
            # 5. Try to create JPEG XL (if supported)
            try:
                jxl_path = save_image_to_field(img, medication, 'medication_image_jpeg_xl', 'JPEG_XL', quality_settings)
                results['jxl'] = jxl_path
            except Exception as e:
                logger.warning(f"JPEG XL not supported: {e}")
                results['jxl'] = None
            
            # Update metadata with results
            metadata.update({
                'processed_formats': list(results.keys()),
                'optimization_level': optimization_level,
                'quality_settings': quality_settings,
                'resize_factor': resize_factor,
            })
            
            return {
                'success': True,
                'metadata': metadata,
                'optimization_level': optimization_level,
                'results': results
            }
            
    except Exception as e:
        logger.error(f"Error processing image for {medication.name}: {e}")
        return {
            'success': False,
            'error': str(e),
            'metadata': {},
            'optimization_level': 'none'
        }


def create_thumbnail(img: Image.Image, size: Tuple[int, int]) -> Optional[Image.Image]:
    """Create a thumbnail from the image."""
    try:
        thumbnail = img.copy()
        thumbnail.thumbnail(size, Resampling.LANCZOS)
        return thumbnail
    except Exception as e:
        logger.error(f"Error creating thumbnail: {e}")
        return None


def enhance_image(img: Image.Image, optimization_level: str) -> Image.Image:
    """Apply image enhancements based on optimization level."""
    try:
        enhanced = img.copy()
        
        if optimization_level in ['high', 'urgent']:
            # Apply sharpening
            enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
            
            # Enhance contrast slightly
            enhancer = ImageEnhance.Contrast(enhanced)
            enhanced = enhancer.enhance(1.1)
        
        elif optimization_level == 'medium':
            # Apply light sharpening
            enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
        
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing image: {e}")
        return img


def save_image_to_field(img: Image.Image, medication: Medication, field_name: str, 
                       format: str, quality_settings: Dict[str, Any]) -> Optional[str]:
    """Save image to a specific field of the medication model."""
    try:
        # Create a BytesIO buffer
        buffer = BytesIO()
        
        # Save image to buffer
        if format == 'JPEG':
            img.save(buffer, format='JPEG', **quality_settings)
        elif format == 'WEBP':
            img.save(buffer, format='WEBP', **quality_settings)
        elif format == 'AVIF':
            img.save(buffer, format='AVIF', **quality_settings)
        elif format == 'JPEG_XL':
            img.save(buffer, format='JPEG_XL', **quality_settings)
        else:
            img.save(buffer, format=format, **quality_settings)
        
        # Reset buffer position
        buffer.seek(0)
        
        # Create filename
        filename = f"{medication.id}_{field_name}_{format.lower()}.{format.lower()}"
        
        # Save to field
        field = getattr(medication, field_name)
        field.save(filename, ContentFile(buffer.getvalue()), save=False)
        
        return field.name
        
    except Exception as e:
        logger.error(f"Error saving {format} image for {medication.name}: {e}")
        return None


@shared_task(bind=True, name='medications.extract_image_metadata')
def extract_image_metadata_task(self, medication_id: int):
    """Extract metadata from medication images."""
    try:
        medication = Medication.objects.get(id=medication_id)
        
        metadata = {}
        
        # Check each image field
        image_fields = [
            'medication_image', 'medication_image_thumbnail', 'medication_image_webp',
            'medication_image_avif', 'medication_image_jpeg_xl', 'medication_image_original'
        ]
        
        for field_name in image_fields:
            field = getattr(medication, field_name)
            if field and hasattr(field, 'path') and os.path.exists(field.path):
                try:
                    with Image.open(field.path) as img:
                        metadata[field_name] = {
                            'format': img.format,
                            'mode': img.mode,
                            'size': img.size,
                            'width': img.width,
                            'height': img.height,
                            'file_size': os.path.getsize(field.path),
                        }
                except Exception as e:
                    logger.error(f"Error extracting metadata from {field_name}: {e}")
                    metadata[field_name] = {'error': str(e)}
        
        # Update medication metadata
        medication.image_metadata = metadata
        medication.save()
        
        return {'status': 'success', 'metadata': metadata}
        
    except Exception as e:
        logger.error(f"Error in extract_image_metadata_task: {e}")
        raise


@shared_task(bind=True, name='medications.batch_image_processing')
def batch_image_processing_task(self, medication_ids: list = None, priority: str = 'medium'):
    """
    Process multiple medication images in batch.
    
    Args:
        medication_ids: List of medication IDs to process
        priority: Processing priority level
    """
    try:
        if medication_ids:
            medications = Medication.objects.filter(id__in=medication_ids)
        else:
            # Get medications with pending processing
            medications = Medication.objects.filter(
                image_processing_status='pending'
            ).order_by('-image_processing_priority', 'created_at')[:50]  # Limit batch size
        
        # Update priorities if specified
        if priority != 'medium':
            medications.update(image_processing_priority=priority)
        
        # Queue processing tasks
        for medication in medications:
            if priority == 'urgent':
                process_urgent_images_task.delay()
            elif priority == 'high':
                process_high_priority_images_task.delay()
            elif priority == 'low':
                process_low_priority_images_task.delay()
            else:
                process_standard_images_task.delay()
        
        return {
            'status': 'success',
            'medications_queued': len(medications),
            'priority': priority
        }
        
    except Exception as e:
        logger.error(f"Error in batch_image_processing_task: {e}")
        raise 