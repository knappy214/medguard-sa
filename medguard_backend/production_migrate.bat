@echo off
REM Production Migration Script for MedGuard SA - Windows Batch Wrapper
REM
REM This script provides easy-to-use commands for production deployment.
REM It wraps the Python migration script with additional safety checks.
REM
REM Usage:
REM     production_migrate.bat [command] [options]
REM
REM Commands:
REM     check-migrations    - Check for pending migrations without applying them
REM     migrate             - Run all migrations safely
REM     migrate-apps        - Run migrations for specific apps with detailed logging
REM     collectstatic       - Collect static files
REM     deploy-check        - Run deployment validation
REM     full-deploy         - Run complete deployment sequence
REM     backup              - Create database backup before migration
REM     help                - Show this help message

setlocal enabledelayedexpansion

REM Set script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Initialize variables
set "PYTHON_CMD="
set "DJANGO_SETTINGS_MODULE=medguard_backend.settings.production"

REM Color codes for output
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Logging functions
:log
echo %BLUE%[%date% %time%]%NC% %~1
goto :eof

:error
echo %RED%[ERROR]%NC% %~1 >&2
goto :eof

:warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

REM Check if Python is available
:check_python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :eof
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python3"
    goto :eof
)

call :error "Python is not installed or not in PATH"
exit /b 1

REM Check if virtual environment is activated
:check_venv
if "%VIRTUAL_ENV%"=="" (
    call :warning "Virtual environment not detected"
    if exist ".venv\Scripts\activate.bat" (
        call :log "Activating virtual environment..."
        call .venv\Scripts\activate.bat
    ) else if exist "venv\Scripts\activate.bat" (
        call :log "Activating virtual environment..."
        call venv\Scripts\activate.bat
    ) else (
        call :warning "No virtual environment found. Make sure dependencies are installed."
    )
)
goto :eof

REM Check if Django is installed
:check_django
%PYTHON_CMD% -c "import django" >nul 2>&1
if %errorlevel% neq 0 (
    call :error "Django is not installed. Please install requirements first."
    exit /b 1
)
goto :eof

REM Check if manage.py exists
:check_manage_py
if not exist "manage.py" (
    call :error "manage.py not found. Please run this script from the Django project root."
    exit /b 1
)
goto :eof

REM Check environment variables
:check_environment
if "%DJANGO_SETTINGS_MODULE%"=="" (
    set "DJANGO_SETTINGS_MODULE=medguard_backend.settings.production"
    call :log "Set DJANGO_SETTINGS_MODULE to production"
)

REM Check for required environment variables
set "missing_vars="
if "%DB_NAME%"=="" set "missing_vars=%missing_vars% DB_NAME"
if "%DB_USER%"=="" set "missing_vars=%missing_vars% DB_USER"
if "%DB_PASSWORD%"=="" set "missing_vars=%missing_vars% DB_PASSWORD"

if not "%missing_vars%"=="" (
    call :warning "Missing environment variables: %missing_vars%"
    call :warning "Make sure these are set in your environment or .env file"
)
goto :eof

REM Show help
:show_help
echo Production Migration Script for MedGuard SA
echo.
echo Usage: %~nx0 [command] [options]
echo.
echo Commands:
echo     check-migrations    - Check for pending migrations without applying them
echo     migrate             - Run all migrations safely
echo     migrate-apps        - Run migrations for specific apps with detailed logging
echo     collectstatic       - Collect static files
echo     deploy-check        - Run deployment validation
echo     full-deploy         - Run complete deployment sequence
echo     backup              - Create database backup before migration
echo     help                - Show this help message
echo.
echo Options:
echo     --run-syncdb        - Run syncdb for initial deployment (with migrate command)
echo     --apps APP1 APP2    - Specific apps to migrate (with migrate-apps command)
echo     --no-backup         - Skip database backup before migration
echo.
echo Examples:
echo     %~nx0 check-migrations
echo     %~nx0 migrate --run-syncdb
echo     %~nx0 migrate-apps --apps medications users
echo     %~nx0 full-deploy
echo     %~nx0 backup
echo.
echo Environment Variables:
echo     DJANGO_SETTINGS_MODULE - Django settings module (default: medguard_backend.settings.production)
echo     DB_NAME                - Database name
echo     DB_USER                - Database user
echo     DB_PASSWORD            - Database password
echo     DB_HOST                - Database host (default: localhost)
echo     DB_PORT                - Database port (default: 5432)
echo.
goto :eof

REM Main function
:main
set "command=%~1"
if "%command%"=="" goto :show_help
if "%command%"=="help" goto :show_help
if "%command%"=="--help" goto :show_help
if "%command%"=="-h" goto :show_help

call :log "Starting production migration script..."

REM Pre-flight checks
call :check_python
call :check_venv
call :check_django
call :check_manage_py
call :check_environment

REM Build command arguments
set "args=%command%"

REM Handle specific command options
if "%command%"=="migrate" (
    :migrate_loop
    shift
    if "%~1"=="" goto :execute
    if "%~1"=="--run-syncdb" (
        set "args=%args% --run-syncdb"
        goto :migrate_loop
    )
    if "%~1"=="--no-backup" (
        set "args=%args% --no-backup"
        goto :migrate_loop
    )
    call :error "Unknown option: %~1"
    exit /b 1
)

if "%command%"=="migrate-apps" (
    set "apps="
    :migrate_apps_loop
    shift
    if "%~1"=="" goto :check_apps
    if "%~1"=="--apps" (
        :apps_loop
        shift
        if "%~1"=="" goto :check_apps
        if "%~1"=="--" goto :check_apps
        if "%~1"=="--run-syncdb" goto :check_apps
        if "%~1"=="--no-backup" goto :check_apps
        if "%apps%"=="" (
            set "apps=%~1"
        ) else (
            set "apps=%apps% %~1"
        )
        goto :apps_loop
    )
    call :error "Unknown option: %~1"
    exit /b 1
)

:check_apps
if "%apps%"=="" (
    call :error "Please specify apps to migrate with --apps"
    exit /b 1
)
set "args=%args% --apps %apps%"

:execute
REM Execute the Python script
call :log "Executing: %PYTHON_CMD% production_migrate.py %args%"

%PYTHON_CMD% production_migrate.py %args%
if %errorlevel% equ 0 (
    call :success "Migration command completed successfully"
    exit /b 0
) else (
    call :error "Migration command failed"
    exit /b 1
)

REM Handle script interruption
:cleanup
call :error "Script interrupted by user"
exit /b 1

REM Run main function with all arguments
call :main %* 