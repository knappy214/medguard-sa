"""
URL configuration for users app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from . import views
from .auth_views import (
    CustomTokenObtainPairView,
    LoginView,
    RegisterView,
    LogoutView,
    RefreshTokenView,
    ValidateTokenView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    health_check
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'profile', views.UserProfileViewSet, basename='user-profile')

# URL patterns
urlpatterns = [
    # Authentication endpoints
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', RefreshTokenView.as_view(), name='refresh'),
    path('auth/validate/', ValidateTokenView.as_view(), name='validate'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('auth/password-reset/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # JWT Authentication (alternative endpoints)
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Profile management
    path('', include(router.urls)),
    path('profile/summary/', views.profile_summary, name='profile-summary'),
    path('profile/delete-account/', views.delete_account, name='delete-account'),
    
    # Utility endpoints
    path('health/', health_check, name='health-check'),
    path('export/', views.export_profile_data, name='export-profile'),
    path('import/', views.import_profile_data, name='import-profile'),
]

# Include Wagtail API URLs (commented out for now)
# urlpatterns += [
#     path('api/v2/', include(views.api_router.urls)),
# ] 