# MedGuard SA - Django Internationalization (i18n) Setup

This document describes the internationalization configuration for the MedGuard SA Django backend project.

## Overview

The project is configured to support multiple languages with Django's built-in internationalization system and Wagtail's content management internationalization features.

## Supported Languages

- **English** (`en`) - Default language
- **Afrikaans** (`af`) - Secondary language

## Configuration

### Django Settings (`medguard_backend/settings/base.py`)

#### Core i18n Settings
```python
# Internationalization
LANGUAGE_CODE = 'en'
TIME_ZONE = 'Africa/Johannesburg'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Supported languages for Django frontend
LANGUAGES = [
    ('en', _('English')),
    ('af', _('Afrikaans')),
]

# Wagtail content languages (can be same as LANGUAGES or subset)
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES

# Enable Wagtail internationalization
WAGTAIL_I18N_ENABLED = True

# Locale paths for translation files
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
```

#### Middleware Configuration
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Language detection
    'django.middleware.common.CommonMiddleware',
    # ... other middleware
]
```

#### Template Context Processors
```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # ... other processors
                'django.template.context_processors.i18n',  # Language variables
            ],
        },
    },
]
```

### URL Configuration (`medguard_backend/urls.py`)

The project uses Django's `i18n_patterns` to automatically add language prefixes to URLs:

```python
from django.conf.urls.i18n import i18n_patterns

# Non-translatable URLs (admin, API, etc.)
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),  # Language switching
    path('django-admin/', admin.site.urls),
    path('admin/', include('wagtail.admin.urls')),
    # ... API endpoints
]

# Translatable URLs (with language prefix)
urlpatterns += i18n_patterns(
    path('search/', include('search.urls')),
    path('medications/', include('medications.urls')),
    path('home/', include('home.urls')),
    path('', include('wagtail.urls')),
    prefix_default_language=False,  # No prefix for default language
)
```

## Translation Files

### Directory Structure
```
medguard_backend/
└── locale/
    ├── en/
    │   └── LC_MESSAGES/
    │       ├── django.po
    │       └── django.mo
    └── af/
        └── LC_MESSAGES/
            ├── django.po
            └── django.mo
```

### Translation File Headers

#### English (`locale/en/LC_MESSAGES/django.po`)
```po
# English translations for MedGuard SA.
# Copyright (C) 2025 MedGuard SA
msgid ""
msgstr ""
"Project-Id-Version: MedGuard SA 1.0\n"
"Language-Team: en\n"
"Language: en\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"
```

#### Afrikaans (`locale/af/LC_MESSAGES/django.po`)
```po
# Afrikaans translations for MedGuard SA.
# Copyright (C) 2024 MedGuard SA
msgid ""
msgstr ""
"Project-Id-Version: MedGuard SA 1.0\n"
"Language: af\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"
```

## Usage

### In Python Code

```python
from django.utils.translation import gettext as _

# Simple translation
message = _("Medications")

# Context-aware translation
from django.utils.translation import pgettext
message = pgettext("context", "Medications")

# Pluralization
from django.utils.translation import ngettext
count = 5
message = ngettext("1 medication", "%(count)d medications", count) % {'count': count}
```

### In Templates

```django
{% load i18n %}

{# Simple translation #}
<h1>{% translate "MedGuard SA" %}</h1>

{# Context-aware translation #}
<p>{% translate "Medications" context "medical" %}</p>

{# Block translation with variables #}
{% blocktranslate with name=user.name %}
Welcome, {{ name }}!
{% endblocktranslate %}

{# Pluralization #}
{% blocktranslate count counter=medication_count %}
{{ counter }} medication found.
{% plural %}
{{ counter }} medications found.
{% endblocktranslate %}
```

### Language Switching

#### Form-based Language Selection
```django
<form action="{% url 'set_language' %}" method="post">
    {% csrf_token %}
    <input name="next" type="hidden" value="{{ request.path }}">
    <select name="language">
        {% get_current_language as LANGUAGE_CODE %}
        {% get_available_languages as LANGUAGES %}
        {% get_language_info_list for LANGUAGES as languages %}
        {% for language in languages %}
            <option value="{{ language.code }}"{% if language.code == LANGUAGE_CODE %} selected{% endif %}>
                {{ language.name_local }} ({{ language.code }})
            </option>
        {% endfor %}
    </select>
    <input type="submit" value="{% translate 'Change Language' %}">
</form>
```

#### Link-based Language Selection
```django
{% for lang_code, lang_name in LANGUAGES %}
    <a href="{% url 'set_language' %}?language={{ lang_code }}&next={{ request.path|urlencode }}">
        {{ lang_name }}
    </a>
{% endfor %}
```

## Testing

### Test Script
Run the test script to verify the configuration:

```bash
cd medguard_backend
python test_i18n.py
```

### Test View
Visit the test page to see the internationalization in action:

- English: `http://localhost:8000/home/i18n-test/`
- Afrikaans: `http://localhost:8000/af/home/i18n-test/`

## Wagtail Integration

### Content Languages
Wagtail content can be created in multiple languages. The `WAGTAIL_CONTENT_LANGUAGES` setting defines which languages are available for content creation.

### Translatable Models
To make models translatable, inherit from `TranslatableMixin`:

```python
from wagtail.models import TranslatableMixin

class MyModel(TranslatableMixin, models.Model):
    name = models.CharField(max_length=255)
    # ... other fields
```

### Page Translations
Wagtail pages can have translations in different languages. Use the `page.localized` property to get the translated version:

```python
# Get the page in the current language
current_page = page.localized

# Get the page in a specific language
from django.utils.translation import override
with override('af'):
    afrikaans_page = page.localized
```

## Management Commands

### Extract Messages
```bash
python manage.py makemessages -l en
python manage.py makemessages -l af
python manage.py makemessages --all
```

### Compile Messages
```bash
python manage.py compilemessages
```

### Update Messages
```bash
python manage.py makemessages -l en --update
python manage.py makemessages -l af --update
```

## Best Practices

1. **Always use translation functions** for user-facing strings
2. **Provide context** when translations might be ambiguous
3. **Use pluralization** for countable items
4. **Test translations** in all supported languages
5. **Keep translation files updated** when adding new strings
6. **Use meaningful translation keys** that describe the content
7. **Review translations** for accuracy and cultural appropriateness

## Troubleshooting

### Common Issues

1. **Translation not working**: Check if `USE_I18N = True` and `LocaleMiddleware` is in `MIDDLEWARE`
2. **Language not switching**: Verify `i18n_patterns` is used in URLs and `set_language` view is included
3. **Missing translations**: Run `makemessages` to extract new strings and `compilemessages` to compile
4. **Wagtail i18n not working**: Ensure `WAGTAIL_I18N_ENABLED = True` and `WAGTAIL_CONTENT_LANGUAGES` is set

### Debug Tools

- Use `django-debug-toolbar` to inspect language detection
- Check `request.LANGUAGE_CODE` in views
- Use `{% get_current_language %}` in templates
- Monitor Django logs for i18n-related messages

## References

- [Django Internationalization Documentation](https://docs.djangoproject.com/en/5.2/topics/i18n/)
- [Wagtail Internationalization Guide](https://docs.wagtail.org/en/stable/advanced_topics/i18n.html)
- [Django Translation Utilities](https://docs.djangoproject.com/en/5.2/ref/utils/#translation-functions) 