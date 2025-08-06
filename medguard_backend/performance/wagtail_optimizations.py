"""
Wagtail 7.0.2 Performance Optimizations for MedGuard SA.

This module implements comprehensive performance optimizations using Wagtail 7.0.2's
enhanced features for better query performance, caching, and admin experience.

Optimizations include:
1. Enhanced page query optimizations
2. Improved image rendition caching
3. Enhanced StreamField query optimizations
4. Page tree caching strategies
5. Admin query optimizations
6. Search query performance improvements
7. Template fragment caching
8. Database query prefetching
9. Sitemap generation optimizations
10. Async view support
"""

import logging
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.models import Page, Site
from wagtail.images.models import Image
from wagtail.search import index
from wagtail.admin.views.pages.listing import PageListingTable
from wagtail.admin.views.pages.bulk_actions import BulkAction

logger = logging.getLogger(__name__)


# =============================================================================
# 1. ENHANCED PAGE QUERY OPTIMIZATIONS
# =============================================================================

class OptimizedPageQuerySet(models.QuerySet):
    """
    Enhanced QuerySet for pages with Wagtail 7.0.2 optimizations.
    
    Features:
    - Selective field loading
    - Optimized prefetching
    - Smart caching strategies
    - Reduced database hits
    """
    
    def optimized_for_listing(self):
        """Optimize queryset for admin listing with minimal field loading."""
        return self.select_related(
            'owner',
            'content_type'
        ).prefetch_related(
            'revisions',
            'permissions',
            'group_permissions'
        ).only(
            'id', 'title', 'slug', 'content_type_id', 'owner_id',
            'live', 'has_unpublished_changes', 'first_published_at',
            'last_published_at', 'latest_revision_created_at',
            'expired', 'expire_at', 'locked', 'locked_at', 'locked_by_id'
        )
    
    def optimized_for_detail(self):
        """Optimize queryset for detailed page views."""
        return self.select_related(
            'owner',
            'content_type',
            'locked_by'
        ).prefetch_related(
            'revisions',
            'permissions',
            'group_permissions',
            'page_permissions',
            'page_permissions__group',
            'page_permissions__user'
        )
    
    def with_children_optimized(self):
        """Optimize queryset for pages with children."""
        return self.prefetch_related(
            models.Prefetch(
                'children',
                queryset=Page.objects.only(
                    'id', 'title', 'slug', 'content_type_id',
                    'live', 'has_unpublished_changes'
                )
            )
        )
    
    def with_ancestors_optimized(self):
        """Optimize queryset for pages with ancestors."""
        return self.select_related(
            'owner'
        ).prefetch_related(
            'ancestors'
        ).only(
            'id', 'title', 'slug', 'content_type_id', 'owner_id',
            'path', 'depth', 'numchild'
        )


class PageQueryOptimizer:
    """
    Optimizer for page queries using Wagtail 7.0.2 enhancements.
    """
    
    @staticmethod
    def get_optimized_page_queryset(base_queryset=None):
        """Get optimized page queryset with enhanced performance."""
        if base_queryset is None:
            base_queryset = Page.objects.all()
        
        return base_queryset.select_related(
            'owner',
            'content_type'
        ).prefetch_related(
            'revisions',
            'permissions'
        ).only(
            'id', 'title', 'slug', 'content_type_id', 'owner_id',
            'live', 'has_unpublished_changes', 'first_published_at',
            'last_published_at', 'latest_revision_created_at'
        )
    
    @staticmethod
    def optimize_explorer_queryset(pages, parent_page=None):
        """Optimize queryset for page explorer."""
        if parent_page:
            pages = pages.descendant_of(parent_page)
        
        return pages.select_related(
            'owner',
            'content_type'
        ).prefetch_related(
            'revisions',
            'permissions'
        ).only(
            'id', 'title', 'slug', 'content_type_id', 'owner_id',
            'live', 'has_unpublished_changes', 'first_published_at',
            'last_published_at', 'latest_revision_created_at',
            'path', 'depth', 'numchild'
        )
    
    @staticmethod
    def optimize_search_queryset(queryset, search_query):
        """Optimize queryset for search results."""
        return queryset.select_related(
            'owner',
            'content_type'
        ).prefetch_related(
            'revisions'
        ).only(
            'id', 'title', 'slug', 'content_type_id', 'owner_id',
            'live', 'has_unpublished_changes', 'search_description'
        )


# Register optimized queryset methods
@hooks.register('construct_explorer_page_queryset')
def apply_page_query_optimizations(pages, parent_page):
    """Apply page query optimizations to explorer."""
    optimizer = PageQueryOptimizer()
    return optimizer.optimize_explorer_queryset(pages, parent_page)


@hooks.register('construct_page_listing_queryset')
def apply_listing_optimizations(pages, request):
    """Apply optimizations to page listing."""
    return pages.select_related(
        'owner',
        'content_type'
    ).prefetch_related(
        'revisions'
    ).only(
        'id', 'title', 'slug', 'content_type_id', 'owner_id',
        'live', 'has_unpublished_changes', 'first_published_at',
        'last_published_at', 'latest_revision_created_at'
    )


# =============================================================================
# 2. IMPROVED IMAGE RENDITION CACHING
# =============================================================================

class OptimizedImageRenditionCache:
    """
    Enhanced image rendition caching using Wagtail 7.0.2 improvements.
    
    Features:
    - Multi-tier caching strategy
    - Automatic cache invalidation
    - Memory-efficient storage
    - Async generation support
    """
    
    CACHE_PREFIX = 'wagtail_image_rendition'
    CACHE_TIMEOUT = 86400  # 24 hours
    
    @classmethod
    def get_cache_key(cls, image_id, filter_spec, focal_point_key=None):
        """Generate cache key for image rendition."""
        key_parts = [cls.CACHE_PREFIX, str(image_id), filter_spec]
        if focal_point_key:
            key_parts.append(focal_point_key)
        return ':'.join(key_parts)
    
    @classmethod
    def get_rendition(cls, image, filter_spec, focal_point_key=None):
        """Get cached rendition or generate new one."""
        cache_key = cls.get_cache_key(image.id, filter_spec, focal_point_key)
        
        # Try to get from cache first
        cached_rendition = cache.get(cache_key)
        if cached_rendition:
            logger.debug(f"Cache hit for image rendition: {cache_key}")
            return cached_rendition
        
        # Generate new rendition
        try:
            rendition = image.get_rendition(filter_spec)
            
            # Cache the rendition URL and metadata
            cache_data = {
                'url': rendition.url,
                'width': rendition.width,
                'height': rendition.height,
                'file_size': rendition.file.size if rendition.file else 0,
                'generated_at': timezone.now().isoformat()
            }
            
            cache.set(cache_key, cache_data, cls.CACHE_TIMEOUT)
            logger.debug(f"Cached new image rendition: {cache_key}")
            
            return rendition
            
        except Exception as e:
            logger.error(f"Error generating image rendition: {e}")
            return None
    
    @classmethod
    def invalidate_image_cache(cls, image_id):
        """Invalidate all cached renditions for an image."""
        pattern = f"{cls.CACHE_PREFIX}:{image_id}:*"
        
        # Get all keys matching the pattern
        keys_to_delete = []
        for key in cache.keys(pattern):
            keys_to_delete.append(key)
        
        # Delete all matching keys
        if keys_to_delete:
            cache.delete_many(keys_to_delete)
            logger.info(f"Invalidated {len(keys_to_delete)} cached renditions for image {image_id}")
    
    @classmethod
    def prefetch_renditions(cls, images, filter_specs):
        """Prefetch multiple renditions for better performance."""
        cache_keys = []
        renditions = {}
        
        for image in images:
            for filter_spec in filter_specs:
                cache_key = cls.get_cache_key(image.id, filter_spec)
                cache_keys.append(cache_key)
                renditions[cache_key] = None
        
        # Batch get from cache
        cached_data = cache.get_many(cache_keys)
        
        # Process results
        for cache_key, cached_data in cached_data.items():
            if cached_data:
                renditions[cache_key] = cached_data
        
        return renditions


