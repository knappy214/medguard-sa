"""
Views for Pharmacy Locator Plugin
Admin views for pharmacy location, search, and inventory management.
"""
import json
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.gis.geos import Point
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import TemplateView
from wagtail.admin import messages as wagtail_messages

from .models import Pharmacy, MedicationInventory, PharmacyReview, PharmacySearchLog
from .services import PharmacyLocatorService


class PharmacyLocatorDashboardView(PermissionRequiredMixin, TemplateView):
    """Main dashboard view for pharmacy locator."""
    
    template_name = "wagtail_pharmacy_locator/dashboard.html"
    permission_required = "wagtail_pharmacy_locator.view_pharmacy"
    
    def get_context_data(self, **kwargs):
        """Add context data for the dashboard."""
        context = super().get_context_data(**kwargs)
        
        # Get pharmacy statistics
        total_pharmacies = Pharmacy.objects.filter(status='active').count()
        total_inventory_items = MedicationInventory.objects.count()
        
        # Get low stock alerts
        low_stock_items = MedicationInventory.objects.filter(
            quantity_available__lte=models.F('reorder_level')
        ).select_related('pharmacy')[:10]
        
        # Get recent searches
        recent_searches = PharmacySearchLog.objects.select_related(
            'user'
        ).order_by('-created_at')[:10]
        
        # Get pharmacy distribution by type
        pharmacy_types = Pharmacy.objects.filter(
            status='active'
        ).values('pharmacy_type').annotate(
            count=Count('id')
        )
        
        # Get top searched medications
        top_medications = PharmacySearchLog.objects.filter(
            medication_searched__isnull=False
        ).exclude(
            medication_searched=''
        ).values('medication_searched').annotate(
            search_count=Count('id')
        ).order_by('-search_count')[:10]
        
        # Get average ratings
        avg_rating = PharmacyReview.objects.aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0
        
        context.update({
            'title': _("Pharmacy Locator Dashboard"),
            'total_pharmacies': total_pharmacies,
            'total_inventory_items': total_inventory_items,
            'low_stock_items': low_stock_items,
            'low_stock_count': low_stock_items.count(),
            'recent_searches': recent_searches,
            'pharmacy_types': pharmacy_types,
            'top_medications': top_medications,
            'average_rating': avg_rating,
        })
        
        return context


