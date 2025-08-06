"""
Enhanced mobile search with voice input support
Wagtail 7.0.2 search improvements
"""

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from wagtail.models import Page
from wagtail.search import index
from wagtail.search.backends import get_search_backend
import json
import logging
import speech_recognition as sr
from io import BytesIO
import base64

logger = logging.getLogger(__name__)


class MobileSearchEngine:
    """
    Enhanced mobile search engine with voice input support
    """
    
    def __init__(self):
        self.search_backend = get_search_backend()
        self.recognizer = sr.Recognizer()
        self.voice_enabled = True
    
    def search(self, query, page_type=None, filters=None, page=1, per_page=10):
        """
        Perform mobile-optimized search
        """
        try:
            # Get base queryset
            if page_type:
                queryset = Page.objects.type(page_type).live()
            else:
                queryset = Page.objects.live()
            
            # Apply filters
            if filters:
                queryset = self._apply_filters(queryset, filters)
            
            # Perform search
            if query:
                search_results = self.search_backend.search(query, queryset)
            else:
                search_results = queryset
            
            # Paginate results
            paginator = Paginator(search_results, per_page)
            page_obj = paginator.get_page(page)
            
            return {
                'results': page_obj,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'current_page': page,
                'total_pages': paginator.num_pages,
            }
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                'results': [],
                'total_count': 0,
                'error': str(e)
            }
    
    def _apply_filters(self, queryset, filters):
        """
        Apply search filters
        """
        for key, value in filters.items():
            if hasattr(queryset, key):
                queryset = getattr(queryset, key)(value)
        
        return queryset
    
    def voice_search(self, audio_data):
        """
        Convert voice input to text for search
        """
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data.split(',')[1])
            
            # Convert to audio file
            audio_file = BytesIO(audio_bytes)
            
            # Use speech recognition
            with sr.AudioFile(audio_file) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)
                
                return {
                    'success': True,
                    'text': text,
                    'confidence': 0.8  # Placeholder confidence
                }
                
        except Exception as e:
            logger.error(f"Voice search error: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class MobileSearchSuggestions:
    """
    Mobile search suggestions and autocomplete
    """
    
    def __init__(self):
        self.search_backend = get_search_backend()
    
    def get_suggestions(self, query, limit=5):
        """
        Get search suggestions based on query
        """
        try:
            # Search for pages with similar titles
            suggestions = []
            
            # Get pages with similar titles
            pages = Page.objects.live().filter(title__icontains=query)[:limit]
            for page in pages:
                suggestions.append({
                    'text': page.title,
                    'url': page.url,
                    'type': 'page'
                })
            
            # Get medication suggestions if available
            try:
                from medications.models import Medication
                medications = Medication.objects.filter(
                    name__icontains=query
                )[:limit]
                for med in medications:
                    suggestions.append({
                        'text': f"{med.name} - {med.generic_name}",
                        'url': f"/medications/{med.slug}/",
                        'type': 'medication'
                    })
            except ImportError:
                pass
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Search suggestions error: {e}")
            return []
    
    def get_popular_searches(self, limit=10):
        """
        Get popular search terms
        """
        # This could be enhanced with actual analytics data
        popular_terms = [
            'paracetamol',
            'ibuprofen',
            'antibiotics',
            'diabetes medication',
            'blood pressure',
            'cholesterol',
            'asthma',
            'allergies',
            'pain relief',
            'vitamins'
        ]
        
        return popular_terms[:limit]


class MobileSearchResults:
    """
    Mobile-optimized search results formatting
    """
    
    @staticmethod
    def format_search_result(page, query=None):
        """
        Format a single search result for mobile display
        """
        # Extract relevant content
        title = page.title
        url = page.url
        description = getattr(page, 'search_description', '')
        
        # If no description, try to get content
        if not description and hasattr(page, 'body'):
            try:
                # Get first few words from body
                body_text = str(page.body)
                description = body_text[:150] + '...' if len(body_text) > 150 else body_text
            except:
                description = ''
        
        # Highlight search terms
        if query:
            title = MobileSearchResults._highlight_terms(title, query)
            description = MobileSearchResults._highlight_terms(description, query)
        
        return {
            'title': title,
            'url': url,
            'description': description,
            'type': page.content_type.model,
            'last_published': page.last_published_at.isoformat() if page.last_published_at else None,
        }
    
    @staticmethod
    def _highlight_terms(text, query):
        """
        Highlight search terms in text
        """
        if not text or not query:
            return text
        
        query_terms = query.lower().split()
        highlighted_text = text
        
        for term in query_terms:
            if term in highlighted_text.lower():
                # Simple highlighting - could be enhanced with regex
                highlighted_text = highlighted_text.replace(
                    term, f'<mark>{term}</mark>'
                )
        
        return mark_safe(highlighted_text)


class MobileSearchInterface:
    """
    Mobile search interface components
    """
    
    @staticmethod
    def get_search_form_html(placeholder="Search medications..."):
        """
        Get mobile-optimized search form HTML
        """
        html = f"""
        <div class="mobile-search-container">
            <form class="mobile-search-form" id="mobileSearchForm">
                <div class="search-input-group">
                    <input type="text" 
                           class="mobile-search-input" 
                           placeholder="{placeholder}"
                           id="mobileSearchInput"
                           autocomplete="off">
                    <button type="button" 
                            class="voice-search-btn" 
                            id="voiceSearchBtn"
                            aria-label="Voice search">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                        </svg>
                    </button>
                    <button type="submit" 
                            class="search-submit-btn"
                            aria-label="Search">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                        </svg>
                    </button>
                </div>
                <div class="search-suggestions" id="searchSuggestions"></div>
            </form>
        </div>
        """
        
        return format_html(html)
    
    @staticmethod
    def get_search_results_html(results, query=None):
        """
        Get mobile-optimized search results HTML
        """
        if not results:
            return format_html('<div class="no-results">No results found</div>')
        
        html = '<div class="mobile-search-results">'
        
        for result in results:
            html += f"""
            <div class="search-result-item">
                <h3 class="result-title">
                    <a href="{result['url']}">{result['title']}</a>
                </h3>
                <p class="result-description">{result['description']}</p>
                <div class="result-meta">
                    <span class="result-type">{result['type']}</span>
                    {f'<span class="result-date">{result["last_published"]}</span>' if result.get('last_published') else ''}
                </div>
            </div>
            """
        
        html += '</div>'
        
        return format_html(html)


class MobileSearchCSS:
    """
    CSS for mobile search interface
    """
    
    @staticmethod
    def get_search_css():
        """
        Get CSS for mobile search interface
        """
        css = """
        <style>
        .mobile-search-container {
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
            padding: 1rem;
        }
        
        .mobile-search-form {
            position: relative;
        }
        
        .search-input-group {
            display: flex;
            align-items: center;
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .mobile-search-input {
            flex: 1;
            padding: 16px;
            border: none;
            outline: none;
            font-size: 16px;
            background: transparent;
        }
        
        .voice-search-btn,
        .search-submit-btn {
            padding: 16px;
            border: none;
            background: transparent;
            color: #6b7280;
            cursor: pointer;
            transition: color 0.2s ease;
            min-width: 48px;
            min-height: 48px;
        }
        
        .voice-search-btn:hover,
        .search-submit-btn:hover {
            color: #2563eb;
        }
        
        .voice-search-btn.recording {
            color: #dc2626;
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .search-suggestions {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #e2e8f0;
            border-top: none;
            border-radius: 0 0 12px 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            z-index: 1000;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .suggestion-item {
            padding: 12px 16px;
            border-bottom: 1px solid #f3f4f6;
            cursor: pointer;
            transition: background-color 0.2s ease;
        }
        
        .suggestion-item:hover {
            background-color: #f9fafb;
        }
        
        .suggestion-item:last-child {
            border-bottom: none;
        }
        
        .mobile-search-results {
            margin-top: 2rem;
        }
        
        .search-result-item {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .result-title {
            margin: 0 0 0.5rem 0;
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        .result-title a {
            color: #2563eb;
            text-decoration: none;
        }
        
        .result-title a:hover {
            text-decoration: underline;
        }
        
        .result-description {
            margin: 0 0 0.5rem 0;
            color: #6b7280;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        
        .result-meta {
            display: flex;
            gap: 1rem;
            font-size: 0.8rem;
            color: #9ca3af;
        }
        
        .result-type {
            background: #f3f4f6;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            font-weight: 500;
        }
        
        .no-results {
            text-align: center;
            padding: 2rem;
            color: #6b7280;
            font-style: italic;
        }
        
        mark {
            background-color: #fef3c7;
            color: #92400e;
            padding: 1px 2px;
            border-radius: 2px;
        }
        
        /* Mobile optimizations */
        @media (max-width: 768px) {
            .mobile-search-container {
                padding: 0.5rem;
            }
            
            .mobile-search-input {
                font-size: 16px; /* Prevent zoom on iOS */
            }
            
            .search-result-item {
                margin-bottom: 0.5rem;
                padding: 0.75rem;
            }
        }
        </style>
        """
        
        return format_html(css)


class MobileSearchJavaScript:
    """
    JavaScript for mobile search functionality
    """
    
    @staticmethod
    def get_search_js():
        """
        Get JavaScript for mobile search functionality
        """
        js = """
        <script>
        class MobileSearch {
            constructor() {
                this.searchInput = document.getElementById('mobileSearchInput');
                this.voiceBtn = document.getElementById('voiceSearchBtn');
                this.suggestionsContainer = document.getElementById('searchSuggestions');
                this.searchForm = document.getElementById('mobileSearchForm');
                this.isRecording = false;
                this.mediaRecorder = null;
                this.audioChunks = [];
                
                this.init();
            }
            
            init() {
                this.setupEventListeners();
                this.setupVoiceSearch();
            }
            
            setupEventListeners() {
                // Search input events
                this.searchInput.addEventListener('input', this.handleInput.bind(this));
                this.searchInput.addEventListener('focus', this.showSuggestions.bind(this));
                this.searchInput.addEventListener('blur', this.hideSuggestions.bind(this));
                
                // Form submission
                this.searchForm.addEventListener('submit', this.handleSubmit.bind(this));
                
                // Voice search
                this.voiceBtn.addEventListener('click', this.toggleVoiceSearch.bind(this));
                
                // Click outside to close suggestions
                document.addEventListener('click', (e) => {
                    if (!this.searchInput.contains(e.target) && !this.suggestionsContainer.contains(e.target)) {
                        this.hideSuggestions();
                    }
                });
            }
            
            setupVoiceSearch() {
                // Check if browser supports speech recognition
                if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                    this.speechRecognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                    this.speechRecognition.continuous = false;
                    this.speechRecognition.interimResults = false;
                    this.speechRecognition.lang = 'en-US';
                    
                    this.speechRecognition.onresult = (event) => {
                        const transcript = event.results[0][0].transcript;
                        this.searchInput.value = transcript;
                        this.handleInput();
                        this.stopVoiceSearch();
                    };
                    
                    this.speechRecognition.onerror = (event) => {
                        console.error('Speech recognition error:', event.error);
                        this.stopVoiceSearch();
                    };
                } else {
                    this.voiceBtn.style.display = 'none';
                }
            }
            
            async handleInput() {
                const query = this.searchInput.value.trim();
                
                if (query.length < 2) {
                    this.hideSuggestions();
                    return;
                }
                
                try {
                    const suggestions = await this.getSuggestions(query);
                    this.showSuggestions(suggestions);
                } catch (error) {
                    console.error('Error getting suggestions:', error);
                }
            }
            
            async getSuggestions(query) {
                const response = await fetch(`/api/mobile/search/suggestions/?q=${encodeURIComponent(query)}`);
                return await response.json();
            }
            
            showSuggestions(suggestions = []) {
                if (suggestions.length === 0) {
                    this.hideSuggestions();
                    return;
                }
                
                this.suggestionsContainer.innerHTML = suggestions.map(suggestion => `
                    <div class="suggestion-item" data-url="${suggestion.url}">
                        <div class="suggestion-text">${suggestion.text}</div>
                        <div class="suggestion-type">${suggestion.type}</div>
                    </div>
                `).join('');
                
                this.suggestionsContainer.style.display = 'block';
                
                // Add click handlers
                this.suggestionsContainer.querySelectorAll('.suggestion-item').forEach(item => {
                    item.addEventListener('click', () => {
                        window.location.href = item.dataset.url;
                    });
                });
            }
            
            hideSuggestions() {
                this.suggestionsContainer.style.display = 'none';
            }
            
            toggleVoiceSearch() {
                if (this.isRecording) {
                    this.stopVoiceSearch();
                } else {
                    this.startVoiceSearch();
                }
            }
            
            startVoiceSearch() {
                if (this.speechRecognition) {
                    this.speechRecognition.start();
                    this.isRecording = true;
                    this.voiceBtn.classList.add('recording');
                    this.voiceBtn.setAttribute('aria-label', 'Stop recording');
                }
            }
            
            stopVoiceSearch() {
                if (this.speechRecognition) {
                    this.speechRecognition.stop();
                    this.isRecording = false;
                    this.voiceBtn.classList.remove('recording');
                    this.voiceBtn.setAttribute('aria-label', 'Voice search');
                }
            }
            
            handleSubmit(e) {
                e.preventDefault();
                const query = this.searchInput.value.trim();
                
                if (query) {
                    window.location.href = `/search/?q=${encodeURIComponent(query)}`;
                }
            }
        }
        
        // Initialize when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
            new MobileSearch();
        });
        </script>
        """
        
        return format_html(js) 