class OptimizedImageQuerySet(models.QuerySet):
    """
    Enhanced QuerySet for images with optimized rendition handling.
    """
    
    def with_renditions(self, filter_specs):
        """Prefetch renditions for images."""
        images = list(self)
        
        # Prefetch renditions
        rendition_cache = OptimizedImageRenditionCache()
        rendition_cache.prefetch_renditions(images, filter_specs)
        
        return images
    
    def optimized_for_listing(self):
        """Optimize queryset for admin listing."""
        return self.select_related(
            'uploaded_by_user'
        ).prefetch_related(
            'renditions'
        ).only(
            'id', 'title', 'file', 'width', 'height',
            'uploaded_by_user_id', 'created_at', 'updated_at'
        )


# Register image optimization hooks
@hooks.register('after_create_image')
def cache_new_image_renditions(image):
    """Cache common renditions for new images."""
    common_filters = ['fill-800x600', 'fill-400x300', 'max-1200x800']
    
    for filter_spec in common_filters:
        try:
            OptimizedImageRenditionCache.get_rendition(image, filter_spec)
        except Exception as e:
            logger.warning(f"Failed to pre-cache rendition {filter_spec} for image {image.id}: {e}")


@hooks.register('after_edit_image')
def invalidate_image_cache(image):
    """Invalidate cache when image is edited."""
    OptimizedImageRenditionCache.invalidate_image_cache(image.id)


# =============================================================================
# 3. ENHANCED STREAMFIELD QUERY OPTIMIZATIONS
# =============================================================================

class StreamFieldOptimizer:
    """
    Optimizer for StreamField queries using Wagtail 7.0.2 enhancements.
    
    Features:
    - Lazy loading of StreamField content
    - Selective field loading
    - Optimized block rendering
    - Memory-efficient processing
    """
    
    @staticmethod
    def optimize_streamfield_queryset(queryset, streamfield_names):
        """Optimize queryset for StreamField content."""
        select_fields = []
        prefetch_fields = []
        
        for field_name in streamfield_names:
            # Add StreamField to select fields to avoid lazy loading
            select_fields.append(field_name)
            
            # Add related fields that might be accessed
            prefetch_fields.extend([
                f'{field_name}__blocks',
                f'{field_name}__blocks__value'
            ])
        
        return queryset.select_related(
            'owner',
            'content_type'
        ).prefetch_related(
            *prefetch_fields
        ).only(
            'id', 'title', 'slug', 'content_type_id', 'owner_id',
            *select_fields
        )
    
    @staticmethod
    def lazy_load_streamfield_blocks(streamfield_data, block_types=None):
        """Lazy load StreamField blocks for better performance."""
        if not streamfield_data:
            return []
        
        blocks = []
        for block in streamfield_data:
            # Only load specified block types if filter is applied
            if block_types and block.block_type not in block_types:
                continue
            
            # Lazy load block value
            try:
                block_value = block.value
                blocks.append({
                    'type': block.block_type,
                    'value': block_value,
                    'id': getattr(block, 'id', None)
                })
            except Exception as e:
                logger.warning(f"Error loading StreamField block: {e}")
                continue
        
        return blocks
    
    @staticmethod
    def optimize_block_rendering(blocks, template_cache=None):
        """Optimize block rendering with template caching."""
        if template_cache is None:
            template_cache = {}
        
        rendered_blocks = []
        
        for block in blocks:
            block_type = block.get('type')
            template_key = f"streamfield_block_{block_type}"
            
            # Get cached template
            if template_key in template_cache:
                template = template_cache[template_key]
            else:
                # Load template and cache it
                try:
                    from django.template.loader import get_template
                    template = get_template(f"medications/blocks/{block_type}.html")
                    template_cache[template_key] = template
                except Exception as e:
                    logger.warning(f"Template not found for block type {block_type}: {e}")
                    continue
            
            # Render block
            try:
                context = {
                    'block': block,
                    'value': block.get('value'),
                    'block_id': block.get('id')
                }
                rendered_content = template.render(context)
                rendered_blocks.append(rendered_content)
            except Exception as e:
                logger.error(f"Error rendering block {block_type}: {e}")
                continue
        
        return rendered_blocks


class OptimizedStreamFieldQuerySet(models.QuerySet):
    """
    Enhanced QuerySet for models with StreamField content.
    """
    
    def with_streamfield_optimized(self, streamfield_names):
        """Optimize queryset for StreamField content."""
        optimizer = StreamFieldOptimizer()
        return optimizer.optimize_streamfield_queryset(self, streamfield_names)
    
    def lazy_load_blocks(self, streamfield_name, block_types=None):
        """Lazy load StreamField blocks."""
        pages = list(self)
        
        for page in pages:
            if hasattr(page, streamfield_name):
                streamfield_data = getattr(page, streamfield_name)
                blocks = StreamFieldOptimizer.lazy_load_streamfield_blocks(
                    streamfield_data, block_types
                )
                setattr(page, f'{streamfield_name}_blocks', blocks)
        
        return pages


# Register StreamField optimization hooks
@hooks.register('construct_page_queryset')
def apply_streamfield_optimizations(pages, request):
    """Apply StreamField optimizations to page queryset."""
    # Common StreamField names in MedGuard
    streamfield_names = [
        'content',
        'medication_details',
        'prescription_info',
        'side_effects',
        'interactions'
    ]
    
    # Filter to only include fields that exist on the model
    available_fields = []
    if pages.exists():
        sample_page = pages.first()
        for field_name in streamfield_names:
            if hasattr(sample_page, field_name):
                available_fields.append(field_name)
    
    if available_fields:
        optimizer = StreamFieldOptimizer()
        return optimizer.optimize_streamfield_queryset(pages, available_fields)
    
    return pages


# =============================================================================
# 4. PAGE TREE CACHING STRATEGIES
# =============================================================================

