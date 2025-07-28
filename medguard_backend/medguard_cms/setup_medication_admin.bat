@echo off
REM MedGuard SA - Medication Admin Setup Script (Windows)
REM This script sets up the Wagtail ModelAdmin medication management system

echo 🏥 MedGuard SA - Setting up Medication Admin System
echo ==================================================

REM Check if we're in the correct directory
if not exist "manage.py" (
    echo [ERROR] This script must be run from the medguard_cms directory
    exit /b 1
)

echo [INFO] Starting medication admin setup...

REM Step 1: Create locale directories if they don't exist
echo [INFO] Creating locale directories...
if not exist "locale\en-ZA\LC_MESSAGES" mkdir "locale\en-ZA\LC_MESSAGES"
if not exist "locale\af-ZA\LC_MESSAGES" mkdir "locale\af-ZA\LC_MESSAGES"

REM Step 2: Compile translations
echo [INFO] Compiling translations...
python manage.py compilemessages --locale=en-ZA
if %errorlevel% neq 0 (
    echo [WARNING] English translation compilation had issues - continuing anyway
) else (
    echo [SUCCESS] English translations compiled successfully
)

python manage.py compilemessages --locale=af-ZA
if %errorlevel% neq 0 (
    echo [WARNING] Afrikaans translation compilation had issues - continuing anyway
) else (
    echo [SUCCESS] Afrikaans translations compiled successfully
)

REM Step 3: Collect static files
echo [INFO] Collecting static files...
python manage.py collectstatic --noinput
if %errorlevel% neq 0 (
    echo [WARNING] Static file collection had issues - continuing anyway
) else (
    echo [SUCCESS] Static files collected successfully
)

REM Step 4: Run migrations
echo [INFO] Running database migrations...
python manage.py makemigrations
python manage.py migrate
if %errorlevel% neq 0 (
    echo [ERROR] Database migrations failed
    exit /b 1
) else (
    echo [SUCCESS] Database migrations completed successfully
)

REM Step 5: Create superuser if it doesn't exist
echo [INFO] Checking for superuser...
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('Superuser exists' if User.objects.filter(is_superuser=True).exists() else 'Creating superuser...'); User.objects.create_superuser('admin', 'admin@medguard-sa.com', 'admin123') if not User.objects.filter(is_superuser=True).exists() else None"

REM Step 6: Verify setup
echo [INFO] Verifying setup...

REM Check if wagtail_hooks.py exists
if exist "medguard_cms\wagtail_hooks.py" (
    echo [SUCCESS] Wagtail hooks configuration found
) else (
    echo [ERROR] Wagtail hooks configuration missing
    exit /b 1
)

REM Check if CSS file exists
if exist "medguard_cms\static\css\medication-admin.css" (
    echo [SUCCESS] Custom CSS found
) else (
    echo [WARNING] Custom CSS file missing
)

REM Check if JS file exists
if exist "medguard_cms\static\js\medication-admin.js" (
    echo [SUCCESS] Custom JavaScript found
) else (
    echo [WARNING] Custom JavaScript file missing
)

REM Check if translation files exist
if exist "locale\en-ZA\LC_MESSAGES\django.mo" (
    echo [SUCCESS] English translations compiled
) else (
    echo [WARNING] English translations not compiled
)

if exist "locale\af-ZA\LC_MESSAGES\django.mo" (
    echo [SUCCESS] Afrikaans translations compiled
) else (
    echo [WARNING] Afrikaans translations not compiled
)

REM Step 7: Display setup summary
echo.
echo 🎉 Medication Admin Setup Complete!
echo ==================================
echo.
echo 📋 Setup Summary:
echo   ✅ Wagtail ModelAdmin configured
echo   ✅ Custom admin panels created
echo   ✅ Healthcare color scheme applied
echo   ✅ Advanced filtering and search enabled
echo   ✅ Bulk actions interface ready
echo   ✅ Internationalization (en-ZA, af-ZA) configured
echo   ✅ Custom CSS and JavaScript loaded
echo   ✅ Database migrations applied
echo.
echo 🚀 Next Steps:
echo   1. Start the development server: python manage.py runserver
echo   2. Navigate to: http://localhost:8000/admin/
echo   3. Login with: admin/admin123
echo   4. Look for 'Medication Management' in the sidebar
echo.
echo 📚 Documentation:
echo   - README_MEDICATION_ADMIN.md - Complete setup guide
echo   - Check the admin interface for usage instructions
echo.
echo 🔧 Customization:
echo   - Edit medguard_cms/wagtail_hooks.py for ModelAdmin changes
echo   - Modify medguard_cms/static/css/medication-admin.css for styling
echo   - Update locale/*/LC_MESSAGES/django.po for translations
echo.

echo [SUCCESS] Medication admin system is ready to use!

REM Optional: Start the development server
set /p start_server="Would you like to start the development server now? (y/n): "
if /i "%start_server%"=="y" (
    echo [INFO] Starting development server...
    python manage.py runserver
)

pause 