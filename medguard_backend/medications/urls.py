from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API router for medications
router = DefaultRouter()
router.register(r'medications', views.MedicationViewSet)
router.register(r'schedules', views.MedicationScheduleViewSet, basename='medication-schedule')
router.register(r'logs', views.MedicationLogViewSet, basename='medication-log')
router.register(r'alerts', views.StockAlertViewSet)
router.register(r'pharmacy-integrations', views.PharmacyIntegrationViewSet)
router.register(r'stock-analytics', views.StockAnalyticsViewSet, basename='stock-analytics')

# Combined URL patterns that work for both API and regular views
urlpatterns = [
    # API endpoints (for /api/ prefix)
    path('', include(router.urls)),
    
    # Test and utility views (for /medications/ prefix)
    path('test-i18n/', views.test_i18n, name='test_i18n'),
    path('working-i18n-test/', views.working_i18n_test, name='working_i18n_test'),
    path('api-i18n-test/', views.api_i18n_test, name='api_i18n_test'),
    path('set-language/', views.set_language_ajax, name='set_language_ajax'),
] 