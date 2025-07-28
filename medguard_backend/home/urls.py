"""
URL patterns for the home app.
"""

from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('i18n-test/', views.i18n_test_view, name='i18n_test'),
] 