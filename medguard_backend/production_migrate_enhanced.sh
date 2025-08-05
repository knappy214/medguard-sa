#!/bin/bash
"""
Production Migration Script for MedGuard SA - Enhanced Shell Wrapper

This script provides easy-to-use commands for production deployment with advanced safety features.
It wraps the Python migration script with additional safety checks, monitoring, and rollback capabilities.

Usage:
    ./production_migrate_enhanced.sh [command] [options]

Commands:
    check-migrations    - Check for pending migrations without applying them
    migrate             - Run all migrations safely
    migrate-apps        - Run migrations for specific apps with detailed logging
    collectstatic       - Collect static files
    deploy-check        - Run deployment validation
    full-deploy         - Run complete deployment sequence
    backup              - Create database backup before migration
    verify-data         - Verify critical data integrity
    zero-downtime       - Execute zero-downtime migration strategy
    monitor-migration   - Set up monitoring for migration performance
    rollback            - Rollback to previous migration (if backup exists)
    help                - Show this help message

Examples:
    ./production_migrate_enhanced.sh check-migrations
    ./production_migrate_enhanced.sh migrate --run-syncdb
    ./production_migrate_enhanced.sh migrate-apps --apps medications users
    ./production_migrate_enhanced.sh full-deploy
    ./production_migrate_enhanced.sh verify-data
    ./production_migrate_enhanced.sh zero-downtime
"""

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
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

# Check for required system tools
check_system_tools() {
    local tools=("pg_dump" "psql" "psutil")
    local missing_tools=()
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        warning "Missing system tools: ${missing_tools[*]}"
        warning "Some features may not work properly"
    fi
}

# Show help
show_help() {
    cat << EOF
Production Migration Script for MedGuard SA - Enhanced Version

Usage: $0 [command] [options]

Commands:
    check-migrations    - Check for pending migrations without applying them
    migrate             - Run all migrations safely
    migrate-apps        - Run migrations for specific apps with detailed logging
    collectstatic       - Collect static files
    deploy-check        - Run deployment validation
    full-deploy         - Run complete deployment sequence
    backup              - Create database backup before migration
    verify-data         - Verify critical data integrity
    zero-downtime       - Execute zero-downtime migration strategy
    monitor-migration   - Set up monitoring for migration performance
    rollback            - Rollback to previous migration (if backup exists)
    help                - Show this help message

Options:
    --run-syncdb        - Run syncdb for initial deployment (with migrate command)
    --apps APP1 APP2    - Specific apps to migrate (with migrate-apps command)
    --no-backup         - Skip database backup before migration
    --monitor           - Enable performance monitoring (with any command)

Examples:
    $0 check-migrations
    $0 migrate --run-syncdb
    $0 migrate-apps --apps medications users
    $0 full-deploy
    $0 backup
    $0 verify-data
    $0 zero-downtime

Advanced Features:
    - Automatic database backups with compression
    - Real-time performance monitoring
    - Data integrity verification
    - Zero-downtime migration strategies
    - Automatic rollback script generation
    - Comprehensive logging and reporting

Environment Variables:
    DJANGO_SETTINGS_MODULE - Django settings module (default: medguard_backend.settings.production)
    DB_NAME                - Database name
    DB_USER                - Database user
    DB_PASSWORD            - Database password
    DB_HOST                - Database host (default: localhost)
    DB_PORT                - Database port (default: 5432)

EOF
}

# Create enhanced backup with monitoring
create_enhanced_backup() {
    info "Creating enhanced database backup..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="backups/medguard_backup_${timestamp}.sql"
    
    # Create backup directory if it doesn't exist
    mkdir -p backups
    
    # Get database settings from environment
    local db_host="${DB_HOST:-localhost}"
    local db_port="${DB_PORT:-5432}"
    local db_name="${DB_NAME:-medguard_sa}"
    local db_user="${DB_USER:-medguard_user}"
    
    # Create compressed backup
    log "Creating compressed PostgreSQL backup..."
    
    if PGPASSWORD="$DB_PASSWORD" pg_dump -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" \
        --format=custom --compress=9 --verbose > "$backup_file"; then
        
        local backup_size=$(du -h "$backup_file" | cut -f1)
        success "Backup created successfully: $backup_file (Size: $backup_size)"
        
        # Create backup metadata
        cat > "${backup_file}.json" << EOF
{
  "timestamp": "$timestamp",
  "backup_file": "$backup_file",
  "database": "$db_name",
  "size_bytes": $(stat -c%s "$backup_file"),
  "compression": "custom",
  "created_by": "production_migrate_enhanced.sh"
}
EOF
        
        return 0
    else
        error "Backup creation failed"
        return 1
    fi
}