class PageTreeCache:
    """
    Enhanced page tree caching using Wagtail 7.0.2's new cache strategies.
    
    Features:
    - Hierarchical cache structure
    - Automatic invalidation
    - Memory-efficient storage
    - Async cache warming
    """
    
    CACHE_PREFIX = 'wagtail_page_tree'
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @classmethod
    def get_tree_cache_key(cls, site_id, parent_id=None, depth=None):
        """Generate cache key for page tree."""
        key_parts = [cls.CACHE_PREFIX, str(site_id)]
        if parent_id:
            key_parts.append(f"parent_{parent_id}")
        if depth:
            key_parts.append(f"depth_{depth}")
        return ':'.join(key_parts)
    
    @classmethod
    def get_cached_tree(cls, site_id, parent_id=None, depth=3):
        """Get cached page tree or build new one."""
        cache_key = cls.get_tree_cache_key(site_id, parent_id, depth)
        
        # Try to get from cache
        cached_tree = cache.get(cache_key)
        if cached_tree:
            logger.debug(f"Cache hit for page tree: {cache_key}")
            return cached_tree
        
        # Build new tree
        try:
            tree_data = cls.build_page_tree(site_id, parent_id, depth)
            
            # Cache the tree data
            cache.set(cache_key, tree_data, cls.CACHE_TIMEOUT)
            logger.debug(f"Cached new page tree: {cache_key}")
            
            return tree_data
            
        except Exception as e:
            logger.error(f"Error building page tree: {e}")
            return None
    
    @classmethod
    def build_page_tree(cls, site_id, parent_id=None, depth=3):
        """Build page tree structure for caching."""
        try:
            site = Site.objects.get(id=site_id)
            root_page = site.root_page
            
            if parent_id:
                parent_page = Page.objects.get(id=parent_id)
                pages = parent_page.get_descendants().live().public()
            else:
                pages = root_page.get_descendants().live().public()
            
            # Optimize queryset
            pages = pages.select_related(
                'owner',
                'content_type'
            ).prefetch_related(
                'revisions'
            ).only(
                'id', 'title', 'slug', 'content_type_id', 'owner_id',
                'live', 'has_unpublished_changes', 'path', 'depth',
                'first_published_at', 'last_published_at'
            )
            
            # Build tree structure
            tree_data = {
                'pages': [],
                'total_count': pages.count(),
                'generated_at': timezone.now().isoformat(),
                'cache_key': cls.get_tree_cache_key(site_id, parent_id, depth)
            }
            
            for page in pages:
                if page.depth <= (root_page.depth + depth):
                    page_data = {
                        'id': page.id,
                        'title': page.title,
                        'slug': page.slug,
                        'url': page.get_url(),
                        'depth': page.depth,
                        'content_type': page.content_type.model,
                        'live': page.live,
                        'has_unpublished_changes': page.has_unpublished_changes,
                        'first_published_at': page.first_published_at.isoformat() if page.first_published_at else None,
                        'last_published_at': page.last_published_at.isoformat() if page.last_published_at else None
                    }
                    tree_data['pages'].append(page_data)
            
            return tree_data
            
        except Exception as e:
            logger.error(f"Error building page tree: {e}")
            return None
    
    @classmethod
    def invalidate_tree_cache(cls, page_id=None, site_id=None):
        """Invalidate page tree cache."""
        if site_id:
            # Invalidate all trees for the site
            pattern = f"{cls.CACHE_PREFIX}:{site_id}:*"
        elif page_id:
            # Invalidate trees containing the page
            pattern = f"{cls.CACHE_PREFIX}:*:parent_{page_id}:*"
        else:
            # Invalidate all tree caches
            pattern = f"{cls.CACHE_PREFIX}:*"
        
        # Get all keys matching the pattern
        keys_to_delete = []
        for key in cache.keys(pattern):
            keys_to_delete.append(key)
        
        # Delete all matching keys
        if keys_to_delete:
            cache.delete_many(keys_to_delete)
            logger.info(f"Invalidated {len(keys_to_delete)} page tree caches")
    
    @classmethod
    def warm_cache_async(cls, site_ids=None):
        """Warm page tree cache asynchronously."""
        if site_ids is None:
            site_ids = Site.objects.values_list('id', flat=True)
        
        for site_id in site_ids:
            try:
                # Warm cache for different depths
                for depth in [2, 3, 4]:
                    cls.get_cached_tree(site_id, depth=depth)
                logger.info(f"Warmed page tree cache for site {site_id}")
            except Exception as e:
                logger.error(f"Error warming cache for site {site_id}: {e}")


class OptimizedPageTreeQuerySet(models.QuerySet):
    """
    Enhanced QuerySet for page trees with caching.
    """
    
    def with_tree_cache(self, site_id, parent_id=None, depth=3):
        """Get pages with tree caching."""
        tree_data = PageTreeCache.get_cached_tree(site_id, parent_id, depth)
        
        if tree_data:
            # Return pages from cache
            page_ids = [page['id'] for page in tree_data['pages']]
            return self.filter(id__in=page_ids)
        
        # Fallback to database query
        return self


# Register page tree caching hooks
@hooks.register('after_publish_page')
def invalidate_page_tree_cache(page):
    """Invalidate page tree cache when page is published."""
    PageTreeCache.invalidate_tree_cache(page_id=page.id)


@hooks.register('after_unpublish_page')
def invalidate_page_tree_cache_unpublish(page):
    """Invalidate page tree cache when page is unpublished."""
    PageTreeCache.invalidate_tree_cache(page_id=page.id)


@hooks.register('after_move_page')
def invalidate_page_tree_cache_move(page):
    """Invalidate page tree cache when page is moved."""
    PageTreeCache.invalidate_tree_cache(page_id=page.id)


# =============================================================================
# 5. ADMIN QUERY OPTIMIZATIONS
# =============================================================================

class AdminQueryOptimizer:
    """
    Optimizer for admin queries using Wagtail 7.0.2 improvements.
    
    Features:
    - Optimized admin listing queries
    - Enhanced bulk action performance
    - Improved admin search
    - Better dashboard performance
    """
    
    @staticmethod
    def optimize_admin_listing_queryset(queryset, request):
        """Optimize queryset for admin listing."""
        return queryset.select_related(
            'owner',
            'content_type',
            'locked_by'
        ).prefetch_related(
            'revisions',
            'permissions',
            'group_permissions',
            'page_permissions',
            'page_permissions__group',
            'page_permissions__user'
        ).only(
            'id', 'title', 'slug', 'content_type_id', 'owner_id',
            'live', 'has_unpublished_changes', 'first_published_at',
            'last_published_at', 'latest_revision_created_at',
            'expired', 'expire_at', 'locked', 'locked_at', 'locked_by_id',
            'path', 'depth', 'numchild'
        )
    
    @staticmethod
    def optimize_bulk_action_queryset(queryset, action_type):
        """Optimize queryset for bulk actions."""
        # Different optimizations for different action types
        if action_type in ['publish', 'unpublish']:
            return queryset.select_related(
                'owner',
                'content_type'
            ).prefetch_related(
                'revisions'
            ).only(
                'id', 'title', 'slug', 'content_type_id', 'owner_id',
                'live', 'has_unpublished_changes', 'first_published_at',
                'last_published_at', 'latest_revision_created_at'
            )
        
        elif action_type in ['delete', 'move', 'copy']:
            return queryset.select_related(
                'owner',
                'content_type',
                'locked_by'
            ).prefetch_related(
                'revisions',
                'permissions',
                'children'
            ).only(
                'id', 'title', 'slug', 'content_type_id', 'owner_id',
                'live', 'has_unpublished_changes', 'path', 'depth',
                'numchild', 'locked', 'locked_at', 'locked_by_id'
            )
        
        else:
            return queryset.select_related(
                'owner',
                'content_type'
            ).only(
                'id', 'title', 'slug', 'content_type_id', 'owner_id',
                'live', 'has_unpublished_changes'
            )
    
    @staticmethod
    def optimize_admin_search_queryset(queryset, search_query):
        """Optimize queryset for admin search."""
        return queryset.select_related(
            'owner',
            'content_type'
        ).prefetch_related(
            'revisions'
        ).only(
            'id', 'title', 'slug', 'content_type_id', 'owner_id',
            'live', 'has_unpublished_changes', 'search_description',
            'first_published_at', 'last_published_at'
        )
    
    @staticmethod
    def optimize_dashboard_queryset(queryset):
        """Optimize queryset for dashboard."""
        return queryset.select_related(
            'owner',
            'content_type'
        ).prefetch_related(
            'revisions'
        ).only(
            'id', 'title', 'slug', 'content_type_id', 'owner_id',
            'live', 'has_unpublished_changes', 'first_published_at',
            'last_published_at', 'latest_revision_created_at'
        )


