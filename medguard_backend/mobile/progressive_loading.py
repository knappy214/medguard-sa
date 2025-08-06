"""
Progressive loading implementation for mobile performance
Wagtail 7.0.2 progressive loading features
"""

from django.core.cache import cache
from django.http import JsonResponse
from django.utils.html import format_html
from wagtail.models import Page
from wagtail.images.models import Image
from wagtail.images.shortcuts import get_rendition_or_not_found
import json
import logging
import time

logger = logging.getLogger(__name__)


class ProgressiveLoader:
    """
    Progressive loading system for mobile devices
    """
    
    # Loading priorities
    PRIORITIES = {
        'critical': 1,    # Above-the-fold content
        'high': 2,        # Important content
        'medium': 3,      # Secondary content
        'low': 4,         # Below-the-fold content
    }
    
    # Chunk sizes for progressive loading
    CHUNK_SIZES = {
        'mobile': 5,      # Smaller chunks for mobile
        'tablet': 10,     # Medium chunks for tablets
        'desktop': 15,    # Larger chunks for desktop
    }
    
    @classmethod
    def get_progressive_content(cls, page, device_type='mobile', priority='medium'):
        """
        Get content with progressive loading metadata
        """
        chunk_size = cls.CHUNK_SIZES.get(device_type, 5)
        
        # Get page content in chunks
        content_chunks = cls._chunk_content(page, chunk_size)
        
        return {
            'chunks': content_chunks,
            'total_chunks': len(content_chunks),
            'priority': priority,
            'device_type': device_type,
            'load_strategy': cls._get_load_strategy(device_type, priority),
        }
    
    @classmethod
    def _chunk_content(cls, page, chunk_size):
        """
        Split page content into loadable chunks
        """
        chunks = []
        
        # Get StreamField blocks if available
        if hasattr(page, 'body') and page.body:
            blocks = list(page.body)
            
            for i in range(0, len(blocks), chunk_size):
                chunk = blocks[i:i + chunk_size]
                chunks.append({
                    'id': f'chunk_{i//chunk_size}',
                    'blocks': chunk,
                    'index': i // chunk_size,
                })
        
        # If no StreamField, create single chunk
        if not chunks:
            chunks.append({
                'id': 'chunk_0',
                'content': page.content if hasattr(page, 'content') else str(page),
                'index': 0,
            })
        
        return chunks
    
    @classmethod
    def _get_load_strategy(cls, device_type, priority):
        """
        Get loading strategy based on device and priority
        """
        strategies = {
            'mobile': {
                'critical': 'eager',
                'high': 'lazy',
                'medium': 'lazy',
                'low': 'lazy',
            },
            'tablet': {
                'critical': 'eager',
                'high': 'lazy',
                'medium': 'lazy',
                'low': 'lazy',
            },
            'desktop': {
                'critical': 'eager',
                'high': 'lazy',
                'medium': 'lazy',
                'low': 'lazy',
            }
        }
        
        return strategies.get(device_type, {}).get(priority, 'lazy')


class LazyImageLoader:
    """
    Lazy loading for images with progressive enhancement
    """
    
    @classmethod
    def get_lazy_image_html(cls, image, filter_spec='fill-400x300', css_class=''):
        """
        Generate lazy-loaded image HTML
        """
        if not image:
            return ''
        
        try:
            rendition = get_rendition_or_not_found(image, filter_spec)
            
            # Generate low-quality placeholder
            placeholder = cls._generate_placeholder(rendition)
            
            html = f"""
            <div class="lazy-image-container {css_class}">
                <img src="{placeholder}"
                     data-src="{rendition.url}"
                     alt="{image.alt or ''}"
                     width="{rendition.width}"
                     height="{rendition.height}"
                     loading="lazy"
                     decoding="async"
                     class="lazy-image"
                     onload="this.classList.add('loaded')">
                <div class="lazy-image-placeholder"></div>
            </div>
            """
            
            return format_html(html)
            
        except Exception as e:
            logger.error(f"Error generating lazy image: {e}")
            return ''
    
    @classmethod
    def _generate_placeholder(cls, rendition):
        """
        Generate low-quality placeholder for progressive loading
        """
        # Use a very small, blurred version as placeholder
        try:
            placeholder_spec = f'fill-20x15|blur-10'
            placeholder = get_rendition_or_not_found(rendition.image, placeholder_spec)
            return placeholder.url
        except:
            # Fallback to data URI
            return 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMTUiIHZpZXdCb3g9IjAgMCAyMCAxNSIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjIwIiBoZWlnaHQ9IjE1IiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xMCA3LjVMMTUgMTJIMTVMMTAgMTIuNUw1IDEySDFMMTAgNy41WiIgZmlsbD0iI0QxRDU5QSIvPgo8L3N2Zz4K'


