"""
Touch-friendly admin interface using Wagtail 7.0.2 mobile improvements
"""

from django.contrib.admin import AdminSite
from django.contrib.admin.sites import site
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from wagtail.admin.ui.components import Component
from wagtail.admin.views.pages.listing import PageListingTable
from wagtail.admin.widgets import Button
import json


class TouchFriendlyAdminSite(AdminSite):
    """
    Touch-friendly admin site with mobile optimizations
    """
    
    site_header = "MedGuard SA Mobile Admin"
    site_title = "MedGuard Mobile Admin"
    index_title = "Mobile Administration"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_touch_optimizations = True
    
    def get_app_list(self, request):
        """
        Get app list with touch-friendly modifications
        """
        app_list = super().get_app_list(request)
        
        if self.enable_touch_optimizations:
            app_list = self._optimize_for_touch(app_list)
        
        return app_list
    
    def _optimize_for_touch(self, app_list):
        """
        Optimize app list for touch devices
        """
        for app in app_list:
            # Increase touch targets
            app['touch_optimized'] = True
            
            for model in app['models']:
                model['touch_target_size'] = 'large'
                model['touch_friendly'] = True
        
        return app_list


class TouchFriendlyComponent(Component):
    """
    Base component for touch-friendly admin elements
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.touch_optimized = True
        self.min_touch_target = 44  # iOS minimum touch target size
    
    def get_css_classes(self):
        """
        Get CSS classes for touch optimization
        """
        classes = super().get_css_classes()
        if self.touch_optimized:
            classes.extend([
                'touch-optimized',
                'min-h-11',  # 44px minimum height
                'min-w-11',  # 44px minimum width
            ])
        return classes


class TouchFriendlyButton(Button):
    """
    Touch-friendly button component
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.touch_optimized = True
        self.min_touch_target = 44
    
    def render_html(self, parent_context=None):
        """
        Render touch-optimized button HTML
        """
        html = super().render_html(parent_context)
        
        # Add touch-friendly classes
        touch_classes = 'touch-optimized min-h-11 min-w-11 px-4 py-3 text-base'
        
        # Replace existing classes or add new ones
        if 'class="' in html:
            html = html.replace('class="', f'class="{touch_classes} ')
        else:
            html = html.replace('<button', f'<button class="{touch_classes}"')
        
        return mark_safe(html)


class TouchFriendlyPageListingTable(PageListingTable):
    """
    Touch-friendly page listing table
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.touch_optimized = True
    
    def get_table_classes(self):
        """
        Get touch-optimized table classes
        """
        classes = super().get_table_classes()
        classes.extend([
            'touch-optimized-table',
            'table-responsive',
        ])
        return classes
    
    def get_row_classes(self):
        """
        Get touch-optimized row classes
        """
        classes = super().get_row_classes()
        classes.extend([
            'touch-optimized-row',
            'min-h-12',  # 48px minimum row height
        ])
        return classes


class TouchFriendlyFormMixin:
    """
    Mixin for touch-friendly form fields
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.touch_optimized = True
    
    def get_field_classes(self):
        """
        Get touch-optimized field classes
        """
        classes = super().get_field_classes()
        classes.extend([
            'touch-optimized-field',
            'min-h-12',  # 48px minimum height
            'text-base',  # Larger text
            'px-3',      # More padding
            'py-2',      # More padding
        ])
        return classes


class MobileAdminCSS:
    """
    CSS for touch-friendly admin interface
    """
    
    @staticmethod
    def get_touch_optimized_css():
        """
        Get CSS for touch-friendly admin interface
        """
        css = """
        <style>
        /* Touch-friendly admin styles */
        .touch-optimized {
            min-height: 44px;
            min-width: 44px;
            touch-action: manipulation;
        }
        
        .touch-optimized-table {
            border-collapse: separate;
            border-spacing: 0;
        }
        
        .touch-optimized-table th,
        .touch-optimized-table td {
            padding: 12px 8px;
            min-height: 48px;
            vertical-align: middle;
        }
        
        .touch-optimized-table th {
            background-color: #f8f9fa;
            font-weight: 600;
            font-size: 14px;
        }
        
        .touch-optimized-row {
            min-height: 48px;
            transition: background-color 0.2s ease;
        }
        
        .touch-optimized-row:hover {
            background-color: #f8f9fa;
        }
        
        .touch-optimized-field {
            min-height: 48px;
            font-size: 16px;
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            transition: border-color 0.2s ease;
        }
        
        .touch-optimized-field:focus {
            border-color: #2563eb;
            outline: none;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .touch-optimized button {
            min-height: 44px;
            min-width: 44px;
            padding: 12px 16px;
            font-size: 16px;
            border-radius: 8px;
            border: none;
            background-color: #2563eb;
            color: white;
            cursor: pointer;
            transition: background-color 0.2s ease;
        }
        
        .touch-optimized button:hover {
            background-color: #1d4ed8;
        }
        
        .touch-optimized button:active {
            background-color: #1e40af;
            transform: translateY(1px);
        }
        
        .touch-optimized .btn-secondary {
            background-color: #6b7280;
        }
        
        .touch-optimized .btn-secondary:hover {
            background-color: #4b5563;
        }
        
        .touch-optimized .btn-danger {
            background-color: #dc2626;
        }
        
        .touch-optimized .btn-danger:hover {
            background-color: #b91c1c;
        }
        
        /* Mobile-specific optimizations */
        @media (max-width: 768px) {
            .touch-optimized-table {
                font-size: 14px;
            }
            
            .touch-optimized-table th,
            .touch-optimized-table td {
                padding: 8px 4px;
            }
            
            .touch-optimized-field {
                font-size: 16px; /* Prevent zoom on iOS */
                padding: 12px 12px;
            }
            
            .touch-optimized button {
                width: 100%;
                margin-bottom: 8px;
            }
        }
        
        /* Touch feedback */
        .touch-optimized * {
            -webkit-tap-highlight-color: rgba(37, 99, 235, 0.2);
        }
        
        /* Improved scrolling */
        .touch-optimized {
            -webkit-overflow-scrolling: touch;
            scroll-behavior: smooth;
        }
        
        /* Better focus indicators */
        .touch-optimized *:focus {
            outline: 2px solid #2563eb;
            outline-offset: 2px;
        }
        
        /* Reduced motion for accessibility */
        @media (prefers-reduced-motion: reduce) {
            .touch-optimized * {
                transition: none !important;
                animation: none !important;
            }
        }
        </style>
        """
        
        return format_html(css)


