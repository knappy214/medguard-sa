"""
Wagtail 7.0.2 Mobile Optimization Module
Enhanced responsive image system and mobile features for MedGuard SA
"""

from django.conf import settings
from django.core.cache import cache
from django.utils.html import format_html
from wagtail.images.models import Image
from wagtail.images.shortcuts import get_rendition_or_not_found
from wagtail.images.templatetags.wagtailimages_tags import image_url
import json
import logging

logger = logging.getLogger(__name__)


class MobileImageOptimizer:
    """
    Enhanced responsive image system for mobile devices
    Wagtail 7.0.2 responsive image features
    """
    
    # Mobile breakpoints for responsive images
    MOBILE_BREAKPOINTS = {
        'xs': 320,   # Small phones
        'sm': 576,   # Large phones
        'md': 768,   # Tablets
        'lg': 992,   # Small desktops
        'xl': 1200,  # Large desktops
    }
    
    # Image quality settings for different devices
    QUALITY_SETTINGS = {
        'mobile': 85,    # Higher compression for mobile
        'tablet': 90,    # Medium quality for tablets
        'desktop': 95,   # High quality for desktop
    }
    
    @classmethod
    def get_responsive_image_renditions(cls, image, filter_specs=None):
        """
        Generate responsive image renditions for all breakpoints
        """
        if not image:
            return {}
            
        if filter_specs is None:
            filter_specs = {
                'xs': 'fill-320x240',
                'sm': 'fill-576x432', 
                'md': 'fill-768x576',
                'lg': 'fill-992x744',
                'xl': 'fill-1200x900',
            }
        
        renditions = {}
        cache_key = f"mobile_responsive_{image.id}_{hash(str(filter_specs))}"
        
        # Check cache first
        cached_renditions = cache.get(cache_key)
        if cached_renditions:
            return cached_renditions
        
        try:
            for breakpoint, filter_spec in filter_specs.items():
                rendition = get_rendition_or_not_found(image, filter_spec)
                renditions[breakpoint] = {
                    'url': rendition.url,
                    'width': rendition.width,
                    'height': rendition.height,
                    'alt': image.alt or '',
                }
            
            # Cache for 1 hour
            cache.set(cache_key, renditions, 3600)
            return renditions
            
        except Exception as e:
            logger.error(f"Error generating responsive renditions: {e}")
            return {}
    
    @classmethod
    def get_picture_element_html(cls, image, filter_specs=None, css_class=''):
        """
        Generate HTML5 picture element with responsive images
        """
        renditions = cls.get_responsive_image_renditions(image, filter_specs)
        
        if not renditions:
            return ''
        
        # Build source elements for different breakpoints
        sources = []
        for breakpoint, rendition in renditions.items():
            media_query = f"(min-width: {cls.MOBILE_BREAKPOINTS[breakpoint]}px)"
            source_html = f'<source media="{media_query}" srcset="{rendition["url"]}">'
            sources.append(source_html)
        
        # Default image (smallest breakpoint)
        default_rendition = renditions.get('xs', renditions.get(list(renditions.keys())[0]))
        
        picture_html = f"""
        <picture class="{css_class}">
            {''.join(sources)}
            <img src="{default_rendition['url']}" 
                 alt="{default_rendition['alt']}"
                 width="{default_rendition['width']}"
                 height="{default_rendition['height']}"
                 loading="lazy"
                 decoding="async">
        </picture>
        """
        
        return format_html(picture_html)
    
    @classmethod
    def optimize_for_mobile(cls, image, device_type='mobile'):
        """
        Optimize image specifically for mobile devices
        """
        if not image:
            return None
            
        quality = cls.QUALITY_SETTINGS.get(device_type, 85)
        
        # Mobile-optimized filter specs
        mobile_filters = {
            'mobile': f'fill-400x300|jpegquality-{quality}',
            'tablet': f'fill-800x600|jpegquality-{quality}',
            'desktop': f'fill-1200x900|jpegquality-{quality}',
        }
        
        filter_spec = mobile_filters.get(device_type, mobile_filters['mobile'])
        
        try:
            rendition = get_rendition_or_not_found(image, filter_spec)
            return {
                'url': rendition.url,
                'width': rendition.width,
                'height': rendition.height,
                'alt': image.alt or '',
                'file_size': rendition.file.size if rendition.file else 0,
            }
        except Exception as e:
            logger.error(f"Error optimizing image for mobile: {e}")
            return None


class MobileImageMiddleware:
    """
    Middleware to detect mobile devices and optimize images
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Detect mobile device
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        is_mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone', 'ipad'])
        
        # Add mobile detection to request
        request.is_mobile_device = is_mobile
        
        response = self.get_response(request)
        return response


# Template tags for responsive images
def responsive_image(image, filter_specs=None, css_class=''):
    """
    Template tag for responsive images
    Usage: {% responsive_image page.image 'xs:fill-320x240,md:fill-768x576' 'img-fluid' %}
    """
    if not image:
        return ''
    
    if filter_specs:
        # Parse filter specs string
        specs = {}
        for spec in filter_specs.split(','):
            if ':' in spec:
                breakpoint, filter_spec = spec.split(':', 1)
                specs[breakpoint.strip()] = filter_spec.strip()
        filter_specs = specs
    
    return MobileImageOptimizer.get_picture_element_html(image, filter_specs, css_class)


def mobile_optimized_image(image, device_type='mobile'):
    """
    Template tag for mobile-optimized images
    Usage: {% mobile_optimized_image page.image 'mobile' %}
    """
    if not image:
        return ''
    
    optimized = MobileImageOptimizer.optimize_for_mobile(image, device_type)
    if not optimized:
        return ''
    
    return format_html(
        '<img src="{}" alt="{}" width="{}" height="{}" loading="lazy" decoding="async">',
        optimized['url'],
        optimized['alt'],
        optimized['width'],
        optimized['height']
    ) 