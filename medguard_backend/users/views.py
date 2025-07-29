"""
Views for users app.

This module contains API views for managing users and authentication.
"""

import logging
from django.shortcuts import render
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django_filters.rest_framework import DjangoFilterBackend

from .models import User
from .serializers import UserSerializer, UserDetailSerializer, UserCreateSerializer
from security.jwt_auth import generate_secure_tokens, blacklist_token, get_token_generator
from security.audit import log_audit_event

logger = logging.getLogger(__name__)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view with device validation and security checks.
    """
    
    def post(self, request, *args, **kwargs):
        """Handle login request with device validation."""
        try:
            # Get device fingerprint from request
            device_fingerprint = self._get_device_fingerprint(request)
            
            # Authenticate user
            username = request.data.get('username')
            password = request.data.get('password')
            
            if not username or not password:
                return Response({
                    'error': 'Username and password are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = authenticate(username=username, password=password)
            
            if not user:
                # Log failed login attempt
                log_audit_event(
                    user=None,
                    action='login_failed',
                    description=f'Failed login attempt for username: {username}',
                    severity='medium',
                    request=request,
                    metadata={'username': username, 'ip_address': self._get_client_ip(request)}
                )
                
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if not user.is_active:
                return Response({
                    'error': 'Account is disabled'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Generate secure tokens with device validation
            tokens = generate_secure_tokens(user, request)
            
            # Log successful login
            log_audit_event(
                user=user,
                action='login',
                description=f'Successful login for user: {user.username}',
                severity='low',
                request=request,
                metadata={
                    'device_fingerprint': device_fingerprint,
                    'ip_address': self._get_client_ip(request)
                }
            )
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            return Response({
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'user_type': user.user_type,
                    'preferred_language': user.preferred_language,
                }
            })
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response({
                'error': 'Authentication failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_device_fingerprint(self, request):
        """Extract device fingerprint from request headers."""
        # Get device fingerprint from custom header
        device_fingerprint = request.META.get('HTTP_X_DEVICE_FINGERPRINT')
        
        if not device_fingerprint:
            # Generate a basic fingerprint from user agent and IP
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = self._get_client_ip(request)
            device_fingerprint = f"{ip_address}:{hash(user_agent) % 1000000}"
        
        return device_fingerprint
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view with security checks.
    """
    
    def post(self, request, *args, **kwargs):
        """Handle token refresh with security validation."""
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response({
                    'error': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate refresh token
            try:
                token = RefreshToken(refresh_token)
                user_id = token.payload.get('user_id')
                
                if not user_id:
                    raise InvalidToken('Invalid token payload')
                
                # Get user
                try:
                    user = User.objects.get(id=user_id, is_active=True)
                except User.DoesNotExist:
                    raise InvalidToken('User not found or inactive')
                
                # Validate device fingerprint if present
                device_fingerprint = self._get_device_fingerprint(request)
                token_fingerprint = token.payload.get('device_fingerprint')
                
                if token_fingerprint and device_fingerprint != token_fingerprint:
                    # Log potential security issue
                    log_audit_event(
                        user=user,
                        action='token_refresh_failed',
                        description='Device fingerprint mismatch during token refresh',
                        severity='high',
                        request=request,
                        metadata={
                            'expected_fingerprint': token_fingerprint,
                            'received_fingerprint': device_fingerprint,
                            'ip_address': self._get_client_ip(request)
                        }
                    )
                    
                    return Response({
                        'error': 'Invalid device fingerprint'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                # Generate new access token
                new_access_token = token.access_token
                
                # Log successful refresh
                log_audit_event(
                    user=user,
                    action='token_refresh',
                    description=f'Token refreshed for user: {user.username}',
                    severity='low',
                    request=request,
                    metadata={
                        'device_fingerprint': device_fingerprint,
                        'ip_address': self._get_client_ip(request)
                    }
                )
                
                return Response({
                    'access': str(new_access_token)
                })
                
            except (InvalidToken, TokenError) as e:
                return Response({
                    'error': 'Invalid refresh token'
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return Response({
                'error': 'Token refresh failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_device_fingerprint(self, request):
        """Extract device fingerprint from request headers."""
        device_fingerprint = request.META.get('HTTP_X_DEVICE_FINGERPRINT')
        
        if not device_fingerprint:
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = self._get_client_ip(request)
            device_fingerprint = f"{ip_address}:{hash(user_agent) % 1000000}"
        
        return device_fingerprint
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """
    Logout view to blacklist refresh token.
    """
    try:
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Blacklist the refresh token
        success = blacklist_token(refresh_token, request.user if request.user.is_authenticated else None)
        
        if success:
            # Log logout
            if request.user.is_authenticated:
                log_audit_event(
                    user=request.user,
                    action='logout',
                    description=f'User logged out: {request.user.username}',
                    severity='low',
                    request=request,
                    metadata={'ip_address': _get_client_ip(request)}
                )
            
            return Response({
                'message': 'Successfully logged out'
            })
        else:
            return Response({
                'error': 'Invalid refresh token'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response({
            'error': 'Logout failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


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
