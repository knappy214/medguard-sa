"""
Views for Drug Interactions Plugin
Admin views for drug interaction checking and management.
"""
import json
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import TemplateView
from wagtail.admin import messages as wagtail_messages

from .models import DrugInteraction, InteractionCheck, DrugAllergy
from .services import DrugInteractionService


class DrugInteractionsDashboardView(PermissionRequiredMixin, TemplateView):
    """Main dashboard for drug interactions system."""
    
    template_name = "wagtail_drug_interactions/dashboard.html"
    permission_required = "wagtail_drug_interactions.view_druginteraction"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        service = DrugInteractionService()
        stats = service.get_interaction_statistics()
        
        # Recent interaction checks
        recent_checks = InteractionCheck.objects.select_related(
            'checked_by', 'patient'
        ).order_by('-created_at')[:10]
        
        context.update({
            'title': _("Drug Interactions Dashboard"),
            'stats': stats,
            'recent_checks': recent_checks,
        })
        
        return context


class InteractionCheckerView(PermissionRequiredMixin, View):
    """View for checking drug interactions."""
    
    permission_required = "wagtail_drug_interactions.perform_interaction_checks"
    
    def get(self, request):
        """Display interaction checker form."""
        context = {
            'title': _("Drug Interaction Checker"),
        }
        return render(request, 'wagtail_drug_interactions/checker.html', context)
    
    def post(self, request):
        """Handle interaction check request."""
        try:
            data = json.loads(request.body)
            medications = data.get('medications', [])
            patient_id = data.get('patient_id')
            
            if not medications:
                return JsonResponse({
                    'success': False,
                    'error': _("No medications provided")
                }, status=400)
            
            service = DrugInteractionService()
            results = service.check_drug_interactions(
                medications=medications,
                patient_id=patient_id,
                checked_by_id=request.user.id,
                include_allergies=True
            )
            
            return JsonResponse(results)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': _("Invalid JSON data")
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class PatientAllergiesView(PermissionRequiredMixin, TemplateView):
    """View for managing patient drug allergies."""
    
    template_name = "wagtail_drug_interactions/patient_allergies.html"
    permission_required = "wagtail_drug_interactions.view_patient_allergies"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        patient_id = kwargs.get('patient_id')
        
        # Get patient allergies
        allergies = DrugAllergy.objects.filter(
            patient_id=patient_id,
            is_active=True
        ).order_by('-severity')
        
        # Get interaction history
        service = DrugInteractionService()
        history = service.get_patient_interaction_history(patient_id)
        
        context.update({
            'title': _("Patient Drug Allergies"),
            'patient_id': patient_id,
            'allergies': allergies,
            'interaction_history': history,
        })
        
        return context


class InteractionDatabaseView(PermissionRequiredMixin, TemplateView):
    """View for managing the interaction database."""
    
    template_name = "wagtail_drug_interactions/database.html"
    permission_required = "wagtail_drug_interactions.manage_interaction_database"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get interaction statistics by severity
        interactions = DrugInteraction.objects.filter(is_active=True)
        
        context.update({
            'title': _("Interaction Database Management"),
            'total_interactions': interactions.count(),
            'interactions_by_severity': {
                'contraindicated': interactions.filter(severity='contraindicated').count(),
                'major': interactions.filter(severity='major').count(),
                'moderate': interactions.filter(severity='moderate').count(),
                'minor': interactions.filter(severity='minor').count(),
            }
        })
        
        return context


class DrugInteractionsAPIView(PermissionRequiredMixin, View):
    """API endpoint for drug interactions functionality."""
    
    permission_required = "wagtail_drug_interactions.view_druginteraction"
    
    def post(self, request):
        """Handle API requests for drug interaction checking."""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'check_interactions':
                return self._check_interactions(request, data)
            elif action == 'add_allergy':
                return self._add_allergy(request, data)
            elif action == 'validate_interaction':
                return self._validate_interaction(request, data)
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    def _check_interactions(self, request, data):
        """Check drug interactions via API."""
        try:
            medications = data.get('medications', [])
            patient_id = data.get('patient_id')
            
            service = DrugInteractionService()
            results = service.check_drug_interactions(
                medications=medications,
                patient_id=patient_id,
                checked_by_id=request.user.id
            )
            
            return JsonResponse(results)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _add_allergy(self, request, data):
        """Add drug allergy via API."""
        try:
            if not request.user.has_perm('wagtail_drug_interactions.add_drugallergy'):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                }, status=403)
            
            patient_id = data.get('patient_id')
            allergy_data = data.get('allergy_data', {})
            
            service = DrugInteractionService()
            allergy = service.add_drug_allergy(
                patient_id=patient_id,
                allergy_data=allergy_data,
                reported_by_id=request.user.id
            )
            
            return JsonResponse({
                'success': True,
                'allergy_id': str(allergy.id),
                'message': _("Drug allergy added successfully")
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _validate_interaction(self, request, data):
        """Validate interaction data via API."""
        try:
            interaction_data = data.get('interaction_data', {})
            
            service = DrugInteractionService()
            is_valid, errors = service.validate_interaction_data(interaction_data)
            
            return JsonResponse({
                'success': True,
                'is_valid': is_valid,
                'errors': errors
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
