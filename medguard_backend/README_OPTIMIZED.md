# MedGuard SA Backend - Optimized

This is the optimized Django + Wagtail CMS backend for MedGuard SA, following the latest best practices for Django 5.2 and Wagtail 7.0.

## 🚀 Features

- **Modern Django 5.2** with latest security and performance improvements
- **Wagtail 7.0 CMS** for content management
- **PostgreSQL** database with optimized queries
- **Redis** for caching and background tasks
- **REST API** with Django REST Framework
- **Internationalization** support (English & Afrikaans)
- **Comprehensive logging** and monitoring
- **Security best practices** implementation
- **Modular architecture** with proper separation of concerns

## 📁 Project Structure

```
medguard_backend/
├── medguard_backend/          # Main project directory
│   ├── settings/             # Settings package
│   │   ├── __init__.py
│   │   ├── base.py          # Common settings
│   │   ├── development.py   # Development settings
│   │   └── production.py    # Production settings
│   ├── urls.py              # Main URL configuration
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── home/                     # Home page app
├── search/                   # Search functionality
├── users/                    # User management
├── medications/              # Medication management
├── notifications/            # Notification system
├── wagtail_hooks/           # Wagtail customizations
├── templates/               # HTML templates
├── static/                  # Static files
├── media/                   # User uploaded files
├── locale/                  # Translation files
├── requirements.txt         # Python dependencies
└── manage.py               # Django management script
```

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Node.js 18+ (for frontend assets)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd medguard_backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_NAME=medguard_sa
DB_USER=medguard_user
DB_PASSWORD=medguard123
DB_HOST=localhost
DB_PORT=5432

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@medguard-sa.com

# Redis Settings
REDIS_URL=redis://localhost:6379/1
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Wagtail Settings
WAGTAILADMIN_BASE_URL=http://localhost:8000

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Media Settings
MEDIA_URL=/media/
```

### 3. Database Setup

```bash
# Create database
createdb medguard_sa

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (if available)
python manage.py loaddata initial_data.json
```

### 4. Static Files

```bash
# Collect static files
python manage.py collectstatic

# Compile translations
python manage.py compilemessages
```

## 🚀 Running the Application

### Development

```bash
# Run development server
python manage.py runserver

# Run with specific settings
DJANGO_SETTINGS_MODULE=medguard_backend.settings.development python manage.py runserver
```

### Production

```bash
# Run with production settings
DJANGO_SETTINGS_MODULE=medguard_backend.settings.production python manage.py runserver
```

## 📚 Key Components

### 1. Settings Structure

The project uses a modular settings structure:

- **base.py**: Common settings shared across environments
- **development.py**: Development-specific settings
- **production.py**: Production-specific settings with security hardening

### 2. Wagtail Integration

- **HomePage**: Main landing page with hero sections and content
- **MedicationIndexPage**: Lists all medications with filtering
- **MedicationDetailPage**: Individual medication details
- **NotificationIndexPage**: System notifications
- **Search functionality**: Cross-model search capabilities

### 3. Model Architecture

#### Users
- Custom User model with healthcare-specific fields
- User types: Patient, Caregiver, Healthcare Provider, Admin
- Medical record numbers and emergency contacts

#### Medications
- Comprehensive medication management
- Stock tracking and alerts
- Medication schedules and adherence logging
- Expiration date management

#### Notifications
- Multi-channel notification system
- Template-based notifications
- User notification tracking
- Priority and acknowledgment system

### 4. API Endpoints

The backend provides REST API endpoints for:

- `/api/users/` - User management
- `/api/medications/` - Medication management
- `/api/notifications/` - Notification system
- `/search/` - Search functionality

## 🔧 Management Commands

```bash
# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic

# User management
python manage.py createsuperuser
python manage.py changepassword

# Content management
python manage.py compilemessages
python manage.py loaddata

# Development utilities
python manage.py shell
python manage.py dbshell
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users
python manage.py test medications
python manage.py test notifications

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## 📊 Monitoring and Logging

The application includes comprehensive logging:

- **File logging**: All logs stored in `logs/django.log`
- **Console logging**: Development-friendly output
- **Error tracking**: Detailed error reporting
- **Performance monitoring**: Database query optimization

## 🔒 Security Features

- **HTTPS enforcement** in production
- **CSRF protection** enabled
- **XSS protection** headers
- **Content Security Policy** (CSP)
- **Secure cookie settings**
- **Password validation** with strong requirements
- **Session security** with Redis backend

## 🌐 Internationalization

The application supports multiple languages:

- **English (en-ZA)**: Primary language
- **Afrikaans (af-ZA)**: Secondary language

Translation files are located in `locale/` directory.

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker
docker-compose up --build
```

### Manual Deployment

1. Set `DJANGO_SETTINGS_MODULE=medguard_backend.settings.production`
2. Configure environment variables
3. Run `python manage.py collectstatic`
4. Set up reverse proxy (Nginx)
5. Configure SSL certificates
6. Set up monitoring and backups

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔄 Changelog

### Version 2.0.0 (Optimized)
- Upgraded to Django 5.2
- Upgraded to Wagtail 7.0
- Implemented modular settings structure
- Added comprehensive API endpoints
- Enhanced security features
- Improved performance and caching
- Added internationalization support
- Implemented proper logging and monitoring 