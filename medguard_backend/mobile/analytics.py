"""
Mobile analytics and performance monitoring
Wagtail 7.0.2 analytics features
"""

from django.core.cache import cache
from django.http import JsonResponse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from wagtail.models import Page
import json
import logging
import time
from datetime import datetime, timedelta
from collections import defaultdict
import psutil
import threading

logger = logging.getLogger(__name__)


class MobileAnalytics:
    """
    Mobile analytics and tracking system
    """
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.performance_data = {}
        self.user_sessions = {}
    
    def track_page_view(self, request, page, load_time=None):
        """
        Track page view with mobile analytics
        """
        try:
            # Get device information
            device_info = self._get_device_info(request)
            
            # Get user information
            user_info = self._get_user_info(request)
            
            # Create page view event
            page_view = {
                'timestamp': datetime.now().isoformat(),
                'page_id': page.id if page else None,
                'page_url': request.path,
                'page_title': page.title if page else 'Unknown',
                'device_info': device_info,
                'user_info': user_info,
                'load_time': load_time,
                'session_id': self._get_session_id(request),
                'referrer': request.META.get('HTTP_REFERER', ''),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
            
            # Store in cache
            self._store_analytics_event('page_views', page_view)
            
            # Update session data
            self._update_session_data(request, page_view)
            
            return page_view
            
        except Exception as e:
            logger.error(f"Error tracking page view: {e}")
            return None
    
    def track_user_action(self, request, action_type, action_data=None):
        """
        Track user actions (clicks, form submissions, etc.)
        """
        try:
            action_event = {
                'timestamp': datetime.now().isoformat(),
                'action_type': action_type,
                'action_data': action_data or {},
                'device_info': self._get_device_info(request),
                'user_info': self._get_user_info(request),
                'session_id': self._get_session_id(request),
                'page_url': request.path,
            }
            
            self._store_analytics_event('user_actions', action_event)
            
            return action_event
            
        except Exception as e:
            logger.error(f"Error tracking user action: {e}")
            return None
    
    def track_performance_metric(self, request, metric_type, value, metadata=None):
        """
        Track performance metrics
        """
        try:
            performance_event = {
                'timestamp': datetime.now().isoformat(),
                'metric_type': metric_type,
                'value': value,
                'metadata': metadata or {},
                'device_info': self._get_device_info(request),
                'user_info': self._get_user_info(request),
                'session_id': self._get_session_id(request),
            }
            
            self._store_analytics_event('performance_metrics', performance_event)
            
            return performance_event
            
        except Exception as e:
            logger.error(f"Error tracking performance metric: {e}")
            return None
    
    def track_error(self, request, error_type, error_message, stack_trace=None):
        """
        Track errors and exceptions
        """
        try:
            error_event = {
                'timestamp': datetime.now().isoformat(),
                'error_type': error_type,
                'error_message': error_message,
                'stack_trace': stack_trace,
                'device_info': self._get_device_info(request),
                'user_info': self._get_user_info(request),
                'session_id': self._get_session_id(request),
                'page_url': request.path,
            }
            
            self._store_analytics_event('errors', error_event)
            
            return error_event
            
        except Exception as e:
            logger.error(f"Error tracking error: {e}")
            return None
    
    def _get_device_info(self, request):
        """
        Extract device information from request
        """
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        device_info = {
            'is_mobile': any(device in user_agent for device in ['mobile', 'android', 'iphone', 'ipad']),
            'is_tablet': any(device in user_agent for device in ['tablet', 'ipad']),
            'is_desktop': not any(device in user_agent for device in ['mobile', 'android', 'iphone', 'ipad', 'tablet']),
            'user_agent': user_agent,
            'screen_width': request.META.get('HTTP_X_SCREEN_WIDTH'),
            'screen_height': request.META.get('HTTP_X_SCREEN_HEIGHT'),
            'connection_type': request.META.get('HTTP_X_CONNECTION_TYPE', 'unknown'),
        }
        
        # Detect device type
        if 'iphone' in user_agent:
            device_info['device_type'] = 'iPhone'
        elif 'ipad' in user_agent:
            device_info['device_type'] = 'iPad'
        elif 'android' in user_agent:
            device_info['device_type'] = 'Android'
        else:
            device_info['device_type'] = 'Desktop'
        
        return device_info
    
    def _get_user_info(self, request):
        """
        Extract user information from request
        """
        user_info = {
            'is_authenticated': request.user.is_authenticated,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'ip_address': self._get_client_ip(request),
            'language': request.META.get('HTTP_ACCEPT_LANGUAGE', 'en'),
        }
        
        return user_info
    
    def _get_client_ip(self, request):
        """
        Get client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_session_id(self, request):
        """
        Get or create session ID
        """
        if not hasattr(request, 'session'):
            return None
        
        if 'analytics_session_id' not in request.session:
            request.session['analytics_session_id'] = f"session_{int(time.time())}_{hash(request.META.get('REMOTE_ADDR', ''))}"
        
        return request.session['analytics_session_id']
    
    def _store_analytics_event(self, event_type, event_data):
        """
        Store analytics event in cache
        """
        cache_key = f"mobile_analytics_{event_type}_{datetime.now().strftime('%Y%m%d')}"
        
        # Get existing events
        events = cache.get(cache_key, [])
        
        # Add new event
        events.append(event_data)
        
        # Limit events per day (keep last 1000 events)
        if len(events) > 1000:
            events = events[-1000:]
        
        # Store back in cache
        cache.set(cache_key, events, 86400)  # Store for 24 hours
    
    def _update_session_data(self, request, page_view):
        """
        Update session data
        """
        session_id = page_view['session_id']
        if not session_id:
            return
        
        cache_key = f"mobile_session_{session_id}"
        session_data = cache.get(cache_key, {
            'session_id': session_id,
            'start_time': datetime.now().isoformat(),
            'page_views': [],
            'user_actions': [],
            'total_load_time': 0,
            'page_count': 0,
        })
        
        # Update session data
        session_data['page_views'].append({
            'url': page_view['page_url'],
            'title': page_view['page_title'],
            'timestamp': page_view['timestamp'],
            'load_time': page_view.get('load_time', 0),
        })
        
        session_data['total_load_time'] += page_view.get('load_time', 0)
        session_data['page_count'] += 1
        session_data['last_activity'] = datetime.now().isoformat()
        
        # Store updated session
        cache.set(cache_key, session_data, 3600)  # Store for 1 hour


class MobilePerformanceMonitor:
    """
    Mobile performance monitoring system
    """
    
    def __init__(self):
        self.performance_metrics = {}
        self.system_metrics = {}
        self.start_monitoring()
    
    def start_monitoring(self):
        """
        Start background performance monitoring
        """
        def monitor_system():
            while True:
                try:
                    self._collect_system_metrics()
                    time.sleep(60)  # Collect metrics every minute
                except Exception as e:
                    logger.error(f"Error in system monitoring: {e}")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def _collect_system_metrics(self):
        """
        Collect system performance metrics
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            
            self.system_metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'disk_percent': disk.percent,
                'disk_free': disk.free,
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
            }
            
            # Store in cache
            cache.set('mobile_system_metrics', self.system_metrics, 300)  # Store for 5 minutes
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def track_page_load_performance(self, request, page, start_time, end_time):
        """
        Track page load performance
        """
        try:
            load_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            performance_data = {
                'timestamp': datetime.now().isoformat(),
                'page_id': page.id if page else None,
                'page_url': request.path,
                'load_time_ms': load_time,
                'device_info': self._get_device_info(request),
                'session_id': self._get_session_id(request),
            }
            
            # Store performance data
            cache_key = f"mobile_performance_{datetime.now().strftime('%Y%m%d')}"
            performance_list = cache.get(cache_key, [])
            performance_list.append(performance_data)
            
            # Keep last 1000 performance records
            if len(performance_list) > 1000:
                performance_list = performance_list[-1000:]
            
            cache.set(cache_key, performance_list, 86400)
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Error tracking page load performance: {e}")
            return None
    
    def get_performance_summary(self, days=7):
        """
        Get performance summary for the last N days
        """
        try:
            summary = {
                'total_pages': 0,
                'average_load_time': 0,
                'slow_pages': [],
                'fast_pages': [],
                'device_breakdown': {},
                'daily_averages': [],
            }
            
            total_load_time = 0
            page_count = 0
            load_times = []
            
            # Collect data from last N days
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
                cache_key = f"mobile_performance_{date}"
                performance_list = cache.get(cache_key, [])
                
                for perf in performance_list:
                    load_time = perf.get('load_time_ms', 0)
                    load_times.append(load_time)
                    total_load_time += load_time
                    page_count += 1
                    
                    # Track device breakdown
                    device_type = perf.get('device_info', {}).get('device_type', 'Unknown')
                    summary['device_breakdown'][device_type] = summary['device_breakdown'].get(device_type, 0) + 1
                    
                    # Track slow/fast pages
                    if load_time > 3000:  # Slow: > 3 seconds
                        summary['slow_pages'].append({
                            'url': perf.get('page_url'),
                            'load_time': load_time,
                        })
                    elif load_time < 1000:  # Fast: < 1 second
                        summary['fast_pages'].append({
                            'url': perf.get('page_url'),
                            'load_time': load_time,
                        })
            
            if page_count > 0:
                summary['total_pages'] = page_count
                summary['average_load_time'] = total_load_time / page_count
                
                # Sort slow/fast pages
                summary['slow_pages'] = sorted(summary['slow_pages'], key=lambda x: x['load_time'], reverse=True)[:10]
                summary['fast_pages'] = sorted(summary['fast_pages'], key=lambda x: x['load_time'])[:10]
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}
    
    def _get_device_info(self, request):
        """
        Get device information (same as analytics)
        """
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        if 'iphone' in user_agent:
            return {'device_type': 'iPhone'}
        elif 'ipad' in user_agent:
            return {'device_type': 'iPad'}
        elif 'android' in user_agent:
            return {'device_type': 'Android'}
        else:
            return {'device_type': 'Desktop'}
    
    def _get_session_id(self, request):
        """
        Get session ID (same as analytics)
        """
        if not hasattr(request, 'session'):
            return None
        
        if 'analytics_session_id' not in request.session:
            request.session['analytics_session_id'] = f"session_{int(time.time())}_{hash(request.META.get('REMOTE_ADDR', ''))}"
        
        return request.session['analytics_session_id']


