"""
Views for users app.

This module contains API views for managing users and authentication.
"""

import logging
from django.shortcuts import render
from django.contrib.auth import authenticate
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django_filters.rest_framework import DjangoFilterBackend

from .models import User
from .serializers import UserSerializer, UserDetailSerializer, UserCreateSerializer
from security.jwt_auth import generate_secure_tokens, blacklist_token, get_token_generator
from security.audit import log_audit_event
from django.conf import settings

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_view(request):
    """Simple test view."""
    return Response({
        'message': 'Test view working',
        'status': 'success'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Handle user login with JWT token generation."""
    try:
        username_or_email = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')
        
        print(f"Login attempt for username/email: {username_or_email}")
        
        if not username_or_email or not password:
            return Response({
                'error': 'Username/Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to authenticate with username first
        user = authenticate(request, username=username_or_email, password=password)
        
        # If that fails, try to find user by email and authenticate
        if user is None:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        
        if user is None:
            print(f"Authentication failed for username/email: {username_or_email}")
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'error': 'Account is disabled'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        print(f"Authentication successful for user: {user.username}")
        
        # Log the user in
        from django.contrib.auth import login
        login(request, user)
        
        # Generate JWT tokens
        try:
            tokens = generate_secure_tokens(user, request)
            print(f"Tokens generated successfully for user: {user.username}")
            
            # Log audit event
            try:
                log_audit_event(
                    user=user,
                    action='login_success',
                    details={'ip_address': _get_client_ip(request)},
                    request=request
                )
            except Exception as audit_error:
                print(f"Audit logging failed: {audit_error}")
            
            return Response({
                'message': 'Login successful',
                'access_token': tokens['access'],
                'refresh_token': tokens['refresh'],
                'expires_in': tokens['expires_in'],
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'user_type': user.user_type,
                    'preferred_language': user.preferred_language or 'en',
                    'permissions': _get_user_permissions(user),
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'mfa_enabled': False
                }
            })
            
        except Exception as token_error:
            print(f"Token generation failed: {token_error}")
            # Fall back to basic response without tokens
            return Response({
                'message': 'Login successful (tokens unavailable)',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'user_type': user.user_type,
                    'preferred_language': user.preferred_language or 'en',
                    'permissions': ['view_own_profile'],
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'mfa_enabled': False
                }
            })
        
    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f'Login error: {e}')
        return Response({
            'error': 'Login failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """Handle token refresh."""
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
            
            # Generate new access token
            new_access_token = str(token.access_token)
            
            # Log successful refresh
            log_audit_event(
                user=user,
                action='token_refresh',
                description=f'Token refreshed for user: {user.username}',
                severity='low',
                request=request,
                metadata={'ip_address': _get_client_ip(request)}
            )
            
            return Response({
                'access': new_access_token,
                'tokens': {
                    'accessToken': new_access_token,
                    'refreshToken': refresh_token,
                    'expiresAt': _calculate_expires_at(new_access_token)
                }
            })
            
        except (InvalidToken, TokenError) as e:
            logger.warning(f'Token refresh failed: {e}')
            return Response({
                'error': 'Invalid refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        logger.error(f'Token refresh error: {e}')
        return Response({
            'error': 'Token refresh failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _calculate_expires_at(access_token):
    """Calculate token expiration timestamp."""
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError
    
    try:
        token = AccessToken(access_token)
        return int(token.current_time.timestamp() * 1000)  # Convert to milliseconds
    except TokenError:
        # Fallback to 15 minutes from now
        import time
        return int((time.time() + 15 * 60) * 1000)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """Handle user logout and token invalidation."""
    try:
        # Get authorization header (optional for logout)
        auth_header = request.headers.get('Authorization')
        token = None
        user = None
        
        if auth_header and auth_header.startswith('Bearer '):
            # Extract and validate token
            token = auth_header.split(' ')[1]
            try:
                # Blacklist the token if valid
                blacklist_token(token)
            except Exception as e:
                logger.warning(f'Failed to blacklist token: {e}')
            
            # Try to get user from token for logging
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                from rest_framework_simplejwt.exceptions import TokenError
                
                access_token = AccessToken(token)
                user_id = access_token.payload.get('user_id')
                if user_id:
                    user = User.objects.get(id=user_id, is_active=True)
            except (TokenError, User.DoesNotExist):
                pass  # Token is invalid, but we still allow logout
        
        # Get device ID for logging
        device_id = request.data.get('deviceId') or request.headers.get('X-Device-ID')
        
        # Log logout event (even without user for security tracking)
        log_audit_event(
            user=user,
            action='logout',
            description=f'User logout from device {device_id}',
            severity='low',
            request=request,
            metadata={
                'device_id': device_id,
                'ip_address': _get_client_ip(request),
                'token_provided': bool(token)
            }
        )
        
        return Response({
            'message': 'Successfully logged out'
        })
        
    except Exception as e:
        logger.error(f'Logout error: {e}')
        return Response({
            'error': 'Logout failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def validate_token_view(request):
    """Validate token and return current user information."""
    try:
        # Get authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({
                'error': 'No valid authorization header'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        # Validate token and get user
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        
        try:
            access_token = AccessToken(token)
            user_id = access_token.payload.get('user_id')
            
            if not user_id:
                raise TokenError('Invalid token payload')
            
            user = User.objects.get(id=user_id, is_active=True)
            
            # Return user information
            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'user_type': user.user_type,
                    'preferred_language': user.preferred_language,
                    'permissions': _get_user_permissions(user),
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'mfa_enabled': user.mfa_enabled if hasattr(user, 'mfa_enabled') else False
                }
            })
            
        except (TokenError, User.DoesNotExist):
            return Response({
                'error': 'Invalid or expired token'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        logger.error(f'Token validation error: {e}')
        return Response({
            'error': 'Token validation failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """Handle user registration with enhanced validation."""
    try:
        # Extract registration data
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        password_confirm = request.data.get('password_confirm')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        user_type = request.data.get('user_type', User.UserType.PATIENT)
        
        # Validate required fields
        if not all([username, email, password, password_confirm]):
            return Response({
                'error': 'All required fields must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate password confirmation
        if password != password_confirm:
            return Response({
                'error': 'Passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            return Response({
                'error': 'Username already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'Email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type,
                is_active=True  # Users are active by default
            )
            
            # Log the user in
            from django.contrib.auth import login
            login(request, user)
            
            # Generate JWT tokens
            tokens = generate_secure_tokens(user, request)
            
            # Log audit event
            log_audit_event(
                user=user,
                action='user_registration',
                description=f'New user registration: {user.username}',
                severity='low',
                request=request
            )
            
            return Response({
                'message': 'Registration successful',
                'access_token': tokens['access'],
                'refresh_token': tokens['refresh'],
                'expires_in': tokens['expires_in'],
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'user_type': user.user_type,
                    'preferred_language': user.preferred_language or 'en',
                    'permissions': _get_user_permissions(user),
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'mfa_enabled': False
                }
            })
            
        except Exception as create_error:
            logger.error(f'User creation error: {create_error}')
            return Response({
                'error': 'Failed to create user account'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f'Registration error: {e}')
        return Response({
            'error': 'Registration failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    """Handle password reset request."""
    try:
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email address is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists (but don't reveal if they do)
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            # Return success even if user doesn't exist to prevent enumeration
            return Response({
                'message': 'If an account with this email exists, a password reset link has been sent.'
            })
        
        # Generate password reset token
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create password reset URL
        reset_url = f"{request.scheme}://{request.get_host()}/api/users/password-reset-confirm/{uid}/{token}/"
        
        # Send email (in development, just log it)
        if settings.DEBUG:
            logger.info(f'Password reset link for {email}: {reset_url}')
        
        # Log audit event
        log_audit_event(
            user=user,
            action='password_reset_requested',
            description=f'Password reset requested for {user.email}',
            severity='medium',
            request=request
        )
        
        return Response({
            'message': 'If an account with this email exists, a password reset link has been sent.'
        })
        
    except Exception as e:
        logger.error(f'Password reset request error: {e}')
        return Response({
            'error': 'Password reset request failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request, uidb64, token):
    """Handle password reset confirmation."""
    try:
        new_password = request.data.get('new_password')
        new_password_confirm = request.data.get('new_password_confirm')
        
        if not all([new_password, new_password_confirm]):
            return Response({
                'error': 'New password and confirmation are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != new_password_confirm:
            return Response({
                'error': 'Passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Decode user ID
        from django.utils.http import urlsafe_base64_decode
        from django.utils.encoding import force_str
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Invalid password reset link'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate token
        from django.contrib.auth.tokens import default_token_generator
        
        if not default_token_generator.check_token(user, token):
            return Response({
                'error': 'Invalid or expired password reset link'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Log audit event
        log_audit_event(
            user=user,
            action='password_reset_completed',
            description=f'Password reset completed for {user.email}',
            severity='medium',
            request=request
        )
        
        return Response({
            'message': 'Password has been reset successfully'
        })
        
    except Exception as e:
        logger.error(f'Password reset confirm error: {e}')
        return Response({
            'error': 'Password reset failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """Handle password change for authenticated users."""
    try:
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        new_password_confirm = request.data.get('new_password_confirm')
        
        if not all([old_password, new_password, new_password_confirm]):
            return Response({
                'error': 'All password fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != new_password_confirm:
            return Response({
                'error': 'New passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify old password
        if not request.user.check_password(old_password):
            return Response({
                'error': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        request.user.set_password(new_password)
        request.user.save()
        
        # Log audit event
        log_audit_event(
            user=request.user,
            action='password_changed',
            description=f'Password changed for {request.user.username}',
            severity='medium',
            request=request
        )
        
        return Response({
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        logger.error(f'Password change error: {e}')
        return Response({
            'error': 'Password change failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """Handle user profile management."""
    if request.method == 'GET':
        # Return current user profile
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'user_type': user.user_type,
            'preferred_language': user.preferred_language or 'en',
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_active': user.is_active,
            'permissions': _get_user_permissions(user)
        })
    
    elif request.method == 'PUT':
        # Update user profile
        try:
            user = request.user
            
            # Update allowed fields
            if 'first_name' in request.data:
                user.first_name = request.data['first_name']
            if 'last_name' in request.data:
                user.last_name = request.data['last_name']
            if 'preferred_language' in request.data:
                user.preferred_language = request.data['preferred_language']
            
            # Validate email if provided
            if 'email' in request.data:
                new_email = request.data['email']
                if new_email != user.email:
                    # Check if email is already taken
                    if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                        return Response({
                            'error': 'Email address is already in use'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    user.email = new_email
            
            user.save()
            
            # Log audit event
            log_audit_event(
                user=user,
                action='profile_updated',
                description=f'Profile updated for {user.username}',
                severity='low',
                request=request
            )
            
            return Response({
                'message': 'Profile updated successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'user_type': user.user_type,
                    'preferred_language': user.preferred_language or 'en',
                    'permissions': _get_user_permissions(user)
                }
            })
            
        except Exception as e:
            logger.error(f'Profile update error: {e}')
            return Response({
                'error': 'Profile update failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_permissions_view(request):
    """Get current user's permissions."""
    try:
        user = request.user
        permissions = _get_user_permissions(user)
        
        return Response({
            'permissions': permissions,
            'user_type': user.user_type,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser
        })
        
    except Exception as e:
        logger.error(f'Permissions error: {e}')
        return Response({
            'error': 'Failed to get permissions'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_user_permissions(user):
    """Get user permissions based on user type."""
    permissions = []
    
    # Base permissions for all authenticated users
    permissions.extend([
        'view_own_profile',
        'edit_own_profile',
        'view_medications',
        'view_schedules'
    ])
    
    # User type specific permissions
    if user.user_type == 'PATIENT':
        permissions.extend([
            'manage_own_medications',
            'view_own_schedules',
            'mark_medications_taken'
        ])
    elif user.user_type == 'CAREGIVER':
        permissions.extend([
            'manage_patient_medications',
            'view_patient_schedules',
            'mark_patient_medications_taken',
            'view_patient_profiles'
        ])
    elif user.user_type == 'HEALTHCARE_PROVIDER':
        permissions.extend([
            'manage_all_medications',
            'manage_all_schedules',
            'view_all_profiles',
            'manage_users',
            'view_analytics',
            'manage_notifications'
        ])
    
    return permissions


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
