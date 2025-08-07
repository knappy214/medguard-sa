"""
Views for Prescription OCR Plugin
Admin views for OCR processing and result management.
"""
import json
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import TemplateView
from wagtail.admin import messages as wagtail_messages
from wagtailimages.models import Image

from .models import PrescriptionOCRResult, OCRTemplate
from .services import PrescriptionOCRService


class OCRProcessingView(PermissionRequiredMixin, TemplateView):
    """View for processing prescription images with OCR."""
    
    template_name = "wagtail_prescription_ocr/process.html"
    permission_required = "wagtail_prescription_ocr.add_prescriptionocrresult"
    
    def get_context_data(self, **kwargs):
        """Add context data for the template."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _("Process Prescription Image"),
            'ocr_templates': OCRTemplate.objects.filter(is_active=True),
            'recent_results': PrescriptionOCRResult.objects.select_related(
                'prescription_image'
            ).order_by('-processed_at')[:10]
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle OCR processing request."""
        image_id = request.POST.get('image_id')
        template_id = request.POST.get('template_id')
        
        if not image_id:
            wagtail_messages.error(request, _("Please select an image to process."))
            return self.get(request, *args, **kwargs)
        
        try:
            image = get_object_or_404(Image, id=image_id)
            ocr_service = PrescriptionOCRService()
            
            # Process the image
            result = ocr_service.process_prescription_image(
                image.file.path,
                template_id=int(template_id) if template_id else None
            )
            
            if result['success']:
                # Create OCR result record
                ocr_result = PrescriptionOCRResult.objects.create(
                    prescription_image=image,
                    extracted_text=result['extracted_text'],
                    confidence_score=result['confidence_score'],
                    processed_by=request.user,
                    **result['parsed_data']
                )
                
                wagtail_messages.success(
                    request, 
                    _("OCR processing completed successfully. Confidence: {:.1%}").format(
                        result['confidence_score']
                    )
                )
                
                return redirect('prescription_ocr_validate', ocr_id=ocr_result.id)
            
            else:
                wagtail_messages.error(
                    request, 
                    _("OCR processing failed: {}").format(result['error'])
                )
                
        except Exception as e:
            wagtail_messages.error(
                request, 
                _("An error occurred during processing: {}").format(str(e))
            )
        
        return self.get(request, *args, **kwargs)


class OCRResultsView(PermissionRequiredMixin, TemplateView):
    """View for displaying OCR results."""
    
    template_name = "wagtail_prescription_ocr/results.html"
    permission_required = "wagtail_prescription_ocr.view_prescriptionocrresult"
    
    def get_context_data(self, **kwargs):
        """Add context data for the template."""
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        verified = self.request.GET.get('verified')
        confidence_min = self.request.GET.get('confidence_min', 0.7)
        
        # Build queryset
        results = PrescriptionOCRResult.objects.select_related(
            'prescription_image', 'processed_by', 'verified_by'
        ).order_by('-processed_at')
        
        if verified == 'true':
            results = results.filter(is_verified=True)
        elif verified == 'false':
            results = results.filter(is_verified=False)
        
        try:
            confidence_min = float(confidence_min)
            results = results.filter(confidence_score__gte=confidence_min)
        except (ValueError, TypeError):
            pass
        
        context.update({
            'title': _("OCR Results"),
            'results': results[:50],  # Limit for performance
            'total_count': results.count(),
            'verified_count': results.filter(is_verified=True).count(),
            'unverified_count': results.filter(is_verified=False).count(),
            'filters': {
                'verified': verified,
                'confidence_min': confidence_min,
            }
        })
        
        return context


class OCRValidationView(PermissionRequiredMixin, View):
    """View for validating and correcting OCR results."""
    
    permission_required = "wagtail_prescription_ocr.change_prescriptionocrresult"
    
    def get(self, request, ocr_id):
        """Display OCR result for validation."""
        ocr_result = get_object_or_404(PrescriptionOCRResult, id=ocr_id)
        
        context = {
            'title': _("Validate OCR Result"),
            'ocr_result': ocr_result,
            'image': ocr_result.prescription_image,
        }
        
        return render(
            request, 
            'wagtail_prescription_ocr/validate.html', 
            context
        )
    
    def post(self, request, ocr_id):
        """Handle OCR result validation and corrections."""
        ocr_result = get_object_or_404(PrescriptionOCRResult, id=ocr_id)
        
        # Update fields from form
        ocr_result.medication_name = request.POST.get('medication_name', '')
        ocr_result.dosage = request.POST.get('dosage', '')
        ocr_result.frequency = request.POST.get('frequency', '')
        ocr_result.prescriber_name = request.POST.get('prescriber_name', '')
        
        # Handle date field
        prescription_date = request.POST.get('prescription_date')
        if prescription_date:
            try:
                from datetime import datetime
                ocr_result.prescription_date = datetime.strptime(
                    prescription_date, '%Y-%m-%d'
                ).date()
            except ValueError:
                pass
        
        # Mark as verified
        if request.POST.get('verify') == 'true':
            ocr_result.is_verified = True
            ocr_result.verified_by = request.user
            from django.utils import timezone
            ocr_result.verified_at = timezone.now()
        
        # Add notes
        notes = request.POST.get('notes', '')
        if notes:
            ocr_result.notes = notes
        
        ocr_result.save()
        
        # Log access for HIPAA compliance
        self._log_access(request.user, ocr_result)
        
        wagtail_messages.success(
            request, 
            _("OCR result has been updated and verified.")
        )
        
        return redirect('prescription_ocr_results')
    
    def _log_access(self, user, ocr_result):
        """Log access to OCR result for HIPAA compliance."""
        from django.utils import timezone
        
        access_entry = {
            'user_id': user.id,
            'user_name': user.get_full_name() or user.username,
            'timestamp': timezone.now().isoformat(),
            'action': 'validated',
            'ip_address': self.request.META.get('REMOTE_ADDR', '')
        }
        
        if not ocr_result.access_log:
            ocr_result.access_log = []
        
        ocr_result.access_log.append(access_entry)
        ocr_result.save(update_fields=['access_log'])


class OCRAPIView(PermissionRequiredMixin, View):
    """API endpoint for OCR processing from external applications."""
    
    permission_required = "wagtail_prescription_ocr.add_prescriptionocrresult"
    
    def post(self, request):
        """Process OCR request via API."""
        try:
            # Parse JSON request
            data = json.loads(request.body)
            image_id = data.get('image_id')
            template_id = data.get('template_id')
            
            if not image_id:
                return JsonResponse({
                    'success': False,
                    'error': 'image_id is required'
                }, status=400)
            
            image = get_object_or_404(Image, id=image_id)
            ocr_service = PrescriptionOCRService()
            
            # Process image
            result = ocr_service.process_prescription_image(
                image.file.path,
                template_id=template_id
            )
            
            if result['success']:
                # Create OCR result
                ocr_result = PrescriptionOCRResult.objects.create(
                    prescription_image=image,
                    extracted_text=result['extracted_text'],
                    confidence_score=result['confidence_score'],
                    processed_by=request.user,
                    **result['parsed_data']
                )
                
                return JsonResponse({
                    'success': True,
                    'ocr_result_id': str(ocr_result.id),
                    'confidence_score': result['confidence_score'],
                    'extracted_data': result['parsed_data']
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
