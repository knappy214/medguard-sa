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
    # API endpoints
    path('', include(router.urls)),
] 