class PharmacySearchView(PermissionRequiredMixin, TemplateView):
    """View for pharmacy search functionality."""
    
    template_name = "wagtail_pharmacy_locator/search.html"
    permission_required = "wagtail_pharmacy_locator.view_pharmacy"
    
    def get_context_data(self, **kwargs):
        """Add context data for pharmacy search."""
        context = super().get_context_data(**kwargs)
        
        # Get search parameters from GET request
        search_params = {
            'address': self.request.GET.get('address', ''),
            'latitude': self.request.GET.get('latitude'),
            'longitude': self.request.GET.get('longitude'),
            'radius': self.request.GET.get('radius', '10'),
            'medication': self.request.GET.get('medication', ''),
            'pharmacy_type': self.request.GET.get('pharmacy_type', ''),
            'open_now': self.request.GET.get('open_now') == 'true',
            'has_drive_through': self.request.GET.get('has_drive_through') == 'true',
            'wheelchair_accessible': self.request.GET.get('wheelchair_accessible') == 'true',
        }
        
        # Perform search if parameters provided
        search_results = None
        if search_params['address'] or (search_params['latitude'] and search_params['longitude']):
            locator_service = PharmacyLocatorService()
            
            search_filters = {}
            if search_params['pharmacy_type']:
                search_filters['pharmacy_type'] = search_params['pharmacy_type']
            if search_params['open_now']:
                search_filters['open_now'] = True
            if search_params['has_drive_through']:
                search_filters['has_drive_through'] = True
            if search_params['wheelchair_accessible']:
                search_filters['wheelchair_accessible'] = True
            
            search_results = locator_service.search_pharmacies(
                latitude=float(search_params['latitude']) if search_params['latitude'] else None,
                longitude=float(search_params['longitude']) if search_params['longitude'] else None,
                address=search_params['address'] if search_params['address'] else None,
                radius_km=float(search_params['radius']),
                medication_name=search_params['medication'] if search_params['medication'] else None,
                filters=search_filters,
                user_id=self.request.user.id
            )
        
        # Get pharmacy types for filter dropdown
        pharmacy_types = Pharmacy.objects.values_list(
            'pharmacy_type', flat=True
        ).distinct().order_by('pharmacy_type')
        
        context.update({
            'title': _("Pharmacy Search"),
            'search_params': search_params,
            'search_results': search_results,
            'pharmacy_types': pharmacy_types,
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle pharmacy search form submission."""
        # Redirect to GET request with search parameters
        params = {
            'address': request.POST.get('address', ''),
            'latitude': request.POST.get('latitude', ''),
            'longitude': request.POST.get('longitude', ''),
            'radius': request.POST.get('radius', '10'),
            'medication': request.POST.get('medication', ''),
            'pharmacy_type': request.POST.get('pharmacy_type', ''),
        }
        
        # Add boolean filters
        if request.POST.get('open_now'):
            params['open_now'] = 'true'
        if request.POST.get('has_drive_through'):
            params['has_drive_through'] = 'true'
        if request.POST.get('wheelchair_accessible'):
            params['wheelchair_accessible'] = 'true'
        
        # Remove empty parameters
        params = {k: v for k, v in params.items() if v}
        
        return redirect(f"{reverse('pharmacy_search')}?{'&'.join(f'{k}={v}' for k, v in params.items())}")


class PharmacyDetailsView(PermissionRequiredMixin, TemplateView):
    """View for displaying detailed pharmacy information."""
    
    template_name = "wagtail_pharmacy_locator/pharmacy_details.html"
    permission_required = "wagtail_pharmacy_locator.view_pharmacy"
    
    def get_context_data(self, **kwargs):
        """Add context data for pharmacy details."""
        context = super().get_context_data(**kwargs)
        
        pharmacy_id = kwargs.get('pharmacy_id')
        
        # Get pharmacy details using service
        locator_service = PharmacyLocatorService()
        pharmacy_details = locator_service.get_pharmacy_details(pharmacy_id)
        
        if not pharmacy_details['success']:
            wagtail_messages.error(self.request, pharmacy_details['error'])
            return redirect('pharmacy_locator_dashboard')
        
        pharmacy = pharmacy_details['pharmacy']
        
        # Get additional context
        context.update({
            'title': f"{pharmacy.name} - {_('Pharmacy Details')}",
            'pharmacy': pharmacy,
            'inventory_summary': pharmacy_details['inventory_summary'],
            'recent_reviews': pharmacy_details['recent_reviews'],
            'is_open_now': pharmacy_details['is_open_now'],
            'full_address': pharmacy_details['full_address'],
        })
        
        return context


class MedicationAvailabilityView(PermissionRequiredMixin, TemplateView):
    """View for checking medication availability across pharmacies."""
    
    template_name = "wagtail_pharmacy_locator/medication_availability.html"
    permission_required = "wagtail_pharmacy_locator.view_medicationinventory"
    
    def get_context_data(self, **kwargs):
        """Add context data for medication availability."""
        context = super().get_context_data(**kwargs)
        
        medication_name = self.request.GET.get('medication')
        location_lat = self.request.GET.get('latitude')
        location_lng = self.request.GET.get('longitude')
        radius = self.request.GET.get('radius', '10')
        
        availability_results = None
        
        if medication_name:
            locator_service = PharmacyLocatorService()
            
            # Prepare location if provided
            location = None
            if location_lat and location_lng:
                location = (float(location_lat), float(location_lng))
            
            availability_results = locator_service.check_medication_availability(
                medication_name=medication_name,
                location=location,
                radius_km=float(radius) if location else None
            )
        
        context.update({
            'title': _("Medication Availability"),
            'medication_name': medication_name,
            'availability_results': availability_results,
            'search_params': {
                'medication': medication_name,
                'latitude': location_lat,
                'longitude': location_lng,
                'radius': radius,
            }
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle medication availability search."""
        # Redirect to GET request with search parameters
        params = {
            'medication': request.POST.get('medication', ''),
            'latitude': request.POST.get('latitude', ''),
            'longitude': request.POST.get('longitude', ''),
            'radius': request.POST.get('radius', '10'),
        }
        
        # Remove empty parameters
        params = {k: v for k, v in params.items() if v}
        
        return redirect(f"{reverse('medication_availability')}?{'&'.join(f'{k}={v}' for k, v in params.items())}")


class PharmacyMapView(PermissionRequiredMixin, TemplateView):
    """View for displaying pharmacies on an interactive map."""
    
    template_name = "wagtail_pharmacy_locator/map.html"
    permission_required = "wagtail_pharmacy_locator.view_pharmacy"
    
    def get_context_data(self, **kwargs):
        """Add context data for pharmacy map."""
        context = super().get_context_data(**kwargs)
        
        # Get active pharmacies with location data
        pharmacies = Pharmacy.objects.filter(
            status='active',
            location__isnull=False
        ).select_related()
        
        # Convert to GeoJSON format for map display
        pharmacy_geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        
        for pharmacy in pharmacies:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [pharmacy.location.x, pharmacy.location.y]
                },
                "properties": {
                    "id": str(pharmacy.id),
                    "name": pharmacy.name,
                    "address": pharmacy.get_full_address(),
                    "phone": pharmacy.phone,
                    "pharmacy_type": pharmacy.get_pharmacy_type_display(),
                    "is_open_now": pharmacy.is_open_now(),
                    "average_rating": pharmacy.average_rating,
                    "has_drive_through": pharmacy.has_drive_through,
                    "wheelchair_accessible": pharmacy.wheelchair_accessible,
                }
            }
            pharmacy_geojson["features"].append(feature)
        
        context.update({
            'title': _("Pharmacy Map"),
            'pharmacies_geojson': json.dumps(pharmacy_geojson),
            'total_pharmacies': len(pharmacy_geojson["features"]),
        })
        
        return context


