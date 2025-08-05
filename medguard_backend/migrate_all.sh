#!/bin/bash

# MedGuard SA Migration Script - Unix/Linux/macOS Shell Script
# This file provides an easy way to run the migration script on Unix-like systems

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

# Function to show help
show_help() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  --dry-run      Preview changes without executing"
    echo "  --backup-only  Only create database backup"
    echo "  --verify-only  Only run verification checks"
    echo "  --help         Show this help message"
    echo
    echo "Examples:"
    echo "  $0"
    echo "  $0 --dry-run"
    echo "  $0 --backup-only"
    echo "  $0 --verify-only"
    echo
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        if ! command -v python &> /dev/null; then
            print_error "ERROR: Python is not installed or not in PATH"
            exit 1
        fi
    fi
    
    # Check if we're in the right directory
    if [ ! -f "manage.py" ]; then
        print_error "ERROR: manage.py not found in current directory"
        print_error "Please run this script from the medguard_backend directory"
        exit 1
    fi
    
    # Check if migration script exists
    if [ ! -f "migrate_all.py" ]; then
        print_error "ERROR: migrate_all.py not found"
        print_error "Please ensure the migration script is in the current directory"
        exit 1
    fi
    
    # Check if script is executable
    if [ ! -x "migrate_all.py" ]; then
        print_warning "Making migration script executable..."
        chmod +x migrate_all.py
    fi
    
    print_success "Prerequisites check passed"
}

# Function to parse arguments
parse_arguments() {
    DRY_RUN=""
    BACKUP_ONLY=""
    VERIFY_ONLY=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN="--dry-run"
                shift
                ;;
            --backup-only)
                BACKUP_ONLY="--backup-only"
                shift
                ;;
            --verify-only)
                VERIFY_ONLY="--verify-only"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Function to run the migration script
run_migration() {
    print_status "Starting MedGuard SA Migration Script..."
    echo
    
    # Determine Python command
    PYTHON_CMD="python3"
    if ! command -v python3 &> /dev/null; then
        PYTHON_CMD="python"
    fi
    
    # Run the migration script
    if $PYTHON_CMD migrate_all.py $DRY_RUN $BACKUP_ONLY $VERIFY_ONLY; then
        echo
        print_success "========================================"
        print_success "  Migration completed successfully"
        print_success "========================================"
        echo
        print_status "Check the following files for details:"
        echo "  - migration_execution.log"
        echo "  - migration_report_*.json"
        echo "  - backups/ (if backup was created)"
        echo
        return 0
    else
        echo
        print_error "========================================"
        print_error "  Migration failed with errors"
        print_error "========================================"
        echo
        print_error "Please check the log files for details:"
        echo "  - migration_execution.log"
        echo "  - migration_report_*.json"
        echo
        return 1
    fi
}

# Main execution
main() {
    echo
    echo "========================================"
    echo "   MedGuard SA Migration Script"
    echo "========================================"
    echo
    
    # Parse command line arguments
    parse_arguments "$@"
    
    # Check prerequisites
    check_prerequisites
    
    # Run migration
    if run_migration; then
        exit 0
    else
        exit 1
    fi
}

# Run main function with all arguments
main "$@" 