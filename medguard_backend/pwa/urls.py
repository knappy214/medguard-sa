"""
PWA URL Configuration
"""

from django.urls import path
from . import views

app_name = 'pwa'

urlpatterns = [
    # App Shell
    path('', views.AppShellView.as_view(), name='app_shell'),
    
    # PWA Core Files
    path('manifest/', views.pwa_manifest_view, name='manifest'),
    path('service-worker.js', views.service_worker_view, name='service_worker'),
    path('offline/', views.offline_page_view, name='offline_page'),
    
    # API Endpoints
    path('api/push-subscription/', views.push_subscription_view, name='push_subscription'),
    path('api/reminder/<int:reminder_id>/action/', views.reminder_action_view, name='reminder_action'),
    path('api/offline-data/', views.offline_data_view, name='offline_data'),
    path('api/emergency-contacts/', views.emergency_contacts_view, name='emergency_contacts'),
    path('api/settings/', views.pwa_settings_view, name='settings'),
    path('api/installation/', views.pwa_installation_view, name='installation'),
    path('api/medication-tracking/', views.medication_tracking_view, name='medication_tracking'),
    path('api/medications/', views.medications_view, name='medications'),
    
    # Performance Monitoring
    path('api/performance/report/', views.performance_report_view, name='performance_report'),
    path('api/performance/pwa-metrics/', views.pwa_metrics_view, name='pwa_metrics'),
    path('api/performance/optimization/', views.performance_optimization_view, name='performance_optimization'),
    
    # Biometric Authentication
    path('api/biometric/challenge/', views.biometric_challenge_view, name='biometric_challenge'),
    path('api/biometric/register/', views.biometric_register_view, name='biometric_register'),
    path('api/biometric/authenticate/', views.biometric_authenticate_view, name='biometric_authenticate'),
    
    # Secure Medical Data
    path('api/secure-medical-data/<str:data_type>/<int:data_id>/', views.secure_medical_data_view, name='secure_medical_data'),
    
    # Cache Management
    path('api/clear-cache/', views.clear_cache_view, name='clear_cache'),
    path('api/cache-status/', views.cache_status_view, name='cache_status'),
] 