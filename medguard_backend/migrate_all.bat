@echo off
REM MedGuard SA Migration Script - Windows Batch File
REM This file provides an easy way to run the migration script on Windows

echo.
echo ========================================
echo   MedGuard SA Migration Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "manage.py" (
    echo ERROR: manage.py not found in current directory
    echo Please run this script from the medguard_backend directory
    pause
    exit /b 1
)

REM Check if migration script exists
if not exist "migrate_all.py" (
    echo ERROR: migrate_all.py not found
    echo Please ensure the migration script is in the current directory
    pause
    exit /b 1
)

REM Parse command line arguments
set "DRY_RUN="
set "BACKUP_ONLY="
set "VERIFY_ONLY="

:parse_args
if "%1"=="" goto :run_script
if "%1"=="--dry-run" set "DRY_RUN=--dry-run"
if "%1"=="--backup-only" set "BACKUP_ONLY=--backup-only"
if "%1"=="--verify-only" set "VERIFY_ONLY=--verify-only"
if "%1"=="--help" goto :show_help
shift
goto :parse_args

:show_help
echo Usage: migrate_all.bat [options]
echo.
echo Options:
echo   --dry-run      Preview changes without executing
echo   --backup-only  Only create database backup
echo   --verify-only  Only run verification checks
echo   --help         Show this help message
echo.
echo Examples:
echo   migrate_all.bat
echo   migrate_all.bat --dry-run
echo   migrate_all.bat --backup-only
echo   migrate_all.bat --verify-only
echo.
pause
exit /b 0

:run_script
echo Starting migration script...
echo.

REM Run the migration script with provided arguments
python migrate_all.py %DRY_RUN% %BACKUP_ONLY% %VERIFY_ONLY%

REM Check exit code
if errorlevel 1 (
    echo.
    echo ========================================
    echo   Migration failed with errors
    echo ========================================
    echo.
    echo Please check the log files for details:
    echo - migration_execution.log
    echo - migration_report_*.json
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo   Migration completed successfully
    echo ========================================
    echo.
    echo Check the following files for details:
    echo - migration_execution.log
    echo - migration_report_*.json
    echo - backups/ (if backup was created)
    echo.
    pause
    exit /b 0
) 