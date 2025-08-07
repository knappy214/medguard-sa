# MedGuard SA - Wagtail 7.0.2 Development Setup

## Quick Start

1. **Activate your virtual environment**
```bash
source venv/bin/activate # Linux/Mac
```
or
```bash
venv\Scripts\activate # Windows
```

2. **Run the development setup**
```bash
chmod +x start_dev.sh
./start_dev.sh
```

3. **Or start manually with optimized settings**
```bash
python manage.py runserver --settings=medguard_backend.settings.development_wagtail_optimized
```

## Development URLs

- **Main Site**: http://localhost:8000/
- **Django Admin**: http://localhost:8000/admin/
- **Wagtail Admin**: http://localhost:8000/wagtail-admin/
- **API Root**: http://localhost:8000/api/
- **API Docs**: http://localhost:8000/api/docs/

## Development Features Enabled

✅ **Wagtail 7.0.2 Latest Features**
- Enhanced StreamField with improved performance
- Advanced workflow and moderation system  
- Improved admin interface with mobile support
- Enhanced search with PostgreSQL full-text search
- Responsive image optimization (WebP, AVIF)
- Universal listings and filtering
- Enhanced accessibility features

✅ **Development Tools**
- Django Debug Toolbar with all panels
- Enhanced logging with separate Wagtail logs
- Django Extensions (shell_plus, etc.)
- Performance profiling capabilities
- SQL query optimization tracking

✅ **Healthcare-Specific Features**  
- HIPAA compliance monitoring (development mode)
- Prescription workflow system
- Medication management with OCR support
- Security audit logging
- Patient data privacy controls

✅ **API & Integration**
- Enhanced DRF with browsable API
- Wagtail API v2 with custom endpoints
- CORS configured for frontend development
- WebSocket support for real-time features

## Development Commands

**Setup development environment**
```bash
python manage.py dev_setup
```

**Create sample data**
```bash
python manage.py dev_setup --skip-data
```

**Update search index**
```bash
python manage.py update_index
```

**Shell with models preloaded**
```bash
python manage.py shell_plus
```

**Show SQL queries**
```bash
python manage.py shell_plus --print-sql
```

**Run tests with coverage**
```bash
pytest --cov=. --cov-report=html
```

**Format code**
```bash
black .
isort .
```

## Troubleshooting

### Common Issues

1. **Migration Issues**
```bash
python manage.py migrate --run-syncdb
```

2. **Search Index Issues**
```bash
python manage.py update_index --rebuild
```

3. **Static Files Issues**  
```bash
python manage.py collectstatic --clear
```

4. **Cache Issues**
```bash
# Clear all caches
python manage.py shell_plus -c "from django.core.cache import cache; cache.clear()"
```

### Performance Monitoring

- **Debug Toolbar**: Available on all pages when DEBUG=True
- **Logs**: Check `logs/development.log` and `logs/wagtail_dev.log`
- **SQL Queries**: Monitor in debug toolbar SQL panel
- **Cache Performance**: Monitor in debug toolbar cache panel

## Security Notes

- CSRF protection is relaxed for API development
- SSL redirect is disabled for localhost
- Debug information is exposed (development only)
- Session security is relaxed for easier testing

*⚠️ Never use these settings in production!*