class MobileAnalyticsDashboard:
    """
    Mobile analytics dashboard data generator
    """
    
    def __init__(self):
        self.analytics = MobileAnalytics()
        self.performance = MobilePerformanceMonitor()
    
    def get_dashboard_data(self, days=7):
        """
        Get comprehensive dashboard data
        """
        try:
            dashboard_data = {
                'page_views': self._get_page_views_data(days),
                'user_actions': self._get_user_actions_data(days),
                'performance': self.performance.get_performance_summary(days),
                'errors': self._get_errors_data(days),
                'sessions': self._get_sessions_data(days),
                'system_metrics': self._get_system_metrics(),
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}
    
    def _get_page_views_data(self, days):
        """
        Get page views analytics data
        """
        page_views = []
        device_breakdown = defaultdict(int)
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            cache_key = f"mobile_analytics_page_views_{date}"
            events = cache.get(cache_key, [])
            
            for event in events:
                page_views.append(event)
                device_type = event.get('device_info', {}).get('device_type', 'Unknown')
                device_breakdown[device_type] += 1
        
        return {
            'total_views': len(page_views),
            'device_breakdown': dict(device_breakdown),
            'recent_views': page_views[-50:],  # Last 50 views
        }
    
    def _get_user_actions_data(self, days):
        """
        Get user actions analytics data
        """
        actions = []
        action_types = defaultdict(int)
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            cache_key = f"mobile_analytics_user_actions_{date}"
            events = cache.get(cache_key, [])
            
            for event in events:
                actions.append(event)
                action_type = event.get('action_type', 'unknown')
                action_types[action_type] += 1
        
        return {
            'total_actions': len(actions),
            'action_types': dict(action_types),
            'recent_actions': actions[-50:],  # Last 50 actions
        }
    
    def _get_errors_data(self, days):
        """
        Get errors analytics data
        """
        errors = []
        error_types = defaultdict(int)
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            cache_key = f"mobile_analytics_errors_{date}"
            events = cache.get(cache_key, [])
            
            for event in events:
                errors.append(event)
                error_type = event.get('error_type', 'unknown')
                error_types[error_type] += 1
        
        return {
            'total_errors': len(errors),
            'error_types': dict(error_types),
            'recent_errors': errors[-20:],  # Last 20 errors
        }
    
    def _get_sessions_data(self, days):
        """
        Get session analytics data
        """
        sessions = []
        session_durations = []
        
        # Get all session keys from cache
        session_keys = [key for key in cache.keys() if key.startswith('mobile_session_')]
        
        for key in session_keys:
            session_data = cache.get(key)
            if session_data:
                sessions.append(session_data)
                
                # Calculate session duration
                start_time = datetime.fromisoformat(session_data.get('start_time', datetime.now().isoformat()))
                last_activity = datetime.fromisoformat(session_data.get('last_activity', datetime.now().isoformat()))
                duration = (last_activity - start_time).total_seconds()
                session_durations.append(duration)
        
        return {
            'total_sessions': len(sessions),
            'average_session_duration': sum(session_durations) / len(session_durations) if session_durations else 0,
            'average_pages_per_session': sum(s.get('page_count', 0) for s in sessions) / len(sessions) if sessions else 0,
            'recent_sessions': sessions[-20:],  # Last 20 sessions
        }
    
    def _get_system_metrics(self):
        """
        Get current system metrics
        """
        return cache.get('mobile_system_metrics', {})


