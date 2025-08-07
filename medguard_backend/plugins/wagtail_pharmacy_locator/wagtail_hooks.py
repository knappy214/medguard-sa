"""
Wagtail Hooks for Pharmacy Locator Plugin
Integrates pharmacy location and inventory functionality into Wagtail admin interface.
"""
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.contrib.modeladmin.views import IndexView

from .models import Pharmacy, MedicationInventory, PharmacyReview, PharmacySearchLog
from .views import (
    PharmacyLocatorDashboardView,
    PharmacySearchView,
    PharmacyDetailsView,
    MedicationAvailabilityView,
    PharmacyMapView,
    InventoryManagementView
)


class PharmacyAdmin(ModelAdmin):
    """ModelAdmin for Pharmacy."""
    
    model = Pharmacy
    menu_label = _("Pharmacies")
    menu_icon = "site"
    menu_order = 400
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = [
        "name",
        "chain_name", 
        "city",
        "pharmacy_type",
        "status",
        "average_rating",
        "is_open_now_display"
    ]
    list_filter = [
        "status", 
        "pharmacy_type",
        "city",
        "province",
        "has_drive_through",
        "wheelchair_accessible"
    ]
    search_fields = [
        "name", 
        "chain_name",
        "street_address",
        "city",
        "phone"
    ]
    ordering = ["name"]
    
    def is_open_now_display(self, obj):
        """Display if pharmacy is currently open."""
        return "✓" if obj.is_open_now() else "✗"
    is_open_now_display.short_description = _("Open Now")


class MedicationInventoryAdmin(ModelAdmin):
    """ModelAdmin for MedicationInventory."""
    
    model = MedicationInventory
    menu_label = _("Medication Inventory")
    menu_icon = "list-ul"
    menu_order = 401
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = [
        "medication_name",
        "pharmacy",
        "strength",
        "status",
        "quantity_available",
        "unit_price",
        "is_low_stock_display"
    ]
    list_filter = [
        "status",
        "pharmacy__city",
        "pharmacy__pharmacy_type",
        "dosage_form",
        "insurance_covered"
    ]
    search_fields = [
        "medication_name",
        "generic_name",
        "pharmacy__name",
        "manufacturer"
    ]
    ordering = ["medication_name", "pharmacy__name"]
    
    def is_low_stock_display(self, obj):
        """Display low stock indicator."""
        return "⚠️" if obj.is_low_stock else "✓"
    is_low_stock_display.short_description = _("Stock Level")


class PharmacyReviewAdmin(ModelAdmin):
    """ModelAdmin for PharmacyReview."""
    
    model = PharmacyReview
    menu_label = _("Pharmacy Reviews")
    menu_icon = "doc-full-inverse"
    menu_order = 402
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = [
        "pharmacy",
        "reviewer",
        "rating",
        "created_at",
        "is_verified"
    ]
    list_filter = [
        "rating",
        "is_verified",
        "created_at",
        "pharmacy__city"
    ]
    search_fields = [
        "pharmacy__name",
        "reviewer__first_name",
        "reviewer__last_name",
        "title",
        "review_text"
    ]
    ordering = ["-created_at"]


class PharmacySearchLogAdmin(ModelAdmin):
    """ModelAdmin for PharmacySearchLog."""
    
    model = PharmacySearchLog
    menu_label = _("Search Analytics")
    menu_icon = "doc-full"
    menu_order = 403
    add_to_settings_menu = True
    exclude_from_explorer = False
    list_display = [
        "user",
        "medication_searched",
        "search_address",
        "results_count",
        "search_status",
        "created_at"
    ]
    list_filter = [
        "search_status",
        "created_at",
        "medication_searched"
    ]
    search_fields = [
        "user__first_name",
        "user__last_name",
        "medication_searched",
        "search_address"
    ]
    ordering = ["-created_at"]


# Register ModelAdmins
modeladmin_register(PharmacyAdmin)
modeladmin_register(MedicationInventoryAdmin)
modeladmin_register(PharmacyReviewAdmin)
modeladmin_register(PharmacySearchLogAdmin)


@hooks.register("register_admin_urls")
def register_pharmacy_locator_admin_urls():
    """Register custom admin URLs for pharmacy locator functionality."""
    return [
        path(
            "pharmacy-locator/",
            PharmacyLocatorDashboardView.as_view(),
            name="pharmacy_locator_dashboard"
        ),
        path(
            "pharmacy-locator/search/",
            PharmacySearchView.as_view(),
            name="pharmacy_search"
        ),
        path(
            "pharmacy-locator/pharmacy/<uuid:pharmacy_id>/",
            PharmacyDetailsView.as_view(),
            name="pharmacy_details"
        ),
        path(
            "pharmacy-locator/medication-availability/",
            MedicationAvailabilityView.as_view(),
            name="medication_availability"
        ),
        path(
            "pharmacy-locator/map/",
            PharmacyMapView.as_view(),
            name="pharmacy_map"
        ),
        path(
            "pharmacy-locator/inventory/<uuid:pharmacy_id>/",
            InventoryManagementView.as_view(),
            name="inventory_management"
        ),
    ]