class InventoryManagementView(PermissionRequiredMixin, TemplateView):
    """View for managing pharmacy inventory."""
    
    template_name = "wagtail_pharmacy_locator/inventory_management.html"
    permission_required = "wagtail_pharmacy_locator.manage_pharmacy_inventory"
    
    def get_context_data(self, **kwargs):
        """Add context data for inventory management."""
        context = super().get_context_data(**kwargs)
        
        pharmacy_id = kwargs.get('pharmacy_id')
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        
        # Check if user has permission to manage this pharmacy
        if not self._can_manage_pharmacy_inventory(pharmacy):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        
        # Get inventory items
        inventory_items = MedicationInventory.objects.filter(
            pharmacy=pharmacy
        ).order_by('medication_name')
        
        # Get inventory statistics
        inventory_stats = {
            'total_items': inventory_items.count(),
            'in_stock': inventory_items.filter(status='in_stock').count(),
            'low_stock': inventory_items.filter(
                quantity_available__lte=models.F('reorder_level')
            ).count(),
            'out_of_stock': inventory_items.filter(status='out_of_stock').count(),
        }
        
        # Get low stock alerts
        low_stock_items = inventory_items.filter(
            quantity_available__lte=models.F('reorder_level')
        )[:10]
        
        context.update({
            'title': f"{pharmacy.name} - {_('Inventory Management')}",
            'pharmacy': pharmacy,
            'inventory_items': inventory_items,
            'inventory_stats': inventory_stats,
            'low_stock_items': low_stock_items,
        })
        
        return context
    
    def post(self, request, pharmacy_id):
        """Handle inventory updates."""
        pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
        
        if not self._can_manage_pharmacy_inventory(pharmacy):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        
        action = request.POST.get('action')
        
        if action == 'update_inventory':
            inventory_id = request.POST.get('inventory_id')
            quantity = request.POST.get('quantity')
            price = request.POST.get('price')
            
            try:
                inventory = MedicationInventory.objects.get(
                    id=inventory_id,
                    pharmacy=pharmacy
                )
                
                if quantity:
                    inventory.quantity_available = int(quantity)
                if price:
                    inventory.unit_price = float(price)
                
                inventory.save()
                
                wagtail_messages.success(
                    request,
                    _("Inventory updated successfully")
                )
                
            except MedicationInventory.DoesNotExist:
                wagtail_messages.error(
                    request,
                    _("Inventory item not found")
                )
            except (ValueError, TypeError):
                wagtail_messages.error(
                    request,
                    _("Invalid quantity or price")
                )
        
        return redirect('inventory_management', pharmacy_id=pharmacy_id)
    
    def _can_manage_pharmacy_inventory(self, pharmacy):
        """Check if user can manage this pharmacy's inventory."""
        user = self.request.user
        
        # Admins can manage all inventories
        if user.is_staff:
            return True
        
        # Pharmacy staff can manage their own pharmacy
        if user.groups.filter(name='Pharmacy Staff').exists():
            # This would require a relationship between users and pharmacies
            # For now, we'll allow all pharmacy staff
            return True
        
        return False