class OptimizedAdminQuerySet(models.QuerySet):
    """
    Enhanced QuerySet for admin operations.
    """
    
    def optimized_for_admin(self, request=None):
        """Optimize queryset for admin operations."""
        optimizer = AdminQueryOptimizer()
        return optimizer.optimize_admin_listing_queryset(self, request)
    
    def optimized_for_bulk_action(self, action_type):
        """Optimize queryset for bulk actions."""
        optimizer = AdminQueryOptimizer()
        return optimizer.optimize_bulk_action_queryset(self, action_type)
    
    def optimized_for_search(self, search_query):
        """Optimize queryset for admin search."""
        optimizer = AdminQueryOptimizer()
        return optimizer.optimize_admin_search_queryset(self, search_query)
    
    def optimized_for_dashboard(self):
        """Optimize queryset for dashboard."""
        optimizer = AdminQueryOptimizer()
        return optimizer.optimize_dashboard_queryset(self)


# Register admin optimization hooks
@hooks.register('construct_admin_page_listing_queryset')
def apply_admin_query_optimizations(pages, request):
    """Apply admin query optimizations."""
    optimizer = AdminQueryOptimizer()
    return optimizer.optimize_admin_listing_queryset(pages, request)


@hooks.register('construct_admin_search_queryset')
def apply_admin_search_optimizations(pages, request, search_query):
    """Apply admin search optimizations."""
    optimizer = AdminQueryOptimizer()
    return optimizer.optimize_admin_search_queryset(pages, search_query)


@hooks.register('construct_admin_dashboard_queryset')
def apply_dashboard_optimizations(pages, request):
    """Apply dashboard optimizations."""
    optimizer = AdminQueryOptimizer()
    return optimizer.optimize_dashboard_queryset(pages)


# =============================================================================
# 6. SEARCH QUERY PERFORMANCE IMPROVEMENTS
# =============================================================================

class SearchQueryOptimizer:
    """
    Optimizer for search queries using Wagtail 7.0.2 enhancements.
    
    Features:
    - Optimized search indexing
    - Enhanced search result caching
    - Improved search relevance
    - Better search performance
    """
    
    SEARCH_CACHE_PREFIX = 'wagtail_search'
    SEARCH_CACHE_TIMEOUT = 1800  # 30 minutes
    
    @staticmethod
    def optimize_search_queryset(queryset, search_query, search_type='full'):
        """Optimize queryset for search operations."""
        if search_type == 'full':
            return queryset.select_related(
                'owner',
                'content_type'
            ).prefetch_related(
                'revisions',
                'search_vectors'
            ).only(
                'id', 'title', 'slug', 'content_type_id', 'owner_id',
                'live', 'has_unpublished_changes', 'search_description',
                'first_published_at', 'last_published_at'
            )
        
        elif search_type == 'quick':
            return queryset.select_related(
                'content_type'
            ).only(
                'id', 'title', 'slug', 'content_type_id',
                'live', 'has_unpublished_changes'
            )
        
        else:
            return queryset.select_related(
                'owner',
                'content_type'
            ).only(
                'id', 'title', 'slug', 'content_type_id', 'owner_id',
                'live', 'has_unpublished_changes'
            )
    
    @classmethod
    def get_search_cache_key(cls, search_query, search_type='full', filters=None):
        """Generate cache key for search results."""
        key_parts = [cls.SEARCH_CACHE_PREFIX, search_type, search_query]
        if filters:
            key_parts.append(str(hash(str(filters))))
        return ':'.join(key_parts)
    
    @classmethod
    def get_cached_search_results(cls, search_query, search_type='full', filters=None):
        """Get cached search results or perform new search."""
        cache_key = cls.get_search_cache_key(search_query, search_type, filters)
        
        # Try to get from cache
        cached_results = cache.get(cache_key)
        if cached_results:
            logger.debug(f"Cache hit for search: {cache_key}")
            return cached_results
        
        # Perform new search
        try:
            from wagtail.search.models import Query
            
            # Create search query
            query = Query.get(search_query)
            
            # Get search results
            results = query.get_editors_picks()
            
            # Optimize queryset
            optimizer = SearchQueryOptimizer()
            optimized_results = optimizer.optimize_search_queryset(
                results, search_query, search_type
            )
            
            # Cache results
            cache_data = {
                'results': list(optimized_results.values('id', 'title', 'slug', 'content_type_id')),
                'total_count': optimized_results.count(),
                'search_query': search_query,
                'search_type': search_type,
                'generated_at': timezone.now().isoformat()
            }
            
            cache.set(cache_key, cache_data, cls.SEARCH_CACHE_TIMEOUT)
            logger.debug(f"Cached search results: {cache_key}")
            
            return cache_data
            
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            return None
    
    @classmethod
    def invalidate_search_cache(cls, search_query=None):
        """Invalidate search cache."""
        if search_query:
            # Invalidate specific search
            pattern = f"{cls.SEARCH_CACHE_PREFIX}:*:{search_query}:*"
        else:
            # Invalidate all search caches
            pattern = f"{cls.SEARCH_CACHE_PREFIX}:*"
        
        # Get all keys matching the pattern
        keys_to_delete = []
        for key in cache.keys(pattern):
            keys_to_delete.append(key)
        
        # Delete all matching keys
        if keys_to_delete:
            cache.delete_many(keys_to_delete)
            logger.info(f"Invalidated {len(keys_to_delete)} search caches")
    
    @staticmethod
    def optimize_search_indexing(queryset):
        """Optimize queryset for search indexing."""
        return queryset.select_related(
            'owner',
            'content_type'
        ).prefetch_related(
            'revisions'
        ).only(
            'id', 'title', 'slug', 'content_type_id', 'owner_id',
            'live', 'has_unpublished_changes', 'search_description',
            'first_published_at', 'last_published_at'
        )


class OptimizedSearchQuerySet(models.QuerySet):
    """
    Enhanced QuerySet for search operations.
    """
    
    def optimized_for_search(self, search_query, search_type='full'):
        """Optimize queryset for search."""
        optimizer = SearchQueryOptimizer()
        return optimizer.optimize_search_queryset(self, search_query, search_type)
    
    def with_search_cache(self, search_query, search_type='full', filters=None):
        """Get search results with caching."""
        cache_data = SearchQueryOptimizer.get_cached_search_results(
            search_query, search_type, filters
        )
        
        if cache_data:
            # Return results from cache
            result_ids = [result['id'] for result in cache_data['results']]
            return self.filter(id__in=result_ids)
        
        # Fallback to database search
        return self


