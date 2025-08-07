"""
Views for Medical Forms Plugin
Admin views for medical form building and submission management.
"""
import json
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import TemplateView

from .models import MedicalFormTemplate, MedicalFormSubmission


class MedicalFormsDashboardView(PermissionRequiredMixin, TemplateView):
    """Main dashboard for medical forms system."""
    
    template_name = "wagtail_medical_forms/dashboard.html"
    permission_required = "wagtail_medical_forms.view_medicalformtemplate"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Form template statistics
        total_templates = MedicalFormTemplate.objects.filter(is_active=True).count()
        templates_by_category = MedicalFormTemplate.objects.filter(
            is_active=True
        ).values('category').annotate(count=models.Count('id'))
        
        # Submission statistics
        total_submissions = MedicalFormSubmission.objects.count()
        pending_reviews = MedicalFormSubmission.objects.filter(status='under_review').count()
        
        # Recent activity
        recent_submissions = MedicalFormSubmission.objects.select_related(
            'form_template', 'patient'
        ).order_by('-created_at')[:10]
        
        context.update({
            'title': _("Medical Forms Dashboard"),
            'total_templates': total_templates,
            'templates_by_category': templates_by_category,
            'total_submissions': total_submissions,
            'pending_reviews': pending_reviews,
            'recent_submissions': recent_submissions,
        })
        
        return context


class FormBuilderView(PermissionRequiredMixin, TemplateView):
    """View for building medical forms."""
    
    template_name = "wagtail_medical_forms/form_builder.html"
    permission_required = "wagtail_medical_forms.build_medical_forms"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update({
            'title': _("Medical Form Builder"),
        })
        
        return context


class SubmissionDetailView(PermissionRequiredMixin, TemplateView):
    """View for displaying form submission details."""
    
    template_name = "wagtail_medical_forms/submission_detail.html"
    permission_required = "wagtail_medical_forms.view_medicalformsubmission"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        submission_id = kwargs.get('submission_id')
        submission = get_object_or_404(MedicalFormSubmission, id=submission_id)
        
        # Check permissions for HIPAA data
        can_access_hipaa = self.request.user.has_perm('wagtail_medical_forms.access_hipaa_data')
        
        context.update({
            'title': f"{_('Form Submission')} - {submission.form_template.name}",
            'submission': submission,
            'can_access_hipaa': can_access_hipaa,
        })
        
        return context


class MedicalFormsAPIView(PermissionRequiredMixin, View):
    """API endpoint for medical forms functionality."""
    
    permission_required = "wagtail_medical_forms.view_medicalformtemplate"
    
    def post(self, request):
        """Handle API requests for medical forms."""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'create_template':
                return self._create_template(request, data)
            elif action == 'submit_form':
                return self._submit_form(request, data)
            elif action == 'review_submission':
                return self._review_submission(request, data)
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    def _create_template(self, request, data):
        """Create a new form template via API."""
        try:
            if not request.user.has_perm('wagtail_medical_forms.add_medicalformtemplate'):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            template_data = data.get('template_data', {})
            
            template = MedicalFormTemplate.objects.create(
                name=template_data['name'],
                description=template_data.get('description', ''),
                category=template_data.get('category', 'intake'),
                form_fields=template_data.get('form_fields', []),
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'template_id': str(template.id),
                'message': _("Form template created successfully")
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def _submit_form(self, request, data):
        """Submit a form via API."""
        try:
            template_id = data.get('template_id')
            form_data = data.get('form_data', {})
            patient_id = data.get('patient_id')
            
            template = MedicalFormTemplate.objects.get(id=template_id)
            
            submission = MedicalFormSubmission.objects.create(
                form_template=template,
                submitted_by=request.user,
                patient_id=patient_id,
                form_data=form_data,
                submission_source='web'
            )
            
            return JsonResponse({
                'success': True,
                'submission_id': str(submission.id),
                'message': _("Form submitted successfully")
            })
            
        except MedicalFormTemplate.DoesNotExist:
            return JsonResponse({'error': 'Form template not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def _review_submission(self, request, data):
        """Review a form submission via API."""
        try:
            if not request.user.has_perm('wagtail_medical_forms.review_form_submissions'):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            submission_id = data.get('submission_id')
            status = data.get('status')
            review_notes = data.get('review_notes', '')
            
            submission = MedicalFormSubmission.objects.get(id=submission_id)
            submission.status = status
            submission.review_notes = review_notes
            submission.reviewed_by = request.user
            submission.reviewed_at = timezone.now()
            submission.save()
            
            return JsonResponse({
                'success': True,
                'message': _("Submission reviewed successfully")
            })
            
        except MedicalFormSubmission.DoesNotExist:
            return JsonResponse({'error': 'Submission not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