@hooks.register("register_admin_menu_item")
def register_pharmacy_locator_menu_item():
    """Add Pharmacy Locator menu item to Wagtail admin menu."""
    return MenuItem(
        _("Pharmacy Locator"),
        reverse("pharmacy_locator_dashboard"),
        classname="icon icon-site",
        order=1200
    )


@hooks.register("insert_global_admin_css")
def pharmacy_locator_admin_css():
    """Add custom CSS for pharmacy locator admin interface."""
    return format_html(
        '<link rel="stylesheet" href="/static/wagtail_pharmacy_locator/css/locator-admin.css">'
        '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" '
        'integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>'
    )


@hooks.register("insert_global_admin_js")
def pharmacy_locator_admin_js():
    """Add custom JavaScript for pharmacy locator functionality."""
    return format_html(
        '<script src="/static/wagtail_pharmacy_locator/js/locator-admin.js"></script>'
        '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" '
        'integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>'
    )


@hooks.register("construct_main_menu")
def customize_pharmacy_locator_menu(request, menu_items):
    """Customize pharmacy locator menu based on user permissions."""
    # Hide inventory management for non-pharmacy staff
    if not request.user.groups.filter(
        name__in=['Pharmacy Staff', 'Pharmacy Managers']
    ).exists() and not request.user.is_staff:
        menu_items[:] = [
            item for item in menu_items 
            if not (item.url and 'medicationinventory' in item.url)
        ]


@hooks.register("before_create_pharmacy")
def log_pharmacy_creation(request, instance):
    """Log pharmacy creation for audit trail."""
    from medguard_backend.security.models import SecurityEvent
    
    SecurityEvent.objects.create(
        event_type='pharmacy_created',
        user=request.user,
        description=f"Pharmacy created: {instance.name} in {instance.city}",
        metadata={
            'pharmacy_id': str(instance.id),
            'pharmacy_name': instance.name,
            'city': instance.city,
            'pharmacy_type': instance.pharmacy_type
        }
    )


@hooks.register("before_edit_pharmacy")
def log_pharmacy_modification(request, instance):
    """Log pharmacy modifications for audit trail."""
    from medguard_backend.security.models import SecurityEvent
    
    SecurityEvent.objects.create(
        event_type='pharmacy_modified',
        user=request.user,
        description=f"Pharmacy modified: {instance.name}",
        metadata={
            'pharmacy_id': str(instance.id),
            'pharmacy_name': instance.name,
            'modifications': 'Pharmacy details updated'
        }
    )


@hooks.register("before_create_medicationinventory")
def log_inventory_creation(request, instance):
    """Log inventory creation for tracking."""
    from medguard_backend.security.models import SecurityEvent
    
    SecurityEvent.objects.create(
        event_type='inventory_created',
        user=request.user,
        description=f"Inventory created: {instance.medication_name} at {instance.pharmacy.name}",
        metadata={
            'inventory_id': str(instance.id),
            'pharmacy_id': str(instance.pharmacy.id),
            'medication_name': instance.medication_name,
            'quantity': instance.quantity_available
        }
    )


@hooks.register("construct_homepage_panels")
def add_pharmacy_locator_panel(request, panels):
    """Add pharmacy locator panel to Wagtail admin homepage."""
    from wagtail.admin.ui.components import Component
    
    if request.user.has_perm('wagtail_pharmacy_locator.view_pharmacy'):
        # Get pharmacy statistics
        total_pharmacies = Pharmacy.objects.filter(status='active').count()
        low_stock_items = MedicationInventory.objects.filter(
            quantity_available__lte=models.F('reorder_level')
        ).count()
        
        # Get recent searches
        recent_searches = PharmacySearchLog.objects.order_by('-created_at')[:3]
        
        panel_html = f"""
        <div class="panel summary nice-padding">
            <h3><a href="{reverse('pharmacy_locator_dashboard')}">Pharmacy Locator</a></h3>
            <div class="panel-content">
                <p><strong>Active Pharmacies:</strong> {total_pharmacies}</p>
                <p><strong>Low Stock Alerts:</strong> {low_stock_items}</p>
                <p><strong>Recent Searches:</strong> {recent_searches.count()}</p>
            </div>
        </div>
        """
        
        panels.append(Component(panel_html))