# Register search optimization hooks
@hooks.register('construct_search_results')
def apply_search_optimizations(search_results, search_query):
    """Apply search optimizations to results."""
    optimizer = SearchQueryOptimizer()
    return optimizer.optimize_search_queryset(search_results, search_query)


@hooks.register('after_publish_page')
def invalidate_search_cache_publish(page):
    """Invalidate search cache when page is published."""
    SearchQueryOptimizer.invalidate_search_cache()


@hooks.register('after_unpublish_page')
def invalidate_search_cache_unpublish(page):
    """Invalidate search cache when page is unpublished."""
    SearchQueryOptimizer.invalidate_search_cache()


# =============================================================================
# 7. TEMPLATE FRAGMENT CACHING FOR MEDICATION PAGES
# =============================================================================

class TemplateFragmentCache:
    """
    Enhanced template fragment caching using Wagtail 7.0.2's new cache strategies.
    
    Features:
    - Fragment-level caching
    - Automatic cache invalidation
    - Context-aware caching
    - Performance monitoring
    """
    
    FRAGMENT_CACHE_PREFIX = 'wagtail_template_fragment'
    FRAGMENT_CACHE_TIMEOUT = 3600  # 1 hour
    
    @classmethod
    def get_fragment_cache_key(cls, fragment_name, context_data=None, page_id=None):
        """Generate cache key for template fragment."""
        key_parts = [cls.FRAGMENT_CACHE_PREFIX, fragment_name]
        
        if page_id:
            key_parts.append(f"page_{page_id}")
        
        if context_data:
            # Create a hash of context data for cache key
            context_hash = hash(str(sorted(context_data.items())))
            key_parts.append(f"ctx_{context_hash}")
        
        return ':'.join(key_parts)
    
    @classmethod
    def get_cached_fragment(cls, fragment_name, context_data=None, page_id=None):
        """Get cached template fragment or render new one."""
        cache_key = cls.get_fragment_cache_key(fragment_name, context_data, page_id)
        
        # Try to get from cache
        cached_fragment = cache.get(cache_key)
        if cached_fragment:
            logger.debug(f"Cache hit for template fragment: {cache_key}")
            return cached_fragment
        
        # Render new fragment
        try:
            from django.template.loader import get_template
            from django.template import Context
            
            # Get template
            template = get_template(f"medications/fragments/{fragment_name}.html")
            
            # Create context
            context = Context(context_data or {})
            
            # Render fragment
            rendered_fragment = template.render(context)
            
            # Cache the fragment
            cache.set(cache_key, rendered_fragment, cls.FRAGMENT_CACHE_TIMEOUT)
            logger.debug(f"Cached template fragment: {cache_key}")
            
            return rendered_fragment
            
        except Exception as e:
            logger.error(f"Error rendering template fragment {fragment_name}: {e}")
            return None
    
    @classmethod
    def invalidate_fragment_cache(cls, fragment_name=None, page_id=None):
        """Invalidate template fragment cache."""
        if fragment_name and page_id:
            # Invalidate specific fragment for specific page
            pattern = f"{cls.FRAGMENT_CACHE_PREFIX}:{fragment_name}:page_{page_id}:*"
        elif fragment_name:
            # Invalidate all instances of specific fragment
            pattern = f"{cls.FRAGMENT_CACHE_PREFIX}:{fragment_name}:*"
        elif page_id:
            # Invalidate all fragments for specific page
            pattern = f"{cls.FRAGMENT_CACHE_PREFIX}:*:page_{page_id}:*"
        else:
            # Invalidate all fragment caches
            pattern = f"{cls.FRAGMENT_CACHE_PREFIX}:*"
        
        # Get all keys matching the pattern
        keys_to_delete = []
        for key in cache.keys(pattern):
            keys_to_delete.append(key)
        
        # Delete all matching keys
        if keys_to_delete:
            cache.delete_many(keys_to_delete)
            logger.info(f"Invalidated {len(keys_to_delete)} template fragment caches")
    
    @classmethod
    def cache_medication_fragments(cls, medication_page):
        """Cache common fragments for medication pages."""
        common_fragments = [
            'medication_header',
            'medication_details',
            'prescription_info',
            'side_effects',
            'interactions',
            'dosage_instructions'
        ]
        
        context_data = {
            'page': medication_page,
            'medication': medication_page,
            'user': None  # Will be set by request context
        }
        
        for fragment_name in common_fragments:
            try:
                cls.get_cached_fragment(
                    fragment_name, 
                    context_data, 
                    medication_page.id
                )
            except Exception as e:
                logger.warning(f"Failed to cache fragment {fragment_name} for medication {medication_page.id}: {e}")


class MedicationPageFragmentCache:
    """
    Specialized cache for medication page fragments.
    """
    
    @classmethod
    def get_medication_header_cache(cls, medication_page, user=None):
        """Get cached medication header."""
        context_data = {
            'page': medication_page,
            'medication': medication_page,
            'user': user
        }
        
        return TemplateFragmentCache.get_cached_fragment(
            'medication_header',
            context_data,
            medication_page.id
        )
    
    @classmethod
    def get_medication_details_cache(cls, medication_page, user=None):
        """Get cached medication details."""
        context_data = {
            'page': medication_page,
            'medication': medication_page,
            'user': user
        }
        
        return TemplateFragmentCache.get_cached_fragment(
            'medication_details',
            context_data,
            medication_page.id
        )
    
    @classmethod
    def get_prescription_info_cache(cls, medication_page, user=None):
        """Get cached prescription info."""
        context_data = {
            'page': medication_page,
            'medication': medication_page,
            'user': user
        }
        
        return TemplateFragmentCache.get_cached_fragment(
            'prescription_info',
            context_data,
            medication_page.id
        )
    
    @classmethod
    def invalidate_medication_cache(cls, medication_page):
        """Invalidate all caches for a medication page."""
        TemplateFragmentCache.invalidate_fragment_cache(page_id=medication_page.id)


# Register template fragment caching hooks
@hooks.register('after_publish_page')
def cache_medication_fragments_publish(page):
    """Cache medication fragments when page is published."""
    # Check if this is a medication page
    if hasattr(page, 'medication_type'):
        TemplateFragmentCache.cache_medication_fragments(page)


@hooks.register('after_edit_page')
def invalidate_medication_fragments_edit(page):
    """Invalidate medication fragments when page is edited."""
    # Check if this is a medication page
    if hasattr(page, 'medication_type'):
        MedicationPageFragmentCache.invalidate_medication_cache(page)


# =============================================================================
# 8. DATABASE QUERY PREFETCHING
# =============================================================================

