"""
Mobile-optimized page templates using Wagtail 7.0.2 template improvements
"""

from django.template import Context, Template
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from wagtail.models import Page
from wagtail.rich_text import expand_db_html
import json


class MobileTemplateRenderer:
    """
    Mobile-optimized template renderer with Wagtail 7.0.2 improvements
    """
    
    # Mobile-specific template overrides
    MOBILE_TEMPLATES = {
        'home': 'mobile/home.html',
        'medication': 'mobile/medication.html',
        'prescription': 'mobile/prescription.html',
        'search': 'mobile/search.html',
        'admin': 'mobile/admin.html',
    }
    
    @classmethod
    def get_mobile_template(cls, page_type, is_mobile=False):
        """
        Get mobile-optimized template for page type
        """
        if not is_mobile:
            return None
            
        return cls.MOBILE_TEMPLATES.get(page_type)
    
    @classmethod
    def render_mobile_page(cls, page, context=None, is_mobile=False):
        """
        Render page with mobile-optimized template
        """
        if not is_mobile:
            return None
            
        # Determine page type
        page_type = cls._get_page_type(page)
        template_name = cls.get_mobile_template(page_type, is_mobile)
        
        if not template_name:
            return None
            
        try:
            template = get_template(template_name)
            context = context or {}
            context.update({
                'page': page,
                'is_mobile': True,
                'mobile_optimized': True,
            })
            
            return template.render(context)
            
        except Exception as e:
            # Fallback to default template
            return None
    
    @classmethod
    def _get_page_type(cls, page):
        """
        Determine page type for template selection
        """
        if hasattr(page, 'content_type'):
            model_name = page.content_type.model
            if 'home' in model_name.lower():
                return 'home'
            elif 'medication' in model_name.lower():
                return 'medication'
            elif 'prescription' in model_name.lower():
                return 'prescription'
            elif 'search' in model_name.lower():
                return 'search'
        
        return 'default'


class MobileTemplateTags:
    """
    Mobile-specific template tags and filters
    """
    
    @staticmethod
    def mobile_breakpoint(breakpoint):
        """
        Template filter for mobile breakpoint classes
        """
        breakpoint_classes = {
            'xs': 'col-12',
            'sm': 'col-sm-12',
            'md': 'col-md-12',
            'lg': 'col-lg-12',
            'xl': 'col-xl-12',
        }
        return breakpoint_classes.get(breakpoint, 'col-12')
    
    @staticmethod
    def mobile_font_size(size):
        """
        Template filter for mobile font sizes
        """
        font_sizes = {
            'xs': 'text-xs',
            'sm': 'text-sm',
            'base': 'text-base',
            'lg': 'text-lg',
            'xl': 'text-xl',
            '2xl': 'text-2xl',
        }
        return font_sizes.get(size, 'text-base')
    
    @staticmethod
    def mobile_spacing(spacing):
        """
        Template filter for mobile spacing
        """
        spacing_classes = {
            'xs': 'p-2',
            'sm': 'p-3',
            'md': 'p-4',
            'lg': 'p-5',
            'xl': 'p-6',
        }
        return spacing_classes.get(spacing, 'p-3')


class MobileTemplateContext:
    """
    Mobile-specific template context processor
    """
    
    @staticmethod
    def mobile_context(request):
        """
        Add mobile-specific context to all templates
        """
        context = {}
        
        if hasattr(request, 'is_mobile_device') and request.is_mobile_device:
            context.update({
                'is_mobile': True,
                'mobile_breakpoints': {
                    'xs': 320,
                    'sm': 576,
                    'md': 768,
                    'lg': 992,
                    'xl': 1200,
                },
                'mobile_optimizations': {
                    'lazy_loading': True,
                    'progressive_loading': True,
                    'touch_friendly': True,
                    'reduced_motion': True,
                }
            })
        
        return context


class MobileTemplateBlocks:
    """
    Mobile-optimized StreamField blocks
    """
    
    @staticmethod
    def mobile_hero_block(context):
        """
        Mobile-optimized hero block template
        """
        template_str = """
        <div class="mobile-hero bg-primary text-white p-4 rounded-lg mb-4">
            <div class="text-center">
                <h1 class="text-2xl font-bold mb-2">{{ block.value.title }}</h1>
                <p class="text-sm mb-3">{{ block.value.subtitle }}</p>
                {% if block.value.cta_text %}
                <button class="btn btn-secondary btn-sm">{{ block.value.cta_text }}</button>
                {% endif %}
            </div>
        </div>
        """
        return Template(template_str).render(context)
    
    @staticmethod
    def mobile_card_block(context):
        """
        Mobile-optimized card block template
        """
        template_str = """
        <div class="mobile-card bg-white border rounded-lg p-3 mb-3 shadow-sm">
            {% if block.value.image %}
            <div class="mb-2">
                <img src="{{ block.value.image.url }}" 
                     alt="{{ block.value.title }}"
                     class="w-full h-32 object-cover rounded">
            </div>
            {% endif %}
            <h3 class="text-lg font-semibold mb-1">{{ block.value.title }}</h3>
            <p class="text-sm text-gray-600">{{ block.value.description }}</p>
        </div>
        """
        return Template(template_str).render(context)
    
    @staticmethod
    def mobile_list_block(context):
        """
        Mobile-optimized list block template
        """
        template_str = """
        <div class="mobile-list bg-white border rounded-lg p-3 mb-3">
            <h3 class="text-lg font-semibold mb-2">{{ block.value.title }}</h3>
            <ul class="space-y-2">
                {% for item in block.value.items %}
                <li class="flex items-center p-2 bg-gray-50 rounded">
                    <span class="w-2 h-2 bg-primary rounded-full mr-2"></span>
                    <span class="text-sm">{{ item }}</span>
                </li>
                {% endfor %}
            </ul>
        </div>
        """
        return Template(template_str).render(context)


class MobileTemplateOptimizer:
    """
    Template optimization for mobile devices
    """
    
    @staticmethod
    def optimize_html_for_mobile(html_content):
        """
        Optimize HTML content for mobile devices
        """
        if not html_content:
            return html_content
        
        # Add mobile-specific classes and attributes
        optimizations = [
            ('<img', '<img loading="lazy" decoding="async"'),
            ('<video', '<video preload="none"'),
            ('<link rel="stylesheet"', '<link rel="stylesheet" media="all"'),
        ]
        
        for old, new in optimizations:
            html_content = html_content.replace(old, new)
        
        return html_content
    
    @staticmethod
    def add_mobile_meta_tags(html_content):
        """
        Add mobile-specific meta tags
        """
        mobile_meta = """
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="theme-color" content="#2563EB">
        """
        
        # Insert after <head> tag
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', f'<head>{mobile_meta}')
        
        return html_content 