@hooks.register("register_permissions")
def register_pharmacy_locator_permissions():
    """Register custom permissions for pharmacy locator."""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    
    # Get content types
    pharmacy_ct = ContentType.objects.get_for_model(Pharmacy)
    inventory_ct = ContentType.objects.get_for_model(MedicationInventory)
    
    # Define custom permissions
    custom_permissions = [
        ('manage_pharmacy_inventory', 'Can manage pharmacy inventory', inventory_ct),
        ('view_pharmacy_analytics', 'Can view pharmacy search analytics', pharmacy_ct),
        ('verify_pharmacy_data', 'Can verify pharmacy information', pharmacy_ct),
        ('manage_pharmacy_integrations', 'Can manage pharmacy system integrations', pharmacy_ct),
    ]
    
    for codename, name, content_type in custom_permissions:
        Permission.objects.get_or_create(
            codename=codename,
            name=name,
            content_type=content_type
        )


@hooks.register("construct_settings_menu")
def add_pharmacy_locator_settings(request, menu_items):
    """Add pharmacy locator settings to admin settings menu."""
    from wagtail.admin.menu import MenuItem
    
    if request.user.has_perm('wagtail_pharmacy_locator.manage_pharmacy_integrations'):
        menu_items.append(
            MenuItem(
                _("Pharmacy Integrations"),
                reverse("pharmacy_locator_dashboard"),  # Replace with actual settings view
                classname="icon icon-cogs",
                order=900
            )
        )


@hooks.register("register_rich_text_features")
def register_pharmacy_locator_rich_text_features(features):
    """Register custom rich text features for pharmacy descriptions."""
    # Add pharmacy-specific rich text features
    features.register_editor_plugin(
        'hallo', 'pharmacy-highlight',
        HalloPlugin(
            js=['wagtail_pharmacy_locator/js/hallo-pharmacy-highlight.js'],
        )
    )


@hooks.register("construct_wagtail_userbar")
def add_pharmacy_locator_userbar(request, items):
    """Add pharmacy locator items to Wagtail userbar."""
    if not request.user.is_anonymous:
        # Add pharmacy search button
        items.append({
            'url': reverse('pharmacy_search'),
            'label': _('Find Pharmacy'),
            'classname': 'icon icon-site'
        })


# Custom dashboard widgets for pharmacy staff
@hooks.register("construct_homepage_summary_items")
def add_pharmacy_summary_items(request, summary_items):
    """Add pharmacy-specific summary items to homepage."""
    if request.user.groups.filter(name='Pharmacy Staff').exists():
        # Add low stock alert
        low_stock_count = MedicationInventory.objects.filter(
            quantity_available__lte=models.F('reorder_level'),
            pharmacy__in=request.user.managed_pharmacies.all()  # Assuming this relationship exists
        ).count()
        
        if low_stock_count > 0:
            summary_items.append({
                'icon': 'warning',
                'value': low_stock_count,
                'label': _('Low Stock Items'),
                'url': reverse('inventory_management', args=[request.user.managed_pharmacies.first().id])
            })


@hooks.register("after_create_pharmacyreview")
def handle_new_pharmacy_review(request, instance):
    """Handle new pharmacy reviews."""
    # Update pharmacy average rating
    pharmacy = instance.pharmacy
    reviews = PharmacyReview.objects.filter(pharmacy=pharmacy)
    
    avg_rating = reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating'] or 0
    total_reviews = reviews.count()
    
    pharmacy.average_rating = avg_rating
    pharmacy.total_reviews = total_reviews
    pharmacy.save(update_fields=['average_rating', 'total_reviews'])
    
    # Send notification to pharmacy if rating is low
    if instance.rating <= 2:
        from medguard_backend.medguard_notifications.services import NotificationService
        
        # Notify pharmacy managers about low rating
        pharmacy_managers = request.user.objects.filter(
            groups__name='Pharmacy Managers',
            managed_pharmacies=pharmacy
        )
        
        notification_service = NotificationService()
        for manager in pharmacy_managers:
            notification_service.send_notification(
                user=manager,
                title="Low Rating Alert",
                message=f"Your pharmacy {pharmacy.name} received a {instance.rating}-star review. Please review and address any concerns.",
                notification_type="low_rating_alert",
                metadata={
                    'pharmacy_id': str(pharmacy.id),
                    'review_id': str(instance.id),
                    'rating': instance.rating
                }
            )


@hooks.register("register_image_operations")
def register_pharmacy_image_operations():
    """Register custom image operations for pharmacy photos."""
    from wagtail.images.image_operations import DoNothingOperation
    
    # Add custom image operations for pharmacy photos
    # This could include automatic resizing, watermarking, etc.
    pass