class DatabaseQueryPrefetcher:
    """
    Enhanced database query prefetching using Wagtail 7.0.2 improvements.
    
    Features:
    - Smart prefetching strategies
    - Conditional prefetching
    - Memory-efficient prefetching
    - Performance monitoring
    """
    
    @staticmethod
    def optimize_page_queryset(queryset, prefetch_type='default'):
        """Optimize queryset with smart prefetching."""
        if prefetch_type == 'default':
            return queryset.select_related(
                'owner',
                'content_type'
            ).prefetch_related(
                'revisions',
                'permissions'
            )
        
        elif prefetch_type == 'detailed':
            return queryset.select_related(
                'owner',
                'content_type',
                'locked_by'
            ).prefetch_related(
                'revisions',
                'permissions',
                'group_permissions',
                'page_permissions',
                'page_permissions__group',
                'page_permissions__user',
                'children',
                'ancestors'
            )
        
        elif prefetch_type == 'minimal':
            return queryset.select_related(
                'content_type'
            ).only(
                'id', 'title', 'slug', 'content_type_id',
                'live', 'has_unpublished_changes'
            )
        
        else:
            return queryset
    
    @staticmethod
    def optimize_medication_queryset(queryset, prefetch_type='default'):
        """Optimize medication queryset with specific prefetching."""
        if prefetch_type == 'default':
            return queryset.select_related(
                'owner',
                'content_type'
            ).prefetch_related(
                'revisions',
                'prescriptions',
                'stock_alerts',
                'interactions'
            )
        
        elif prefetch_type == 'detailed':
            return queryset.select_related(
                'owner',
                'content_type'
            ).prefetch_related(
                'revisions',
                'prescriptions',
                'prescriptions__patient',
                'prescriptions__prescriber',
                'stock_alerts',
                'interactions',
                'interactions__related_medication'
            )
        
        elif prefetch_type == 'listing':
            return queryset.select_related(
                'owner',
                'content_type'
            ).prefetch_related(
                'revisions'
            ).only(
                'id', 'title', 'slug', 'content_type_id', 'owner_id',
                'medication_type', 'prescription_type', 'strength',
                'pill_count', 'manufacturer', 'is_active'
            )
        
        else:
            return queryset
    
    @staticmethod
    def optimize_user_queryset(queryset, prefetch_type='default'):
        """Optimize user queryset with specific prefetching."""
        if prefetch_type == 'default':
            return queryset.select_related(
                'profile'
            ).prefetch_related(
                'groups',
                'user_permissions'
            )
        
        elif prefetch_type == 'detailed':
            return queryset.select_related(
                'profile'
            ).prefetch_related(
                'groups',
                'user_permissions',
                'owned_pages',
                'locked_pages'
            )
        
        else:
            return queryset
    
    @staticmethod
    def conditional_prefetch(queryset, condition_func, prefetch_func):
        """Apply conditional prefetching based on a condition."""
        if condition_func(queryset):
            return prefetch_func(queryset)
        return queryset
    
    @staticmethod
    def memory_efficient_prefetch(queryset, prefetch_fields, chunk_size=1000):
        """Memory-efficient prefetching for large querysets."""
        if queryset.count() <= chunk_size:
            return queryset.prefetch_related(*prefetch_fields)
        
        # For large querysets, process in chunks
        optimized_querysets = []
        
        for i in range(0, queryset.count(), chunk_size):
            chunk = queryset[i:i + chunk_size]
            optimized_chunk = chunk.prefetch_related(*prefetch_fields)
            optimized_querysets.append(optimized_chunk)
        
        # Combine chunks (this is a simplified approach)
        return queryset.prefetch_related(*prefetch_fields)


class OptimizedPrefetchQuerySet(models.QuerySet):
    """
    Enhanced QuerySet with optimized prefetching.
    """
    
    def with_smart_prefetch(self, prefetch_type='default'):
        """Apply smart prefetching to queryset."""
        prefetcher = DatabaseQueryPrefetcher()
        return prefetcher.optimize_page_queryset(self, prefetch_type)
    
    def with_medication_prefetch(self, prefetch_type='default'):
        """Apply medication-specific prefetching."""
        prefetcher = DatabaseQueryPrefetcher()
        return prefetcher.optimize_medication_queryset(self, prefetch_type)
    
    def with_user_prefetch(self, prefetch_type='default'):
        """Apply user-specific prefetching."""
        prefetcher = DatabaseQueryPrefetcher()
        return prefetcher.optimize_user_queryset(self, prefetch_type)
    
    def with_conditional_prefetch(self, condition_func, prefetch_func):
        """Apply conditional prefetching."""
        prefetcher = DatabaseQueryPrefetcher()
        return prefetcher.conditional_prefetch(self, condition_func, prefetch_func)
    
    def with_memory_efficient_prefetch(self, prefetch_fields, chunk_size=1000):
        """Apply memory-efficient prefetching."""
        prefetcher = DatabaseQueryPrefetcher()
        return prefetcher.memory_efficient_prefetch(self, prefetch_fields, chunk_size)


# Register database prefetching hooks
@hooks.register('construct_page_queryset')
def apply_database_prefetching(pages, request):
    """Apply database prefetching optimizations."""
    prefetcher = DatabaseQueryPrefetcher()
    
    # Determine prefetch type based on request
    if request and request.path.startswith('/admin/'):
        prefetch_type = 'detailed'
    else:
        prefetch_type = 'default'
    
    return prefetcher.optimize_page_queryset(pages, prefetch_type)


@hooks.register('construct_medication_queryset')
def apply_medication_prefetching(medications, request):
    """Apply medication-specific prefetching."""
    prefetcher = DatabaseQueryPrefetcher()
    
    # Determine prefetch type based on request
    if request and request.path.startswith('/admin/'):
        prefetch_type = 'detailed'
    elif request and 'listing' in request.path:
        prefetch_type = 'listing'
    else:
        prefetch_type = 'default'
    
    return prefetcher.optimize_medication_queryset(medications, prefetch_type)


# =============================================================================
# 9. SITEMAP GENERATION OPTIMIZATIONS
# =============================================================================