class ProgressiveContentLoader:
    """
    Progressive content loading with intersection observer
    """
    
    @classmethod
    def get_progressive_loading_script(cls):
        """
        Get JavaScript for progressive loading
        """
        script = """
        <script>
        class ProgressiveLoader {
            constructor() {
                this.observer = null;
                this.loadedChunks = new Set();
                this.init();
            }
            
            init() {
                // Initialize intersection observer
                this.observer = new IntersectionObserver(
                    (entries) => {
                        entries.forEach(entry => {
                            if (entry.isIntersecting) {
                                this.loadChunk(entry.target);
                            }
                        });
                    },
                    {
                        rootMargin: '50px',
                        threshold: 0.1
                    }
                );
                
                // Observe lazy elements
                this.observeLazyElements();
            }
            
            observeLazyElements() {
                const lazyElements = document.querySelectorAll('[data-lazy]');
                lazyElements.forEach(el => this.observer.observe(el));
            }
            
            loadChunk(element) {
                const chunkId = element.dataset.chunkId;
                if (this.loadedChunks.has(chunkId)) return;
                
                this.loadedChunks.add(chunkId);
                
                // Load chunk content
                fetch(`/api/mobile/chunk/${chunkId}/`)
                    .then(response => response.json())
                    .then(data => {
                        element.innerHTML = data.content;
                        element.classList.add('loaded');
                    })
                    .catch(error => {
                        console.error('Error loading chunk:', error);
                    });
            }
        }
        
        // Initialize when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
            new ProgressiveLoader();
        });
        </script>
        """
        
        return format_html(script)
    
    @classmethod
    def get_lazy_loading_css(cls):
        """
        Get CSS for lazy loading animations
        """
        css = """
        <style>
        .lazy-image-container {
            position: relative;
            overflow: hidden;
        }
        
        .lazy-image {
            opacity: 0;
            transition: opacity 0.3s ease-in-out;
        }
        
        .lazy-image.loaded {
            opacity: 1;
        }
        
        .lazy-image-placeholder {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
        }
        
        .lazy-image.loaded + .lazy-image-placeholder {
            display: none;
        }
        
        @keyframes loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        .progressive-chunk {
            min-height: 100px;
            background: #f9f9f9;
            border-radius: 8px;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
        }
        
        .progressive-chunk.loaded {
            background: transparent;
            min-height: auto;
        }
        </style>
        """
        
        return format_html(css)


class MobilePerformanceMonitor:
    """
    Monitor mobile performance and loading metrics
    """
    
    @classmethod
    def track_loading_performance(cls, request, page_id, load_time):
        """
        Track page loading performance
        """
        device_type = cls._get_device_type(request)
        
        metrics = {
            'page_id': page_id,
            'device_type': device_type,
            'load_time': load_time,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': time.time(),
        }
        
        # Store in cache for analysis
        cache_key = f"mobile_performance_{page_id}_{device_type}"
        cache.set(cache_key, metrics, 3600)
        
        return metrics
    
    @classmethod
    def _get_device_type(cls, request):
        """
        Determine device type from request
        """
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        if 'mobile' in user_agent and 'tablet' not in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            return 'tablet'
        else:
            return 'desktop' 