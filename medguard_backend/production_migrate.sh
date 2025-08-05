#!/bin/bash
"""
Production Migration Script for MedGuard SA - Shell Wrapper

This script provides easy-to-use commands for production deployment.
It wraps the Python migration script with additional safety checks.

Usage:
    ./production_migrate.sh [command] [options]

Commands:
    check-migrations    - Check for pending migrations without applying them
    migrate             - Run all migrations safely
    migrate-apps        - Run migrations for specific apps with detailed logging
    collectstatic       - Collect static files
    deploy-check        - Run deployment validation
    full-deploy         - Run complete deployment sequence
    backup              - Create database backup before migration
    help                - Show this help message

Examples:
    ./production_migrate.sh check-migrations
    ./production_migrate.sh migrate --run-syncdb
    ./production_migrate.sh migrate-apps medications users
    ./production_migrate.sh full-deploy
"""

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if Python is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        if ! command -v python &> /dev/null; then
            error "Python is not installed or not in PATH"
            exit 1
        fi
        PYTHON_CMD="python"
    else
        PYTHON_CMD="python3"
    fi
}

# Check if virtual environment is activated
check_venv() {
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        warning "Virtual environment not detected"
        if [[ -d ".venv" ]]; then
            log "Activating virtual environment..."
            source .venv/bin/activate
        elif [[ -d "venv" ]]; then
            log "Activating virtual environment..."
            source venv/bin/activate
        else
            warning "No virtual environment found. Make sure dependencies are installed."
        fi
    fi
}

# Check if Django is installed
check_django() {
    if ! $PYTHON_CMD -c "import django" 2>/dev/null; then
        error "Django is not installed. Please install requirements first."
        exit 1
    fi
}

# Check if manage.py exists
check_manage_py() {
    if [[ ! -f "manage.py" ]]; then
        error "manage.py not found. Please run this script from the Django project root."
        exit 1
    fi
}

# Check environment variables
check_environment() {
    if [[ -z "${DJANGO_SETTINGS_MODULE:-}" ]]; then
        export DJANGO_SETTINGS_MODULE="medguard_backend.settings.production"
        log "Set DJANGO_SETTINGS_MODULE to production"
    fi
    
    # Check for required environment variables
    local required_vars=("DB_NAME" "DB_USER" "DB_PASSWORD")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        warning "Missing environment variables: ${missing_vars[*]}"
        warning "Make sure these are set in your environment or .env file"
    fi
}

# Show help
show_help() {
    cat << EOF
Production Migration Script for MedGuard SA

Usage: $0 [command] [options]

Commands:
    check-migrations    - Check for pending migrations without applying them
    migrate             - Run all migrations safely
    migrate-apps        - Run migrations for specific apps with detailed logging
    collectstatic       - Collect static files
    deploy-check        - Run deployment validation
    full-deploy         - Run complete deployment sequence
    backup              - Create database backup before migration
    help                - Show this help message

Options:
    --run-syncdb        - Run syncdb for initial deployment (with migrate command)
    --apps APP1 APP2    - Specific apps to migrate (with migrate-apps command)
    --no-backup         - Skip database backup before migration

Examples:
    $0 check-migrations
    $0 migrate --run-syncdb
    $0 migrate-apps --apps medications users
    $0 full-deploy
    $0 backup

Environment Variables:
    DJANGO_SETTINGS_MODULE - Django settings module (default: medguard_backend.settings.production)
    DB_NAME                - Database name
    DB_USER                - Database user
    DB_PASSWORD            - Database password
    DB_HOST                - Database host (default: localhost)
    DB_PORT                - Database port (default: 5432)

EOF
}

# Main function
main() {
    local command="${1:-}"
    shift 2>/dev/null || true
    
    # Show help if no command or help requested
    if [[ -z "$command" || "$command" == "help" || "$command" == "--help" || "$command" == "-h" ]]; then
        show_help
        exit 0
    fi
    
    log "Starting production migration script..."
    
    # Pre-flight checks
    check_python
    check_venv
    check_django
    check_manage_py
    check_environment
    
    # Build command arguments
    local args=("$command")
    
    # Handle specific command options
    case "$command" in
        "migrate")
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --run-syncdb)
                        args+=("--run-syncdb")
                        shift
                        ;;
                    --no-backup)
                        args+=("--no-backup")
                        shift
                        ;;
                    *)
                        error "Unknown option: $1"
                        exit 1
                        ;;
                esac
            done
            ;;
        "migrate-apps")
            local apps=()
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --apps)
                        shift
                        while [[ $# -gt 0 && ! "$1" =~ ^-- ]]; do
                            apps+=("$1")
                            shift
                        done
                        ;;
                    *)
                        error "Unknown option: $1"
                        exit 1
                        ;;
                esac
            done
            
            if [[ ${#apps[@]} -eq 0 ]]; then
                error "Please specify apps to migrate with --apps"
                exit 1
            fi
            
            args+=("--apps")
            args+=("${apps[@]}")
            ;;
        *)
            # Pass through other arguments
            args+=("$@")
            ;;
    esac
    
    # Execute the Python script
    log "Executing: $PYTHON_CMD production_migrate.py ${args[*]}"
    
    if $PYTHON_CMD production_migrate.py "${args[@]}"; then
        success "Migration command completed successfully"
        exit 0
    else
        error "Migration command failed"
        exit 1
    fi
}

# Handle script interruption
trap 'error "Script interrupted by user"; exit 1' INT TERM

# Run main function with all arguments
main "$@" 