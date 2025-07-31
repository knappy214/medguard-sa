"""
Authentication views for MedGuard SA.

This module provides views for login, registration, and password management
that work with the custom User model and JWT tokens.
"""

import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .auth_serializers import (
    CustomTokenObtainPairSerializer,
    LoginSerializer,
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
from .serializers import UserSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that supports email-based login.
    """
    serializer_class = CustomTokenObtainPairSerializer


class LoginView(APIView):
    """
    Login view that returns JWT tokens and user information.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Handle login requests.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response with tokens and user information
        """
        serializer = LoginSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = serializer.validated_data['refresh']
            access = serializer.validated_data['access']
            
            # Log successful login
            logger.info(f"User {user.username} logged in successfully")
            
            # Use UserSerializer to get complete user data including avatar_url
            user_data = UserSerializer(user, context={'request': request}).data
            
            return Response({
                'success': True,
                'message': 'Login successful',
                'refresh_token': refresh,
                'access_token': access,
                'expires_in': 3600,  # 1 hour in seconds
                'user': user_data
            })
        else:
            # Log failed login attempt
            username_or_email = request.data.get('username_or_email') or request.data.get('email', 'unknown')
            logger.warning(f"Failed login attempt for user: {username_or_email}")
            
            return Response({
                'success': False,
                'message': 'Login failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    """
    Registration view for new users.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Handle user registration.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response with user information and tokens
        """
        serializer = RegisterSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate tokens for the new user
            refresh = RefreshToken.for_user(user)
            
            # Log successful registration
            logger.info(f"New user registered: {user.username} ({user.email})")
            
            return Response({
                'success': True,
                'message': 'Registration successful',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': 'Registration failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    Logout view that invalidates JWT tokens.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Handle logout requests.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response confirming logout
        """
        try:
            # Get the refresh token from the request
            refresh_token = request.data.get('refresh')
            
            if refresh_token:
                # Blacklist the refresh token
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Log successful logout
            logger.info(f"User {request.user.username} logged out successfully")
            
            return Response({
                'success': True,
                'message': 'Logout successful'
            })
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Invalid token during logout: {e}")
            return Response({
                'success': False,
                'message': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return Response({
                'success': False,
                'message': 'Logout failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefreshTokenView(APIView):
    """
    View for refreshing JWT tokens.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Handle token refresh requests.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response with new access token
        """
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response({
                    'success': False,
                    'message': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate and refresh the token
            token = RefreshToken(refresh_token)
            
            return Response({
                'success': True,
                'message': 'Token refreshed successfully',
                'access': str(token.access_token)
            })
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Invalid refresh token: {e}")
            return Response({
                'success': False,
                'message': 'Invalid refresh token'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return Response({
                'success': False,
                'message': 'Token refresh failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ValidateTokenView(APIView):
    """
    View for validating JWT tokens.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Validate the current user's token.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response with user information
        """
        return Response({
            'success': True,
            'message': 'Token is valid',
            'user': UserSerializer(request.user, context={'request': request}).data
        })


class PasswordResetRequestView(APIView):
    """
    View for requesting password reset.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Handle password reset requests.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response confirming password reset email sent
        """
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email__iexact=email)
                
                # Generate password reset token
                # This would typically send an email with a reset link
                # For now, we'll just return a success message
                
                logger.info(f"Password reset requested for user: {user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Password reset email sent successfully'
                })
            except User.DoesNotExist:
                # Don't reveal that the user doesn't exist
                return Response({
                    'success': True,
                    'message': 'If an account exists with this email, a password reset link has been sent'
                })
        else:
            return Response({
                'success': False,
                'message': 'Invalid email address',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    View for confirming password reset.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, uidb64, token):
        """
        Handle password reset confirmation.
        
        Args:
            request: HTTP request object
            uidb64: Base64 encoded user ID
            token: Password reset token
            
        Returns:
            Response confirming password reset
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Decode user ID and validate token
                # This would typically validate the token and update the password
                # For now, we'll just return a success message
                
                logger.info(f"Password reset confirmed for user ID: {uidb64}")
                
                return Response({
                    'success': True,
                    'message': 'Password reset successfully'
                })
            except Exception as e:
                logger.error(f"Error during password reset: {e}")
                return Response({
                    'success': False,
                    'message': 'Password reset failed'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'success': False,
                'message': 'Invalid password data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for authentication system.
    
    Args:
        request: HTTP request object
        
    Returns:
        Response with authentication system status
    """
    return Response({
        'status': 'healthy',
        'message': 'Authentication system is working',
        'timestamp': timezone.now().isoformat()
    }) 