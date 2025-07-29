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
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='auth_login'),
    path('auth/refresh/', views.CustomTokenRefreshView.as_view(), name='auth_refresh'),
    path('auth/logout/', views.logout_view, name='auth_logout'),
    
    # API endpoints
    path('', include(router.urls)),
] 