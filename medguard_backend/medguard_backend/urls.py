"""
URL configuration for medguard_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

# Admin site customization
admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.site_title = settings.ADMIN_SITE_TITLE
admin.site.index_title = settings.ADMIN_INDEX_TITLE

# Non-translatable URLs (admin, API, etc.)
urlpatterns = [
    # Internationalization
    path('i18n/', include('django.conf.urls.i18n')),
    
    # Django admin (with custom URL)
    path('django-admin/', admin.site.urls),
    
    # Wagtail admin (without language prefix for admin access)
    path('admin/', include('wagtail.admin.urls')),
    
    # API endpoints (without language prefix) - using distinct namespaces
    path('api/', include(('medications.urls', 'api_medications'), namespace='api_medications')),
    path('api/', include(('notifications.urls', 'api_notifications'), namespace='api_notifications')),
    path('api/', include(('users.urls', 'api_users'), namespace='api_users')),
]

# Translatable URLs (with language prefix)
urlpatterns += i18n_patterns(
    # Search functionality
    path('search/', include('search.urls')),
    
    # Frontend medications views (with language prefix) - using distinct namespace
    path('medications/', include(('medications.urls', 'frontend_medications'), namespace='frontend_medications')),
    
    # Home app views (including i18n test)
    path('home/', include('home.urls')),
    
    # Wagtail pages (including home, medications, notifications)
    path('', include('wagtail.urls')),
    
    prefix_default_language=False,
)

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar URLs
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