class MobileAdminJavaScript:
    """
    JavaScript for touch-friendly admin interface
    """
    
    @staticmethod
    def get_touch_optimized_js():
        """
        Get JavaScript for touch-friendly admin interface
        """
        js = """
        <script>
        // Touch-friendly admin JavaScript
        class TouchOptimizedAdmin {
            constructor() {
                this.init();
            }
            
            init() {
                this.setupTouchOptimizations();
                this.setupMobileNavigation();
                this.setupFormOptimizations();
                this.setupTableOptimizations();
            }
            
            setupTouchOptimizations() {
                // Add touch feedback to buttons
                document.querySelectorAll('.touch-optimized button').forEach(button => {
                    button.addEventListener('touchstart', this.handleTouchStart.bind(this));
                    button.addEventListener('touchend', this.handleTouchEnd.bind(this));
                });
                
                // Prevent double-tap zoom on buttons
                document.querySelectorAll('.touch-optimized button').forEach(button => {
                    button.addEventListener('touchend', (e) => {
                        e.preventDefault();
                        button.click();
                    });
                });
            }
            
            setupMobileNavigation() {
                // Mobile-friendly navigation
                const navToggle = document.querySelector('.nav-toggle');
                if (navToggle) {
                    navToggle.addEventListener('click', () => {
                        const nav = document.querySelector('.nav-menu');
                        nav.classList.toggle('nav-open');
                    });
                }
            }
            
            setupFormOptimizations() {
                // Auto-focus first field on mobile
                if (window.innerWidth <= 768) {
                    const firstField = document.querySelector('.touch-optimized-field');
                    if (firstField) {
                        setTimeout(() => firstField.focus(), 100);
                    }
                }
                
                // Better form validation feedback
                document.querySelectorAll('form').forEach(form => {
                    form.addEventListener('submit', this.handleFormSubmit.bind(this));
                });
            }
            
            setupTableOptimizations() {
                // Swipe gestures for tables
                const tables = document.querySelectorAll('.touch-optimized-table');
                tables.forEach(table => {
                    this.setupTableSwipe(table);
                });
            }
            
            setupTableSwipe(table) {
                let startX = 0;
                let startY = 0;
                
                table.addEventListener('touchstart', (e) => {
                    startX = e.touches[0].clientX;
                    startY = e.touches[0].clientY;
                });
                
                table.addEventListener('touchmove', (e) => {
                    if (!startX || !startY) return;
                    
                    const deltaX = e.touches[0].clientX - startX;
                    const deltaY = e.touches[0].clientY - startY;
                    
                    // Horizontal swipe for navigation
                    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                        if (deltaX > 0) {
                            // Swipe right - go back
                            if (window.history.length > 1) {
                                window.history.back();
                            }
                        } else {
                            // Swipe left - go forward
                            window.history.forward();
                        }
                    }
                });
            }
            
            handleTouchStart(e) {
                e.target.style.transform = 'scale(0.95)';
            }
            
            handleTouchEnd(e) {
                e.target.style.transform = 'scale(1)';
            }
            
            handleFormSubmit(e) {
                const form = e.target;
                const submitBtn = form.querySelector('button[type="submit"]');
                
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Submitting...';
                    
                    // Re-enable after 5 seconds as fallback
                    setTimeout(() => {
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Submit';
                    }, 5000);
                }
            }
        }
        
        // Initialize when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
            new TouchOptimizedAdmin();
        });
        </script>
        """
        
        return format_html(js)


class MobileAdminHooks:
    """
    Wagtail hooks for mobile admin optimizations
    """
    
    @staticmethod
    def construct_explorer_page_queryset(parent_page, pages, request):
        """
        Optimize page queryset for mobile admin
        """
        if hasattr(request, 'is_mobile_device') and request.is_mobile_device:
            # Limit results for mobile performance
            pages = pages[:50]
        
        return pages
    
    @staticmethod
    def construct_page_listing_buttons(buttons, page, page_perms, is_parent=False, context=None):
        """
        Add touch-friendly buttons to page listing
        """
        if hasattr(context, 'request') and hasattr(context.request, 'is_mobile_device'):
            if context.request.is_mobile_device:
                # Make buttons larger for touch
                for button in buttons:
                    button.classes = button.classes + ['touch-optimized', 'btn-lg']
        
        return buttons 