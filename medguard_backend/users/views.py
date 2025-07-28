"""
Views for users app.

This module contains API views for managing users.
"""

from django.shortcuts import render
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import User
from .serializers import UserSerializer, UserDetailSerializer, UserCreateSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users.
    
    Provides CRUD operations for user management with filtering and search capabilities.
    """
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user_type', 'gender', 'preferred_language', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'medical_record_number']
    ordering_fields = ['username', 'first_name', 'last_name', 'email', 'created_at']
    ordering = ['username']
    
    def get_queryset(self):
        """Filter queryset based on user permissions and request parameters."""
        queryset = super().get_queryset()
        
        # Filter by user type if requested
        user_type = self.request.query_params.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        # Filter by active users if requested
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def get_serializer_class(self):
        """Use appropriate serializer based on action."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a user account."""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'status': 'user activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user account."""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'status': 'user deactivated'})
    
    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Get detailed profile information for a user."""
        user = self.get_object()
        serializer = UserDetailSerializer(user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile information."""
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def patients(self, request):
        """Get all patient users."""
        patients = User.objects.filter(user_type=User.UserType.PATIENT)
        serializer = UserSerializer(patients, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def caregivers(self, request):
        """Get all caregiver users."""
        caregivers = User.objects.filter(user_type=User.UserType.CAREGIVER)
        serializer = UserSerializer(caregivers, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def healthcare_providers(self, request):
        """Get all healthcare provider users."""
        providers = User.objects.filter(user_type=User.UserType.HEALTHCARE_PROVIDER)
        serializer = UserSerializer(providers, many=True, context={'request': request})
        return Response(serializer.data)