# Verify data integrity
verify_data_integrity() {
    info "Verifying data integrity..."
    
    # Run the Python verification command
    if $PYTHON_CMD production_migrate.py verify-data; then
        success "Data integrity verification completed"
        return 0
    else
        error "Data integrity verification failed"
        return 1
    fi
}

# Execute zero-downtime migration
execute_zero_downtime() {
    info "Executing zero-downtime migration strategy..."
    
    # Run the Python zero-downtime command
    if $PYTHON_CMD production_migrate.py zero-downtime; then
        success "Zero-downtime migration completed successfully"
        return 0
    else
        error "Zero-downtime migration failed"
        return 1
    fi
}

# Monitor migration performance
monitor_migration() {
    info "Setting up migration performance monitoring..."
    
    # Create monitoring directory
    mkdir -p migration_monitoring
    
    # Start monitoring in background
    local monitor_pid=""
    (
        while true; do
            local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
            local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
            local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
            local disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
            
            echo "$timestamp,CPU:${cpu_usage}%,MEM:${memory_usage}%,DISK:${disk_usage}%" >> migration_monitoring/performance.log
            
            sleep 5
        done
    ) &
    monitor_pid=$!
    
    echo "$monitor_pid" > migration_monitoring/monitor.pid
    success "Performance monitoring started (PID: $monitor_pid)"
    
    return $monitor_pid
}

# Stop monitoring
stop_monitoring() {
    if [[ -f migration_monitoring/monitor.pid ]]; then
        local monitor_pid=$(cat migration_monitoring/monitor.pid)
        if kill -0 "$monitor_pid" 2>/dev/null; then
            kill "$monitor_pid"
            success "Performance monitoring stopped"
        fi
        rm -f migration_monitoring/monitor.pid
    fi
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
    
    log "Starting enhanced production migration script..."
    
    # Pre-flight checks
    check_python
    check_venv
    check_django
    check_manage_py
    check_environment
    check_system_tools
    
    # Build command arguments
    local args=("$command")
    local enable_monitoring=false
    
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
                    --monitor)
                        enable_monitoring=true
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
                    --monitor)
                        enable_monitoring=true
                        shift
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
        "backup")
            create_enhanced_backup
            exit $?
            ;;
        "verify-data")
            verify_data_integrity
            exit $?
            ;;
        "zero-downtime")
            execute_zero_downtime
            exit $?
            ;;
        "monitor-migration")
            monitor_migration
            exit $?
            ;;
        *)
            # Pass through other arguments
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --monitor)
                        enable_monitoring=true
                        shift
                        ;;
                    *)
                        args+=("$1")
                        shift
                        ;;
                esac
            done
            ;;
    esac
    
    # Start monitoring if requested
    if [[ "$enable_monitoring" == true ]]; then
        monitor_migration
        local monitor_pid=$?
        trap 'stop_monitoring' EXIT
    fi
    
    # Execute the Python script
    log "Executing: $PYTHON_CMD production_migrate.py ${args[*]}"
    
    if $PYTHON_CMD production_migrate.py "${args[@]}"; then
        success "Migration command completed successfully"
        
        # Stop monitoring if it was started
        if [[ "$enable_monitoring" == true ]]; then
            stop_monitoring
        fi
        
        exit 0
    else
        error "Migration command failed"
        
        # Stop monitoring if it was started
        if [[ "$enable_monitoring" == true ]]; then
            stop_monitoring
        fi
        
        exit 1
    fi
}

# Handle script interruption
trap 'error "Script interrupted by user"; stop_monitoring; exit 1' INT TERM

# Run main function with all arguments
main "$@" 