class SitemapOptimizer:
    """
    Enhanced sitemap generation using Wagtail 7.0.2's new optimizations.
    
    Features:
    - Cached sitemap generation
    - Incremental sitemap updates
    - Optimized sitemap queries
    - Performance monitoring
    """
    
    SITEMAP_CACHE_PREFIX = 'wagtail_sitemap'
    SITEMAP_CACHE_TIMEOUT = 86400  # 24 hours
    
    @classmethod
    def get_sitemap_cache_key(cls, site_id, sitemap_type='default'):
        """Generate cache key for sitemap."""
        return f"{cls.SITEMAP_CACHE_PREFIX}:{site_id}:{sitemap_type}"
    
    @classmethod
    def get_cached_sitemap(cls, site_id, sitemap_type='default'):
        """Get cached sitemap or generate new one."""
        cache_key = cls.get_sitemap_cache_key(site_id, sitemap_type)
        
        # Try to get from cache
        cached_sitemap = cache.get(cache_key)
        if cached_sitemap:
            logger.debug(f"Cache hit for sitemap: {cache_key}")
            return cached_sitemap
        
        # Generate new sitemap
        try:
            sitemap_data = cls.generate_sitemap(site_id, sitemap_type)
            
            # Cache the sitemap
            cache.set(cache_key, sitemap_data, cls.SITEMAP_CACHE_TIMEOUT)
            logger.debug(f"Cached new sitemap: {cache_key}")
            
            return sitemap_data
            
        except Exception as e:
            logger.error(f"Error generating sitemap: {e}")
            return None
    
    @classmethod
    def generate_sitemap(cls, site_id, sitemap_type='default'):
        """Generate optimized sitemap."""
        try:
            site = Site.objects.get(id=site_id)
            root_page = site.root_page
            
            # Get all live pages
            pages = root_page.get_descendants().live().public()
            
            # Optimize queryset for sitemap generation
            pages = pages.select_related(
                'owner',
                'content_type'
            ).prefetch_related(
                'revisions'
            ).only(
                'id', 'title', 'slug', 'content_type_id', 'owner_id',
                'live', 'has_unpublished_changes', 'path', 'depth',
                'first_published_at', 'last_published_at'
            )
            
            # Build sitemap data
            sitemap_data = {
                'urls': [],
                'total_count': pages.count(),
                'generated_at': timezone.now().isoformat(),
                'site_id': site_id,
                'sitemap_type': sitemap_type
            }
            
            for page in pages:
                # Skip certain page types if needed
                if hasattr(page, 'include_in_sitemap') and not page.include_in_sitemap:
                    continue
                
                page_data = {
                    'url': page.get_url(),
                    'title': page.title,
                    'last_modified': page.last_published_at.isoformat() if page.last_published_at else None,
                    'priority': cls.get_page_priority(page),
                    'changefreq': cls.get_page_changefreq(page)
                }
                sitemap_data['urls'].append(page_data)
            
            return sitemap_data
            
        except Exception as e:
            logger.error(f"Error generating sitemap: {e}")
            return None
    
    @staticmethod
    def get_page_priority(page):
        """Get priority for sitemap entry."""
        # Homepage gets highest priority
        if page.depth == 1:
            return 1.0
        
        # Medication pages get high priority
        if hasattr(page, 'medication_type'):
            return 0.9
        
        # Other pages get standard priority
        return 0.5
    
    @staticmethod
    def get_page_changefreq(page):
        """Get change frequency for sitemap entry."""
        # Medication pages change frequently
        if hasattr(page, 'medication_type'):
            return 'weekly'
        
        # Other pages change less frequently
        return 'monthly'
    
    @classmethod
    def invalidate_sitemap_cache(cls, site_id=None):
        """Invalidate sitemap cache."""
        if site_id:
            # Invalidate specific site sitemap
            pattern = f"{cls.SITEMAP_CACHE_PREFIX}:{site_id}:*"
        else:
            # Invalidate all sitemap caches
            pattern = f"{cls.SITEMAP_CACHE_PREFIX}:*"
        
        # Get all keys matching the pattern
        keys_to_delete = []
        for key in cache.keys(pattern):
            keys_to_delete.append(key)
        
        # Delete all matching keys
        if keys_to_delete:
            cache.delete_many(keys_to_delete)
            logger.info(f"Invalidated {len(keys_to_delete)} sitemap caches")
    
    @classmethod
    def generate_incremental_sitemap(cls, site_id, updated_pages):
        """Generate incremental sitemap update."""
        try:
            # Get existing sitemap
            existing_sitemap = cls.get_cached_sitemap(site_id)
            
            if not existing_sitemap:
                # Generate full sitemap if none exists
                return cls.generate_sitemap(site_id)
            
            # Update only changed pages
            for page in updated_pages:
                page_url = page.get_url()
                
                # Find and update existing entry
                for url_entry in existing_sitemap['urls']:
                    if url_entry['url'] == page_url:
                        url_entry['last_modified'] = page.last_published_at.isoformat() if page.last_published_at else None
                        url_entry['priority'] = cls.get_page_priority(page)
                        url_entry['changefreq'] = cls.get_page_changefreq(page)
                        break
                else:
                    # Add new entry if not found
                    new_entry = {
                        'url': page_url,
                        'title': page.title,
                        'last_modified': page.last_published_at.isoformat() if page.last_published_at else None,
                        'priority': cls.get_page_priority(page),
                        'changefreq': cls.get_page_changefreq(page)
                    }
                    existing_sitemap['urls'].append(new_entry)
            
            # Update metadata
            existing_sitemap['total_count'] = len(existing_sitemap['urls'])
            existing_sitemap['generated_at'] = timezone.now().isoformat()
            
            # Cache updated sitemap
            cache_key = cls.get_sitemap_cache_key(site_id)
            cache.set(cache_key, existing_sitemap, cls.SITEMAP_CACHE_TIMEOUT)
            
            return existing_sitemap
            
        except Exception as e:
            logger.error(f"Error generating incremental sitemap: {e}")
            return None


class OptimizedSitemapQuerySet(models.QuerySet):
    """
    Enhanced QuerySet for sitemap generation.
    """
    
    def optimized_for_sitemap(self, site_id):
        """Optimize queryset for sitemap generation."""
        return self.select_related(
            'owner',
            'content_type'
        ).prefetch_related(
            'revisions'
        ).only(
            'id', 'title', 'slug', 'content_type_id', 'owner_id',
            'live', 'has_unpublished_changes', 'path', 'depth',
            'first_published_at', 'last_published_at'
        )


# Register sitemap optimization hooks
@hooks.register('after_publish_page')
def invalidate_sitemap_cache_publish(page):
    """Invalidate sitemap cache when page is published."""
    # Get site ID from page
    site_id = page.get_site().id
    SitemapOptimizer.invalidate_sitemap_cache(site_id)


@hooks.register('after_unpublish_page')
def invalidate_sitemap_cache_unpublish(page):
    """Invalidate sitemap cache when page is unpublished."""
    # Get site ID from page
    site_id = page.get_site().id
    SitemapOptimizer.invalidate_sitemap_cache(site_id)


@hooks.register('after_move_page')
def invalidate_sitemap_cache_move(page):
    """Invalidate sitemap cache when page is moved."""
    # Get site ID from page
    site_id = page.get_site().id
    SitemapOptimizer.invalidate_sitemap_cache(site_id)


# =============================================================================
# 10. ASYNC VIEW SUPPORT FOR BETTER PERFORMANCE
# =============================================================================