class MobileAnalyticsJavaScript:
    """
    JavaScript for mobile analytics tracking
    """
    
    @staticmethod
    def get_analytics_js():
        """
        Get JavaScript for mobile analytics tracking
        """
        js = """
        <script>
        class MobileAnalytics {
            constructor() {
                this.startTime = performance.now();
                this.init();
            }
            
            init() {
                this.trackPageView();
                this.trackUserActions();
                this.trackPerformance();
                this.trackErrors();
            }
            
            trackPageView() {
                const pageData = {
                    url: window.location.pathname,
                    title: document.title,
                    referrer: document.referrer,
                    screen_width: window.screen.width,
                    screen_height: window.screen.height,
                    connection_type: this.getConnectionType(),
                };
                
                this.sendAnalytics('page_view', pageData);
            }
            
            trackUserActions() {
                // Track clicks
                document.addEventListener('click', (e) => {
                    const target = e.target.closest('a, button, [role="button"]');
                    if (target) {
                        this.sendAnalytics('click', {
                            element: target.tagName.toLowerCase(),
                            text: target.textContent?.trim().substring(0, 50),
                            href: target.href || null,
                            class: target.className || null,
                        });
                    }
                });
                
                // Track form submissions
                document.addEventListener('submit', (e) => {
                    this.sendAnalytics('form_submit', {
                        form_action: e.target.action,
                        form_method: e.target.method,
                    });
                });
                
                // Track scroll depth
                let maxScroll = 0;
                window.addEventListener('scroll', () => {
                    const scrollPercent = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
                    if (scrollPercent > maxScroll) {
                        maxScroll = scrollPercent;
                        if (maxScroll % 25 === 0) { // Track every 25%
                            this.sendAnalytics('scroll_depth', { depth: maxScroll });
                        }
                    }
                });
            }
            
            trackPerformance() {
                // Track page load performance
                window.addEventListener('load', () => {
                    const loadTime = performance.now() - this.startTime;
                    
                    this.sendAnalytics('performance', {
                        load_time: loadTime,
                        dom_content_loaded: performance.getEntriesByType('navigation')[0]?.domContentLoadedEventEnd || 0,
                        first_paint: performance.getEntriesByType('paint')[0]?.startTime || 0,
                        first_contentful_paint: performance.getEntriesByType('paint')[1]?.startTime || 0,
                    });
                });
                
                // Track resource loading
                const observer = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (entry.entryType === 'resource') {
                            this.sendAnalytics('resource_load', {
                                name: entry.name,
                                duration: entry.duration,
                                size: entry.transferSize || 0,
                                type: entry.initiatorType,
                            });
                        }
                    }
                });
                
                observer.observe({ entryTypes: ['resource'] });
            }
            
            trackErrors() {
                // Track JavaScript errors
                window.addEventListener('error', (e) => {
                    this.sendAnalytics('error', {
                        type: 'javascript_error',
                        message: e.message,
                        filename: e.filename,
                        lineno: e.lineno,
                        colno: e.colno,
                    });
                });
                
                // Track unhandled promise rejections
                window.addEventListener('unhandledrejection', (e) => {
                    this.sendAnalytics('error', {
                        type: 'promise_rejection',
                        message: e.reason?.message || e.reason,
                    });
                });
            }
            
            getConnectionType() {
                if ('connection' in navigator) {
                    return navigator.connection.effectiveType || 'unknown';
                }
                return 'unknown';
            }
            
            async sendAnalytics(eventType, data) {
                try {
                    const payload = {
                        event_type: eventType,
                        timestamp: new Date().toISOString(),
                        data: data,
                        session_id: this.getSessionId(),
                    };
                    
                    await fetch('/api/mobile/analytics/track/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest',
                        },
                        body: JSON.stringify(payload),
                    });
                } catch (error) {
                    console.error('Analytics error:', error);
                }
            }
            
            getSessionId() {
                let sessionId = sessionStorage.getItem('analytics_session_id');
                if (!sessionId) {
                    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                    sessionStorage.setItem('analytics_session_id', sessionId);
                }
                return sessionId;
            }
        }
        
        // Initialize analytics when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
            new MobileAnalytics();
        });
        </script>
        """
        
        return format_html(js) 