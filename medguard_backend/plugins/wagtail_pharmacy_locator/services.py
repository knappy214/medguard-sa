"""
Pharmacy Locator Services
Core services for pharmacy search, location finding, and inventory management.
"""
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import (
    Pharmacy, 
    MedicationInventory, 
    PharmacyReview,
    PharmacySearchLog,
    PharmacyStatus,
    InventoryStatus
)

logger = logging.getLogger(__name__)


class PharmacyLocatorService:
    """Service for locating pharmacies and managing inventory searches."""
    
    def __init__(self):
        """Initialize the pharmacy locator service."""
        self.default_search_radius = getattr(
            settings, 
            'PHARMACY_SEARCH_RADIUS_KM', 
            10.0
        )
        self.google_maps_api_key = getattr(
            settings, 
            'GOOGLE_MAPS_API_KEY', 
            None
        )
    
    def search_pharmacies(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        address: Optional[str] = None,
        radius_km: Optional[float] = None,
        medication_name: Optional[str] = None,
        filters: Optional[Dict] = None,
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Search for pharmacies based on location and criteria.
        
        Args:
            latitude: Search latitude
            longitude: Search longitude
            address: Search address (alternative to lat/lng)
            radius_km: Search radius in kilometers
            medication_name: Specific medication to search for
            filters: Additional search filters
            user_id: ID of user performing search
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            search_start_time = timezone.now()
            filters = filters or {}
            radius_km = radius_km or self.default_search_radius
            
            # Create search log
            search_log = PharmacySearchLog.objects.create(
                user_id=user_id,
                search_address=address or '',
                search_radius=radius_km,
                medication_searched=medication_name or '',
                filters_applied=filters,
                search_status='in_progress'
            )
            
            # Get search location
            search_point = None
            if latitude and longitude:
                search_point = Point(longitude, latitude)
                search_log.search_location = search_point
            elif address:
                # Geocode address
                geocoded = self._geocode_address(address)
                if geocoded:
                    search_point = Point(geocoded['longitude'], geocoded['latitude'])
                    search_log.search_location = search_point
            
            if not search_point:
                search_log.search_status = 'failed'
                search_log.save()
                return {
                    'success': False,
                    'error': _("Invalid search location"),
                    'pharmacies': [],
                    'search_log_id': str(search_log.id)
                }
            
            # Build base queryset
            pharmacies = Pharmacy.objects.filter(
                status=PharmacyStatus.ACTIVE,
                location__isnull=False
            )
            
            # Apply location filter
            pharmacies = pharmacies.filter(
                location__distance_lte=(search_point, Distance(km=radius_km))
            )
            
            # Apply additional filters
            if filters.get('pharmacy_type'):
                pharmacies = pharmacies.filter(pharmacy_type=filters['pharmacy_type'])
            
            if filters.get('has_drive_through'):
                pharmacies = pharmacies.filter(has_drive_through=True)
            
            if filters.get('wheelchair_accessible'):
                pharmacies = pharmacies.filter(wheelchair_accessible=True)
            
            if filters.get('open_now'):
                # Filter for currently open pharmacies
                pharmacies = [p for p in pharmacies if p.is_open_now()]
            
            if filters.get('min_rating'):
                min_rating = float(filters['min_rating'])
                pharmacies = pharmacies.filter(average_rating__gte=min_rating)
            
            # Filter by medication availability
            if medication_name:
                pharmacies = pharmacies.filter(
                    medication_inventory__medication_name__icontains=medication_name,
                    medication_inventory__status=InventoryStatus.IN_STOCK,
                    medication_inventory__quantity_available__gt=0
                ).distinct()
            
            # Calculate distances and sort
            pharmacy_results = []
            for pharmacy in pharmacies:
                distance = pharmacy.location.distance(search_point)
                distance_km = distance.km
                
                # Get medication inventory if searching for specific medication
                medication_info = None
                if medication_name:
                    inventory = MedicationInventory.objects.filter(
                        pharmacy=pharmacy,
                        medication_name__icontains=medication_name,
                        status=InventoryStatus.IN_STOCK
                    ).first()
                    
                    if inventory:
                        medication_info = {
                            'name': inventory.medication_name,
                            'strength': inventory.strength,
                            'dosage_form': inventory.dosage_form,
                            'price': float(inventory.unit_price),
                            'quantity_available': inventory.available_quantity,
                            'insurance_covered': inventory.insurance_covered
                        }
                
                pharmacy_results.append({
                    'pharmacy': pharmacy,
                    'distance_km': distance_km,
                    'medication_info': medication_info,
                    'is_open_now': pharmacy.is_open_now(),
                })
            
            # Sort by distance
            pharmacy_results.sort(key=lambda x: x['distance_km'])
            
            # Update search log
            search_duration = (timezone.now() - search_start_time).total_seconds()
            search_log.results_count = len(pharmacy_results)
            search_log.search_duration = search_duration
            search_log.search_status = 'completed'
            search_log.pharmacies_found.set([result['pharmacy'] for result in pharmacy_results])
            search_log.save()
            
            logger.info(f"Pharmacy search completed: {len(pharmacy_results)} results in {search_duration:.2f}s")
            
            return {
                'success': True,
                'pharmacies': pharmacy_results,
                'search_metadata': {
                    'search_location': {
                        'latitude': search_point.y,
                        'longitude': search_point.x
                    },
                    'radius_km': radius_km,
                    'total_results': len(pharmacy_results),
                    'search_duration': search_duration
                },
                'search_log_id': str(search_log.id)
            }
            
        except Exception as e:
            logger.error(f"Pharmacy search failed: {e}")
            if 'search_log' in locals():
                search_log.search_status = 'failed'
                search_log.save()
            
            return {
                'success': False,
                'error': str(e),
                'pharmacies': [],
                'search_log_id': str(search_log.id) if 'search_log' in locals() else None
            }
    
    def get_pharmacy_details(self, pharmacy_id: str) -> Dict:
        """
        Get detailed information about a specific pharmacy.
        
        Args:
            pharmacy_id: UUID of the pharmacy
            
        Returns:
            Dictionary containing pharmacy details
        """
        try:
            pharmacy = Pharmacy.objects.get(id=pharmacy_id)
            
            # Get inventory summary
            inventory_summary = MedicationInventory.objects.filter(
                pharmacy=pharmacy
            ).aggregate(
                total_medications=Count('id'),
                in_stock_count=Count('id', filter=Q(status=InventoryStatus.IN_STOCK)),
                low_stock_count=Count('id', filter=Q(status=InventoryStatus.LOW_STOCK)),
                out_of_stock_count=Count('id', filter=Q(status=InventoryStatus.OUT_OF_STOCK))
            )
            
            # Get recent reviews
            recent_reviews = PharmacyReview.objects.filter(
                pharmacy=pharmacy
            ).select_related('reviewer').order_by('-created_at')[:5]
            
            # Get operating status
            is_open_now = pharmacy.is_open_now()
            
            return {
                'success': True,
                'pharmacy': pharmacy,
                'inventory_summary': inventory_summary,
                'recent_reviews': recent_reviews,
                'is_open_now': is_open_now,
                'full_address': pharmacy.get_full_address(),
            }
            
        except Pharmacy.DoesNotExist:
            return {
                'success': False,
                'error': _("Pharmacy not found")
            }
        except Exception as e:
            logger.error(f"Failed to get pharmacy details: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_medication_availability(
        self,
        medication_name: str,
        pharmacy_ids: Optional[List[str]] = None,
        location: Optional[Tuple[float, float]] = None,
        radius_km: Optional[float] = None
    ) -> Dict:
        """
        Check medication availability across pharmacies.
        
        Args:
            medication_name: Name of medication to check
            pharmacy_ids: Specific pharmacy IDs to check
            location: (latitude, longitude) for location-based search
            radius_km: Search radius in kilometers
            
        Returns:
            Dictionary containing availability information
        """
        try:
            # Build base queryset
            inventory_query = MedicationInventory.objects.filter(
                medication_name__icontains=medication_name,
                pharmacy__status=PharmacyStatus.ACTIVE
            ).select_related('pharmacy')
            
            # Filter by specific pharmacies
            if pharmacy_ids:
                inventory_query = inventory_query.filter(pharmacy_id__in=pharmacy_ids)
            
            # Filter by location
            elif location and radius_km:
                search_point = Point(location[1], location[0])  # longitude, latitude
                inventory_query = inventory_query.filter(
                    pharmacy__location__distance_lte=(search_point, Distance(km=radius_km))
                )
            
            # Group results by pharmacy
            availability_results = {}
            
            for inventory in inventory_query:
                pharmacy_id = str(inventory.pharmacy.id)
                
                if pharmacy_id not in availability_results:
                    availability_results[pharmacy_id] = {
                        'pharmacy': inventory.pharmacy,
                        'medications': [],
                        'total_available': 0,
                        'lowest_price': None,
                        'is_open_now': inventory.pharmacy.is_open_now()
                    }
                
                med_info = {
                    'inventory_id': str(inventory.id),
                    'medication_name': inventory.medication_name,
                    'generic_name': inventory.generic_name,
                    'strength': inventory.strength,
                    'dosage_form': inventory.dosage_form,
                    'manufacturer': inventory.manufacturer,
                    'status': inventory.status,
                    'quantity_available': inventory.available_quantity,
                    'unit_price': float(inventory.unit_price),
                    'insurance_covered': inventory.insurance_covered,
                    'expiry_date': inventory.expiry_date.isoformat() if inventory.expiry_date else None,
                    'is_expired': inventory.is_expired,
                    'is_low_stock': inventory.is_low_stock
                }
                
                availability_results[pharmacy_id]['medications'].append(med_info)
                availability_results[pharmacy_id]['total_available'] += inventory.available_quantity
                
                # Track lowest price
                if (availability_results[pharmacy_id]['lowest_price'] is None or 
                    inventory.unit_price < availability_results[pharmacy_id]['lowest_price']):
                    availability_results[pharmacy_id]['lowest_price'] = float(inventory.unit_price)
            
            # Convert to list and sort by availability and price
            results_list = list(availability_results.values())
            results_list.sort(key=lambda x: (-x['total_available'], x['lowest_price'] or float('inf')))
            
            return {
                'success': True,
                'medication_name': medication_name,
                'total_pharmacies_found': len(results_list),
                'availability_results': results_list
            }
            
        except Exception as e:
            logger.error(f"Failed to check medication availability: {e}")
            return {
                'success': False,
                'error': str(e),
                'availability_results': []
            }
    
    def reserve_medication(
        self,
        inventory_id: str,
        quantity: int,
        user_id: int,
        reservation_notes: Optional[str] = None
    ) -> Dict:
        """
        Reserve medication at a pharmacy.
        
        Args:
            inventory_id: ID of the medication inventory
            quantity: Quantity to reserve
            user_id: ID of user making reservation
            reservation_notes: Optional notes for the reservation
            
        Returns:
            Dictionary containing reservation result
        """
        try:
            inventory = MedicationInventory.objects.select_for_update().get(id=inventory_id)
            
            # Check availability
            if inventory.available_quantity < quantity:
                return {
                    'success': False,
                    'error': _("Insufficient quantity available"),
                    'available_quantity': inventory.available_quantity
                }
            
            # Check pharmacy status
            if inventory.pharmacy.status != PharmacyStatus.ACTIVE:
                return {
                    'success': False,
                    'error': _("Pharmacy is currently not active")
                }
            
            # Create reservation (this would typically integrate with pharmacy systems)
            reservation_data = {
                'inventory_id': inventory_id,
                'user_id': user_id,
                'quantity_reserved': quantity,
                'reservation_time': timezone.now(),
                'expiry_time': timezone.now() + timedelta(hours=24),  # 24-hour hold
                'notes': reservation_notes or '',
                'pharmacy_name': inventory.pharmacy.name,
                'medication_name': inventory.medication_name,
                'total_price': float(inventory.unit_price * quantity)
            }
            
            # Update inventory
            inventory.quantity_reserved += quantity
            inventory.save()
            
            logger.info(f"Medication reserved: {quantity} units of {inventory.medication_name} at {inventory.pharmacy.name}")
            
            return {
                'success': True,
                'reservation_data': reservation_data,
                'message': _("Medication reserved successfully")
            }
            
        except MedicationInventory.DoesNotExist:
            return {
                'success': False,
                'error': _("Medication inventory not found")
            }
        except Exception as e:
            logger.error(f"Failed to reserve medication: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_pharmacy_directions(
        self,
        pharmacy_id: str,
        origin_latitude: float,
        origin_longitude: float
    ) -> Dict:
        """
        Get directions to a pharmacy.
        
        Args:
            pharmacy_id: ID of the target pharmacy
            origin_latitude: Starting latitude
            origin_longitude: Starting longitude
            
        Returns:
            Dictionary containing directions information
        """
        try:
            pharmacy = Pharmacy.objects.get(id=pharmacy_id)
            
            if not pharmacy.location:
                return {
                    'success': False,
                    'error': _("Pharmacy location not available")
                }
            
            # Use Google Maps Directions API if available
            if self.google_maps_api_key:
                directions = self._get_google_directions(
                    origin_latitude,
                    origin_longitude,
                    pharmacy.location.y,
                    pharmacy.location.x
                )
                
                if directions:
                    return {
                        'success': True,
                        'pharmacy': pharmacy,
                        'directions': directions
                    }
            
            # Fallback to basic distance calculation
            origin_point = Point(origin_longitude, origin_latitude)
            distance = pharmacy.location.distance(origin_point)
            
            return {
                'success': True,
                'pharmacy': pharmacy,
                'directions': {
                    'distance_km': distance.km,
                    'distance_miles': distance.mi,
                    'estimated_drive_time_minutes': int(distance.km * 2),  # Rough estimate
                    'destination': {
                        'latitude': pharmacy.location.y,
                        'longitude': pharmacy.location.x,
                        'address': pharmacy.get_full_address()
                    }
                }
            }
            
        except Pharmacy.DoesNotExist:
            return {
                'success': False,
                'error': _("Pharmacy not found")
            }
        except Exception as e:
            logger.error(f"Failed to get directions: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_pharmacy_inventory(
        self,
        pharmacy_id: str,
        inventory_data: List[Dict]
    ) -> Dict:
        """
        Update pharmacy inventory from external systems.
        
        Args:
            pharmacy_id: ID of the pharmacy
            inventory_data: List of inventory updates
            
        Returns:
            Dictionary containing update results
        """
        try:
            pharmacy = Pharmacy.objects.get(id=pharmacy_id)
            
            updated_count = 0
            created_count = 0
            errors = []
            
            for item in inventory_data:
                try:
                    # Get or create inventory item
                    inventory, created = MedicationInventory.objects.get_or_create(
                        pharmacy=pharmacy,
                        medication_name=item['medication_name'],
                        strength=item.get('strength', ''),
                        dosage_form=item.get('dosage_form', ''),
                        defaults={
                            'generic_name': item.get('generic_name', ''),
                            'manufacturer': item.get('manufacturer', ''),
                            'ndc_number': item.get('ndc_number', ''),
                            'quantity_available': item.get('quantity_available', 0),
                            'unit_price': Decimal(str(item.get('unit_price', 0))),
                            'status': item.get('status', InventoryStatus.IN_STOCK),
                            'expiry_date': item.get('expiry_date'),
                            'external_inventory_id': item.get('external_id', '')
                        }
                    )
                    
                    if not created:
                        # Update existing inventory
                        inventory.quantity_available = item.get('quantity_available', inventory.quantity_available)
                        inventory.unit_price = Decimal(str(item.get('unit_price', inventory.unit_price)))
                        inventory.status = item.get('status', inventory.status)
                        inventory.last_updated = timezone.now()
                        inventory.save()
                        updated_count += 1
                    else:
                        created_count += 1
                        
                except Exception as e:
                    errors.append(f"Failed to update {item.get('medication_name', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Inventory update completed for pharmacy {pharmacy_id}: {created_count} created, {updated_count} updated")
            
            return {
                'success': True,
                'pharmacy_id': pharmacy_id,
                'created_count': created_count,
                'updated_count': updated_count,
                'errors': errors
            }
            
        except Pharmacy.DoesNotExist:
            return {
                'success': False,
                'error': _("Pharmacy not found")
            }
        except Exception as e:
            logger.error(f"Failed to update pharmacy inventory: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _geocode_address(self, address: str) -> Optional[Dict]:
        """Geocode an address using Google Maps API."""
        if not self.google_maps_api_key:
            return None
        
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': address,
                'key': self.google_maps_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return {
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'formatted_address': data['results'][0]['formatted_address']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Geocoding failed: {e}")
            return None
    
    def _get_google_directions(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float
    ) -> Optional[Dict]:
        """Get directions using Google Maps Directions API."""
        if not self.google_maps_api_key:
            return None
        
        try:
            url = "https://maps.googleapis.com/maps/api/directions/json"
            params = {
                'origin': f"{origin_lat},{origin_lng}",
                'destination': f"{dest_lat},{dest_lng}",
                'key': self.google_maps_api_key,
                'mode': 'driving'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['routes']:
                route = data['routes'][0]
                leg = route['legs'][0]
                
                return {
                    'distance_text': leg['distance']['text'],
                    'distance_meters': leg['distance']['value'],
                    'duration_text': leg['duration']['text'],
                    'duration_seconds': leg['duration']['value'],
                    'start_address': leg['start_address'],
                    'end_address': leg['end_address'],
                    'steps': [
                        {
                            'instruction': step['html_instructions'],
                            'distance': step['distance']['text'],
                            'duration': step['duration']['text']
                        }
                        for step in leg['steps']
                    ]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Directions API failed: {e}")
            return None