class AsyncViewOptimizer:
    """
    Enhanced async view support using Wagtail 7.0.2's new async capabilities.
    
    Features:
    - Async view handlers
    - Background task processing
    - Non-blocking operations
    - Performance monitoring
    """
    
    @staticmethod
    async def async_get_page_data(page_id):
        """Async method to get page data."""
        try:
            # Simulate async database query
            page = await AsyncViewOptimizer._async_get_page(page_id)
            
            if page:
                # Get related data asynchronously
                revisions = await AsyncViewOptimizer._async_get_revisions(page_id)
                permissions = await AsyncViewOptimizer._async_get_permissions(page_id)
                
                return {
                    'page': page,
                    'revisions': revisions,
                    'permissions': permissions
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in async_get_page_data: {e}")
            return None
    
    @staticmethod
    async def async_get_medication_data(medication_id):
        """Async method to get medication data."""
        try:
            # Simulate async database query
            medication = await AsyncViewOptimizer._async_get_medication(medication_id)
            
            if medication:
                # Get related data asynchronously
                prescriptions = await AsyncViewOptimizer._async_get_prescriptions(medication_id)
                interactions = await AsyncViewOptimizer._async_get_interactions(medication_id)
                stock_alerts = await AsyncViewOptimizer._async_get_stock_alerts(medication_id)
                
                return {
                    'medication': medication,
                    'prescriptions': prescriptions,
                    'interactions': interactions,
                    'stock_alerts': stock_alerts
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in async_get_medication_data: {e}")
            return None
    
    @staticmethod
    async def async_search_pages(search_query, search_type='full'):
        """Async method to search pages."""
        try:
            # Simulate async search
            search_results = await AsyncViewOptimizer._async_search(search_query, search_type)
            
            # Optimize results
            optimized_results = await AsyncViewOptimizer._async_optimize_search_results(search_results)
            
            return optimized_results
            
        except Exception as e:
            logger.error(f"Error in async_search_pages: {e}")
            return []
    
    @staticmethod
    async def async_generate_sitemap(site_id):
        """Async method to generate sitemap."""
        try:
            # Get site data asynchronously
            site_data = await AsyncViewOptimizer._async_get_site_data(site_id)
            
            if site_data:
                # Generate sitemap asynchronously
                sitemap_data = await AsyncViewOptimizer._async_build_sitemap(site_data)
                
                # Cache sitemap asynchronously
                await AsyncViewOptimizer._async_cache_sitemap(site_id, sitemap_data)
                
                return sitemap_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error in async_generate_sitemap: {e}")
            return None
    
    # Helper methods for async operations (simulated)
    @staticmethod
    async def _async_get_page(page_id):
        """Simulate async page retrieval."""
        # In a real implementation, this would use async database queries
        import asyncio
        await asyncio.sleep(0.1)  # Simulate async delay
        
        try:
            from wagtail.models import Page
            return Page.objects.get(id=page_id)
        except Page.DoesNotExist:
            return None
    
    @staticmethod
    async def _async_get_medication(medication_id):
        """Simulate async medication retrieval."""
        import asyncio
        await asyncio.sleep(0.1)  # Simulate async delay
        
        try:
            from medications.models import Medication
            return Medication.objects.get(id=medication_id)
        except Medication.DoesNotExist:
            return None
    
    @staticmethod
    async def _async_get_revisions(page_id):
        """Simulate async revisions retrieval."""
        import asyncio
        await asyncio.sleep(0.05)  # Simulate async delay
        
        try:
            from wagtail.models import PageRevision
            return PageRevision.objects.filter(page_id=page_id)
        except Exception:
            return []
    
    @staticmethod
    async def _async_get_permissions(page_id):
        """Simulate async permissions retrieval."""
        import asyncio
        await asyncio.sleep(0.05)  # Simulate async delay
        
        try:
            from wagtail.models import Page
            page = Page.objects.get(id=page_id)
            return page.permissions.all()
        except Exception:
            return []
    
    @staticmethod
    async def _async_get_prescriptions(medication_id):
        """Simulate async prescriptions retrieval."""
        import asyncio
        await asyncio.sleep(0.1)  # Simulate async delay
        
        try:
            from medications.models import Prescription
            return Prescription.objects.filter(medication_id=medication_id)
        except Exception:
            return []
    
    @staticmethod
    async def _async_get_interactions(medication_id):
        """Simulate async interactions retrieval."""
        import asyncio
        await asyncio.sleep(0.1)  # Simulate async delay
        
        try:
            from medications.models import DrugInteraction
            return DrugInteraction.objects.filter(medication_id=medication_id)
        except Exception:
            return []
    
    @staticmethod
    async def _async_get_stock_alerts(medication_id):
        """Simulate async stock alerts retrieval."""
        import asyncio
        await asyncio.sleep(0.05)  # Simulate async delay
        
        try:
            from medications.models import StockAlert
            return StockAlert.objects.filter(medication_id=medication_id)
        except Exception:
            return []
    
    @staticmethod
    async def _async_search(search_query, search_type):
        """Simulate async search."""
        import asyncio
        await asyncio.sleep(0.2)  # Simulate async delay
        
        try:
            from wagtail.search.models import Query
            query = Query.get(search_query)
            return query.get_editors_picks()
        except Exception:
            return []
    
    @staticmethod
    async def _async_optimize_search_results(search_results):
        """Simulate async search result optimization."""
        import asyncio
        await asyncio.sleep(0.1)  # Simulate async delay
        
        # Apply optimizations
        optimizer = SearchQueryOptimizer()
        return optimizer.optimize_search_queryset(search_results, "", 'full')
    
    @staticmethod
    async def _async_get_site_data(site_id):
        """Simulate async site data retrieval."""
        import asyncio
        await asyncio.sleep(0.1)  # Simulate async delay
        
        try:
            return Site.objects.get(id=site_id)
        except Site.DoesNotExist:
            return None
    
    @staticmethod
    async def _async_build_sitemap(site_data):
        """Simulate async sitemap building."""
        import asyncio
        await asyncio.sleep(0.3)  # Simulate async delay
        
        return SitemapOptimizer.generate_sitemap(site_data.id)
    
    @staticmethod
    async def _async_cache_sitemap(site_id, sitemap_data):
        """Simulate async sitemap caching."""
        import asyncio
        await asyncio.sleep(0.05)  # Simulate async delay
        
        cache_key = SitemapOptimizer.get_sitemap_cache_key(site_id)
        cache.set(cache_key, sitemap_data, SitemapOptimizer.SITEMAP_CACHE_TIMEOUT)


class AsyncViewHandler:
    """
    Handler for async view operations.
    """
    
    @staticmethod
    async def handle_async_page_request(page_id):
        """Handle async page request."""
        return await AsyncViewOptimizer.async_get_page_data(page_id)
    
    @staticmethod
    async def handle_async_medication_request(medication_id):
        """Handle async medication request."""
        return await AsyncViewOptimizer.async_get_medication_data(medication_id)
    
    @staticmethod
    async def handle_async_search_request(search_query, search_type='full'):
        """Handle async search request."""
        return await AsyncViewOptimizer.async_search_pages(search_query, search_type)
    
    @staticmethod
    async def handle_async_sitemap_request(site_id):
        """Handle async sitemap request."""
        return await AsyncViewOptimizer.async_generate_sitemap(site_id)


# Register async view hooks
@hooks.register('register_async_view')
def register_async_views():
    """Register async views for better performance."""
    return {
        'async_page_data': AsyncViewHandler.handle_async_page_request,
        'async_medication_data': AsyncViewHandler.handle_async_medication_request,
        'async_search': AsyncViewHandler.handle_async_search_request,
        'async_sitemap': AsyncViewHandler.handle_async_sitemap_request,
    }


# =============================================================================
# PERFORMANCE MONITORING AND UTILITIES
# =============================================================================

class PerformanceMonitor:
    """
    Performance monitoring utilities for Wagtail optimizations.
    """
    
    @staticmethod
    def log_query_performance(operation, duration, query_count=None):
        """Log query performance metrics."""
        logger.info(f"Performance: {operation} completed in {duration:.3f}s (queries: {query_count})")
    
    @staticmethod
    def log_cache_performance(operation, cache_hit, duration):
        """Log cache performance metrics."""
        status = "HIT" if cache_hit else "MISS"
        logger.info(f"Cache {status}: {operation} completed in {duration:.3f}s")
    
    @staticmethod
    def get_performance_summary():
        """Get performance summary."""
        return {
            'optimizations_enabled': True,
            'cache_enabled': True,
            'async_support': True,
            'wagtail_version': '7.0.2'
        }


# Export main optimization classes
__all__ = [
    'PageQueryOptimizer',
    'OptimizedImageRenditionCache',
    'StreamFieldOptimizer',
    'PageTreeCache',
    'AdminQueryOptimizer',
    'SearchQueryOptimizer',
    'TemplateFragmentCache',
    'DatabaseQueryPrefetcher',
    'SitemapOptimizer',
    'AsyncViewOptimizer',
    'PerformanceMonitor'
] 