class PharmacyLocatorAPIView(PermissionRequiredMixin, View):
    """API endpoint for pharmacy locator functionality."""
    
    permission_required = "wagtail_pharmacy_locator.view_pharmacy"
    
    def get(self, request):
        """Handle API GET requests."""
        endpoint = request.GET.get('endpoint')
        
        if endpoint == 'search':
            return self._search_pharmacies(request)
        elif endpoint == 'pharmacy_details':
            return self._get_pharmacy_details(request)
        elif endpoint == 'medication_availability':
            return self._check_medication_availability(request)
        elif endpoint == 'directions':
            return self._get_directions(request)
        else:
            return JsonResponse({'error': 'Invalid endpoint'}, status=400)
    
    def post(self, request):
        """Handle API POST requests."""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'reserve_medication':
                return self._reserve_medication(request, data)
            elif action == 'submit_review':
                return self._submit_review(request, data)
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    def _search_pharmacies(self, request):
        """Search pharmacies via API."""
        try:
            locator_service = PharmacyLocatorService()
            
            # Get search parameters
            latitude = request.GET.get('latitude')
            longitude = request.GET.get('longitude')
            address = request.GET.get('address')
            radius = float(request.GET.get('radius', 10))
            medication = request.GET.get('medication')
            
            # Build filters
            filters = {}
            if request.GET.get('pharmacy_type'):
                filters['pharmacy_type'] = request.GET.get('pharmacy_type')
            if request.GET.get('open_now') == 'true':
                filters['open_now'] = True
            
            # Perform search
            results = locator_service.search_pharmacies(
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                address=address,
                radius_km=radius,
                medication_name=medication,
                filters=filters,
                user_id=request.user.id
            )
            
            # Serialize results for API response
            if results['success']:
                serialized_pharmacies = []
                for result in results['pharmacies']:
                    pharmacy = result['pharmacy']
                    serialized_pharmacies.append({
                        'id': str(pharmacy.id),
                        'name': pharmacy.name,
                        'address': pharmacy.get_full_address(),
                        'phone': pharmacy.phone,
                        'pharmacy_type': pharmacy.pharmacy_type,
                        'distance_km': result['distance_km'],
                        'is_open_now': result['is_open_now'],
                        'average_rating': pharmacy.average_rating,
                        'medication_info': result['medication_info'],
                        'coordinates': {
                            'latitude': pharmacy.location.y,
                            'longitude': pharmacy.location.x
                        } if pharmacy.location else None
                    })
                
                results['pharmacies'] = serialized_pharmacies
            
            return JsonResponse(results)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _get_pharmacy_details(self, request):
        """Get pharmacy details via API."""
        try:
            pharmacy_id = request.GET.get('pharmacy_id')
            if not pharmacy_id:
                return JsonResponse({'error': 'pharmacy_id required'}, status=400)
            
            locator_service = PharmacyLocatorService()
            details = locator_service.get_pharmacy_details(pharmacy_id)
            
            if details['success']:
                pharmacy = details['pharmacy']
                
                # Serialize pharmacy data
                pharmacy_data = {
                    'id': str(pharmacy.id),
                    'name': pharmacy.name,
                    'address': pharmacy.get_full_address(),
                    'phone': pharmacy.phone,
                    'email': pharmacy.email,
                    'website': pharmacy.website,
                    'pharmacy_type': pharmacy.get_pharmacy_type_display(),
                    'operating_hours': pharmacy.operating_hours,
                    'services': pharmacy.services,
                    'amenities': {
                        'drive_through': pharmacy.has_drive_through,
                        'parking': pharmacy.has_parking,
                        'wheelchair_accessible': pharmacy.wheelchair_accessible,
                        'consultation_room': pharmacy.has_consultation_room,
                    },
                    'rating': {
                        'average': pharmacy.average_rating,
                        'total_reviews': pharmacy.total_reviews,
                    },
                    'is_open_now': details['is_open_now'],
                    'coordinates': {
                        'latitude': pharmacy.location.y,
                        'longitude': pharmacy.location.x
                    } if pharmacy.location else None
                }
                
                details['pharmacy'] = pharmacy_data
                
                # Serialize reviews
                reviews = []
                for review in details['recent_reviews']:
                    reviews.append({
                        'id': str(review.id),
                        'rating': review.rating,
                        'title': review.title,
                        'review_text': review.review_text,
                        'reviewer_name': review.reviewer.get_full_name(),
                        'created_at': review.created_at.isoformat(),
                    })
                
                details['recent_reviews'] = reviews
            
            return JsonResponse(details)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _check_medication_availability(self, request):
        """Check medication availability via API."""
        try:
            medication_name = request.GET.get('medication')
            if not medication_name:
                return JsonResponse({'error': 'medication parameter required'}, status=400)
            
            latitude = request.GET.get('latitude')
            longitude = request.GET.get('longitude')
            radius = float(request.GET.get('radius', 10))
            
            location = None
            if latitude and longitude:
                location = (float(latitude), float(longitude))
            
            locator_service = PharmacyLocatorService()
            results = locator_service.check_medication_availability(
                medication_name=medication_name,
                location=location,
                radius_km=radius if location else None
            )
            
            return JsonResponse(results)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _reserve_medication(self, request, data):
        """Reserve medication via API."""
        try:
            inventory_id = data.get('inventory_id')
            quantity = int(data.get('quantity', 1))
            notes = data.get('notes', '')
            
            locator_service = PharmacyLocatorService()
            result = locator_service.reserve_medication(
                inventory_id=inventory_id,
                quantity=quantity,
                user_id=request.user.id,
                reservation_notes=notes
            )
            
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _submit_review(self, request, data):
        """Submit pharmacy review via API."""
        try:
            pharmacy_id = data.get('pharmacy_id')
            rating = int(data.get('rating'))
            title = data.get('title', '')
            review_text = data.get('review_text', '')
            
            pharmacy = Pharmacy.objects.get(id=pharmacy_id)
            
            # Create or update review
            review, created = PharmacyReview.objects.update_or_create(
                pharmacy=pharmacy,
                reviewer=request.user,
                defaults={
                    'rating': rating,
                    'title': title,
                    'review_text': review_text,
                }
            )
            
            return JsonResponse({
                'success': True,
                'review_id': str(review.id),
                'message': _("Review submitted successfully")
            })
            
        except Pharmacy.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': _("Pharmacy not found")
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
