"""
URL configuration for users app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'users'

# API router for users
router = DefaultRouter()
router.register(r'users', views.UserViewSet)

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', views.login_view, name='auth_login'),
    path('auth/register/', views.register_view, name='auth_register'),
    path('auth/refresh/', views.refresh_token_view, name='auth_refresh'),
    path('auth/logout/', views.logout_view, name='auth_logout'),
    path('auth/validate/', views.validate_token_view, name='auth_validate'),
    path('auth/change-password/', views.change_password_view, name='auth_change_password'),
    
    # Password reset endpoints
    path('password-reset-request/', views.password_reset_request_view, name='password_reset_request'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    
    # Profile management endpoints
    path('profile/', views.profile_view, name='profile'),
    path('permissions/', views.user_permissions_view, name='permissions'),
    
    # API endpoints
    path('', include(router.urls)),
] 