"""
Offline-capable pages using Wagtail 7.0.2's PWA features
Progressive Web App implementation
"""

from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from wagtail.models import Page
from wagtail.images.models import Image
import json
import logging
import hashlib
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PWAManifest:
    """
    PWA manifest generator for MedGuard SA
    """
    
    def __init__(self):
        self.app_name = "MedGuard SA"
        self.short_name = "MedGuard"
        self.description = "Medication management and health information"
        self.theme_color = "#2563eb"
        self.background_color = "#ffffff"
        self.display = "standalone"
        self.orientation = "portrait"
        self.scope = "/"
        self.start_url = "/"
    
    def generate_manifest(self):
        """
        Generate PWA manifest JSON
        """
        manifest = {
            "name": self.app_name,
            "short_name": self.short_name,
            "description": self.description,
            "theme_color": self.theme_color,
            "background_color": self.background_color,
            "display": self.display,
            "orientation": self.orientation,
            "scope": self.scope,
            "start_url": self.start_url,
            "icons": self._get_icons(),
            "categories": ["medical", "health", "productivity"],
            "lang": "en-ZA",
            "dir": "ltr",
            "screenshots": self._get_screenshots(),
            "shortcuts": self._get_shortcuts(),
        }
        
        return manifest
    
    def _get_icons(self):
        """
        Get PWA icons
        """
        return [
            {
                "src": "/static/images/icons/icon-72x72.png",
                "sizes": "72x72",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/images/icons/icon-96x96.png",
                "sizes": "96x96",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/images/icons/icon-128x128.png",
                "sizes": "128x128",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/images/icons/icon-144x144.png",
                "sizes": "144x144",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/images/icons/icon-152x152.png",
                "sizes": "152x152",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/images/icons/icon-192x192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/images/icons/icon-384x384.png",
                "sizes": "384x384",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/images/icons/icon-512x512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    
    def _get_screenshots(self):
        """
        Get PWA screenshots
        """
        return [
            {
                "src": "/static/images/screenshots/home-mobile.png",
                "sizes": "390x844",
                "type": "image/png",
                "form_factor": "narrow"
            },
            {
                "src": "/static/images/screenshots/medications-mobile.png",
                "sizes": "390x844",
                "type": "image/png",
                "form_factor": "narrow"
            }
        ]
    
    def _get_shortcuts(self):
        """
        Get PWA shortcuts
        """
        return [
            {
                "name": "Search Medications",
                "short_name": "Search",
                "description": "Search for medications",
                "url": "/search/",
                "icons": [
                    {
                        "src": "/static/images/icons/search-96x96.png",
                        "sizes": "96x96"
                    }
                ]
            },
            {
                "name": "My Medications",
                "short_name": "Medications",
                "description": "View my medications",
                "url": "/medications/my/",
                "icons": [
                    {
                        "src": "/static/images/icons/medication-96x96.png",
                        "sizes": "96x96"
                    }
                ]
            },
            {
                "name": "Emergency Contacts",
                "short_name": "Emergency",
                "description": "Emergency contacts",
                "url": "/emergency/",
                "icons": [
                    {
                        "src": "/static/images/icons/emergency-96x96.png",
                        "sizes": "96x96"
                    }
                ]
            }
        ]


class ServiceWorker:
    """
    Service Worker for offline functionality
    """
    
    def __init__(self):
        self.cache_name = "medguard-cache-v1"
        self.offline_page = "/offline/"
        self.api_cache_name = "medguard-api-cache-v1"
    
    def generate_service_worker_js(self):
        """
        Generate Service Worker JavaScript
        """
        sw_js = """
        const CACHE_NAME = 'medguard-cache-v1';
        const API_CACHE_NAME = 'medguard-api-cache-v1';
        const OFFLINE_PAGE = '/offline/';
        
        // Files to cache immediately
        const urlsToCache = [
            '/',
            '/offline/',
            '/static/css/mobile.css',
            '/static/js/mobile.js',
            '/static/images/logo.png',
            '/static/images/icons/icon-192x192.png',
        ];
        
        // Install event - cache essential files
        self.addEventListener('install', (event) => {
            event.waitUntil(
                caches.open(CACHE_NAME)
                    .then((cache) => {
                        console.log('Opened cache');
                        return cache.addAll(urlsToCache);
                    })
            );
        });
        
        // Fetch event - serve from cache when offline
        self.addEventListener('fetch', (event) => {
            const request = event.request;
            
            // Skip non-GET requests
            if (request.method !== 'GET') {
                return;
            }
            
            // Handle API requests
            if (request.url.includes('/api/')) {
                event.respondWith(handleApiRequest(request));
                return;
            }
            
            // Handle page requests
            if (request.mode === 'navigate') {
                event.respondWith(handlePageRequest(request));
                return;
            }
            
            // Handle static assets
            if (request.destination === 'image' || 
                request.destination === 'style' || 
                request.destination === 'script') {
                event.respondWith(handleStaticRequest(request));
                return;
            }
        });
        
        // Handle API requests
        async function handleApiRequest(request) {
            try {
                // Try network first
                const response = await fetch(request);
                
                if (response.ok) {
                    // Cache successful API responses
                    const cache = await caches.open(API_CACHE_NAME);
                    cache.put(request, response.clone());
                }
                
                return response;
            } catch (error) {
                // Fallback to cache
                const cachedResponse = await caches.match(request);
                if (cachedResponse) {
                    return cachedResponse;
                }
                
                // Return offline response
                return new Response(
                    JSON.stringify({ error: 'Offline - API not available' }),
                    { 
                        status: 503,
                        headers: { 'Content-Type': 'application/json' }
                    }
                );
            }
        }
        
        // Handle page requests
        async function handlePageRequest(request) {
            try {
                // Try network first
                const response = await fetch(request);
                
                if (response.ok) {
                    // Cache successful page responses
                    const cache = await caches.open(CACHE_NAME);
                    cache.put(request, response.clone());
                }
                
                return response;
            } catch (error) {
                // Fallback to cache
                const cachedResponse = await caches.match(request);
                if (cachedResponse) {
                    return cachedResponse;
                }
                
                // Return offline page
                return caches.match(OFFLINE_PAGE);
            }
        }
        
        // Handle static requests
        async function handleStaticRequest(request) {
            const cachedResponse = await caches.match(request);
            
            if (cachedResponse) {
                return cachedResponse;
            }
            
            try {
                const response = await fetch(request);
                
                if (response.ok) {
                    const cache = await caches.open(CACHE_NAME);
                    cache.put(request, response.clone());
                }
                
                return response;
            } catch (error) {
                // Return placeholder for images
                if (request.destination === 'image') {
                    return new Response(
                        '<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100" fill="#f0f0f0"/><text x="50" y="50" text-anchor="middle" fill="#666">Image</text></svg>',
                        { headers: { 'Content-Type': 'image/svg+xml' } }
                    );
                }
                
                throw error;
            }
        }
        
        // Background sync for offline actions
        self.addEventListener('sync', (event) => {
            if (event.tag === 'background-sync') {
                event.waitUntil(doBackgroundSync());
            }
        });
        
        async function doBackgroundSync() {
            try {
                // Sync offline data when connection is restored
                const offlineData = await getOfflineData();
                
                for (const data of offlineData) {
                    await syncOfflineAction(data);
                }
                
                console.log('Background sync completed');
            } catch (error) {
                console.error('Background sync failed:', error);
            }
        }
        
        // Push notifications
        self.addEventListener('push', (event) => {
            const options = {
                body: event.data ? event.data.text() : 'New notification from MedGuard',
                icon: '/static/images/icons/icon-192x192.png',
                badge: '/static/images/icons/badge-72x72.png',
                vibrate: [100, 50, 100],
                data: {
                    dateOfArrival: Date.now(),
                    primaryKey: 1
                },
                actions: [
                    {
                        action: 'explore',
                        title: 'View',
                        icon: '/static/images/icons/checkmark.png'
                    },
                    {
                        action: 'close',
                        title: 'Close',
                        icon: '/static/images/icons/xmark.png'
                    }
                ]
            };
            
            event.waitUntil(
                self.registration.showNotification('MedGuard SA', options)
            );
        });
        
        // Notification click
        self.addEventListener('notificationclick', (event) => {
            event.notification.close();
            
            if (event.action === 'explore') {
                event.waitUntil(
                    clients.openWindow('/')
                );
            }
        });
        
        // Cache cleanup
        self.addEventListener('activate', (event) => {
            event.waitUntil(
                caches.keys().then((cacheNames) => {
                    return Promise.all(
                        cacheNames.map((cacheName) => {
                            if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
                                return caches.delete(cacheName);
                            }
                        })
                    );
                })
            );
        });
        """
        
        return sw_js


class OfflineContentManager:
    """
    Manager for offline content and caching
    """
    
    def __init__(self):
        self.cache_duration = 3600  # 1 hour
        self.max_cache_size = 50  # Maximum number of cached pages
    
    def get_offline_content(self, page):
        """
        Get content optimized for offline viewing
        """
        try:
            # Get page content
            content = {
                'id': page.id,
                'title': page.title,
                'url': page.url,
                'last_modified': page.last_published_at.isoformat() if page.last_published_at else None,
                'content_type': page.content_type.model,
            }
            
            # Add page-specific content
            if hasattr(page, 'body') and page.body:
                content['body'] = self._process_streamfield_for_offline(page.body)
            
            if hasattr(page, 'search_description'):
                content['description'] = page.search_description
            
            # Add images with offline URLs
            content['images'] = self._get_offline_images(page)
            
            return content
            
        except Exception as e:
            logger.error(f"Error getting offline content: {e}")
            return None
    
    def _process_streamfield_for_offline(self, streamfield):
        """
        Process StreamField content for offline viewing
        """
        processed_blocks = []
        
        for block in streamfield:
            block_data = {
                'type': block.block_type,
                'value': block.value,
            }
            
            # Process images in blocks
            if hasattr(block.value, 'image') and block.value.image:
                block_data['image_url'] = self._get_offline_image_url(block.value.image)
            
            processed_blocks.append(block_data)
        
        return processed_blocks
    
    def _get_offline_images(self, page):
        """
        Get images for offline viewing
        """
        images = []
        
        # Get page images
        if hasattr(page, 'image') and page.image:
            images.append({
                'url': self._get_offline_image_url(page.image),
                'alt': page.image.alt or '',
                'title': page.image.title or '',
            })
        
        # Get images from StreamField
        if hasattr(page, 'body') and page.body:
            for block in page.body:
                if hasattr(block.value, 'image') and block.value.image:
                    images.append({
                        'url': self._get_offline_image_url(block.value.image),
                        'alt': block.value.image.alt or '',
                        'title': block.value.image.title or '',
                    })
        
        return images
    
    def _get_offline_image_url(self, image):
        """
        Get offline-optimized image URL
        """
        try:
            # Get mobile-optimized rendition
            rendition = image.get_rendition('fill-400x300')
            return rendition.url
        except:
            return image.url
    
    def cache_page_for_offline(self, page):
        """
        Cache page content for offline viewing
        """
        try:
            content = self.get_offline_content(page)
            if not content:
                return False
            
            cache_key = f"offline_page_{page.id}"
            cache.set(cache_key, content, self.cache_duration)
            
            # Update cache index
            self._update_cache_index(page.id, page.url)
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching page for offline: {e}")
            return False
    
    def _update_cache_index(self, page_id, page_url):
        """
        Update cache index
        """
        cache_key = "offline_cache_index"
        index = cache.get(cache_key, [])
        
        # Add new entry
        entry = {
            'page_id': page_id,
            'url': page_url,
            'cached_at': datetime.now().isoformat(),
        }
        
        # Remove if already exists
        index = [item for item in index if item['page_id'] != page_id]
        
        # Add to beginning
        index.insert(0, entry)
        
        # Limit cache size
        if len(index) > self.max_cache_size:
            index = index[:self.max_cache_size]
        
        cache.set(cache_key, index, self.cache_duration)
    
    def get_cached_page(self, page_id):
        """
        Get cached page content
        """
        cache_key = f"offline_page_{page_id}"
        return cache.get(cache_key)
    
    def get_cache_index(self):
        """
        Get cache index
        """
        cache_key = "offline_cache_index"
        return cache.get(cache_key, [])


class PWAMetaTags:
    """
    PWA meta tags generator
    """
    
    @staticmethod
    def get_pwa_meta_tags():
        """
        Get PWA meta tags for HTML head
        """
        meta_tags = """
        <meta name="application-name" content="MedGuard SA">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="apple-mobile-web-app-title" content="MedGuard">
        <meta name="description" content="Medication management and health information">
        <meta name="format-detection" content="telephone=no">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="msapplication-config" content="/static/images/icons/browserconfig.xml">
        <meta name="msapplication-TileColor" content="#2563eb">
        <meta name="msapplication-tap-highlight" content="no">
        <meta name="theme-color" content="#2563eb">
        
        <link rel="apple-touch-icon" href="/static/images/icons/apple-touch-icon.png">
        <link rel="icon" type="image/png" sizes="32x32" href="/static/images/icons/favicon-32x32.png">
        <link rel="icon" type="image/png" sizes="16x16" href="/static/images/icons/favicon-16x16.png">
        <link rel="manifest" href="/manifest.json">
        <link rel="mask-icon" href="/static/images/icons/safari-pinned-tab.svg" color="#2563eb">
        <link rel="shortcut icon" href="/favicon.ico">
        <link rel="stylesheet" href="/static/css/mobile.css">
        """
        
        return format_html(meta_tags)


class OfflinePageGenerator:
    """
    Generate offline page content
    """
    
    @staticmethod
    def get_offline_page_html():
        """
        Get offline page HTML
        """
        html = """
        <!DOCTYPE html>
        <html lang="en-ZA">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Offline - MedGuard SA</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 2rem;
                    background: #f8fafc;
                    color: #1e293b;
                    text-align: center;
                }
                .offline-container {
                    max-width: 400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    padding: 2rem;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                .offline-icon {
                    width: 64px;
                    height: 64px;
                    margin: 0 auto 1rem;
                    background: #e2e8f0;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                }
                h1 {
                    margin: 0 0 1rem 0;
                    color: #1e293b;
                    font-size: 1.5rem;
                }
                p {
                    margin: 0 0 1.5rem 0;
                    color: #64748b;
                    line-height: 1.6;
                }
                .retry-btn {
                    background: #2563eb;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-size: 16px;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }
                .retry-btn:hover {
                    background: #1d4ed8;
                }
                .cached-content {
                    margin-top: 2rem;
                    text-align: left;
                }
                .cached-item {
                    padding: 12px;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    margin-bottom: 8px;
                    background: #f8fafc;
                }
                .cached-item a {
                    color: #2563eb;
                    text-decoration: none;
                }
                .cached-item a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="offline-container">
                <div class="offline-icon">📱</div>
                <h1>You're Offline</h1>
                <p>Don't worry! You can still access some content that was previously loaded.</p>
                
                <button class="retry-btn" onclick="window.location.reload()">
                    Try Again
                </button>
                
                <div class="cached-content" id="cachedContent">
                    <h3>Available Offline:</h3>
                    <div id="cachedItems"></div>
                </div>
            </div>
            
            <script>
                // Show cached content
                async function showCachedContent() {
                    try {
                        const response = await fetch('/api/mobile/offline/cached-pages/');
                        const data = await response.json();
                        
                        const cachedItems = document.getElementById('cachedItems');
                        
                        if (data.pages && data.pages.length > 0) {
                            data.pages.forEach(page => {
                                const item = document.createElement('div');
                                item.className = 'cached-item';
                                item.innerHTML = `
                                    <a href="${page.url}">${page.title}</a>
                                    <br><small>Cached: ${new Date(page.cached_at).toLocaleDateString()}</small>
                                `;
                                cachedItems.appendChild(item);
                            });
                        } else {
                            cachedItems.innerHTML = '<p>No cached content available.</p>';
                        }
                    } catch (error) {
                        console.error('Error loading cached content:', error);
                    }
                }
                
                // Check connection status
                function updateConnectionStatus() {
                    if (navigator.onLine) {
                        window.location.reload();
                    }
                }
                
                // Event listeners
                window.addEventListener('online', updateConnectionStatus);
                window.addEventListener('focus', updateConnectionStatus);
                
                // Load cached content on page load
                document.addEventListener('DOMContentLoaded', showCachedContent);
            </script>
        </body>
        </html>
        """
        
        return format_html(html) 