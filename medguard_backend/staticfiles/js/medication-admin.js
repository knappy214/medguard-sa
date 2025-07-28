/**
 * MedGuard SA - Medication Admin JavaScript
 * Enhanced functionality for medication management interface
 */

(function() {
    'use strict';

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeMedicationAdmin();
    });

    function initializeMedicationAdmin() {
        // Initialize bulk actions
        initializeBulkActions();
        
        // Initialize real-time updates
        initializeRealTimeUpdates();
        
        // Initialize search and filters
        initializeSearchAndFilters();
        
        // Initialize status indicators
        initializeStatusIndicators();
        
        // Initialize accessibility features
        initializeAccessibility();
    }

    /**
     * Bulk Actions Functionality
     */
    function initializeBulkActions() {
        const bulkActionForm = document.querySelector('.bulk-actions-form');
        if (!bulkActionForm) return;

        const selectAllCheckbox = document.querySelector('.select-all-checkbox');
        const itemCheckboxes = document.querySelectorAll('.item-checkbox');
        const bulkActionSelect = document.querySelector('.bulk-action-select');
        const bulkActionButton = document.querySelector('.bulk-action-button');

        // Select all functionality
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                itemCheckboxes.forEach(checkbox => {
                    checkbox.checked = this.checked;
                });
                updateBulkActionButton();
            });
        }

        // Individual checkbox functionality
        itemCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                updateSelectAllCheckbox();
                updateBulkActionButton();
            });
        });

        // Bulk action button functionality
        if (bulkActionButton) {
            bulkActionButton.addEventListener('click', function(e) {
                e.preventDefault();
                const selectedAction = bulkActionSelect.value;
                const selectedItems = getSelectedItems();
                
                if (selectedItems.length === 0) {
                    showNotification('Please select at least one item', 'warning');
                    return;
                }

                if (selectedAction === '') {
                    showNotification('Please select an action', 'warning');
                    return;
                }

                executeBulkAction(selectedAction, selectedItems);
            });
        }

        function updateSelectAllCheckbox() {
            if (!selectAllCheckbox) return;
            
            const checkedBoxes = document.querySelectorAll('.item-checkbox:checked');
            const totalBoxes = itemCheckboxes.length;
            
            selectAllCheckbox.checked = checkedBoxes.length === totalBoxes;
            selectAllCheckbox.indeterminate = checkedBoxes.length > 0 && checkedBoxes.length < totalBoxes;
        }

        function updateBulkActionButton() {
            if (!bulkActionButton) return;
            
            const selectedItems = getSelectedItems();
            bulkActionButton.disabled = selectedItems.length === 0;
        }

        function getSelectedItems() {
            const selectedCheckboxes = document.querySelectorAll('.item-checkbox:checked');
            return Array.from(selectedCheckboxes).map(checkbox => checkbox.value);
        }

        function executeBulkAction(action, items) {
            const csrfToken = getCSRFToken();
            
            fetch('/admin/medications/bulk-action/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    action: action,
                    items: items
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Bulk action error:', error);
                showNotification('An error occurred while processing the bulk action', 'error');
            });
        }
    }

    /**
     * Real-time Updates
     */
    function initializeRealTimeUpdates() {
        // Update stock status every 30 seconds
        setInterval(updateStockStatus, 30000);
        
        // Update expiration warnings every 5 minutes
        setInterval(updateExpirationWarnings, 300000);
    }

    function updateStockStatus() {
        const stockElements = document.querySelectorAll('.stock-status');
        
        stockElements.forEach(element => {
            const medicationId = element.dataset.medicationId;
            if (!medicationId) return;

            fetch(`/admin/medications/${medicationId}/stock-status/`)
                .then(response => response.json())
                .then(data => {
                    element.innerHTML = data.status_html;
                    element.className = `stock-status ${data.status_class}`;
                })
                .catch(error => {
                    console.error('Stock status update error:', error);
                });
        });
    }

    function updateExpirationWarnings() {
        fetch('/admin/medications/expiration-warnings/')
            .then(response => response.json())
            .then(data => {
                if (data.warnings.length > 0) {
                    showExpirationWarnings(data.warnings);
                }
            })
            .catch(error => {
                console.error('Expiration warnings update error:', error);
            });
    }

    function showExpirationWarnings(warnings) {
        const warningContainer = document.getElementById('expiration-warnings');
        if (!warningContainer) return;

        warningContainer.innerHTML = '';
        
        warnings.forEach(warning => {
            const warningElement = document.createElement('div');
            warningElement.className = 'expiration-warning';
            warningElement.innerHTML = `
                <span class="warning-icon">⚠️</span>
                <span class="warning-text">${warning.message}</span>
                <a href="${warning.url}" class="warning-link">View Details</a>
            `;
            warningContainer.appendChild(warningElement);
        });

        warningContainer.style.display = 'block';
    }

    /**
     * Search and Filters
     */
    function initializeSearchAndFilters() {
        const searchInput = document.querySelector('.medication-search');
        const filterSelects = document.querySelectorAll('.medication-filter');
        
        // Debounced search
        let searchTimeout;
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    performSearch(this.value);
                }, 300);
            });
        }

        // Filter changes
        filterSelects.forEach(select => {
            select.addEventListener('change', function() {
                applyFilters();
            });
        });
    }

    function performSearch(query) {
        const currentUrl = new URL(window.location);
        currentUrl.searchParams.set('q', query);
        window.location.href = currentUrl.toString();
    }

    function applyFilters() {
        const currentUrl = new URL(window.location);
        const filterSelects = document.querySelectorAll('.medication-filter');
        
        filterSelects.forEach(select => {
            if (select.value) {
                currentUrl.searchParams.set(select.name, select.value);
            } else {
                currentUrl.searchParams.delete(select.name);
            }
        });

        window.location.href = currentUrl.toString();
    }

    /**
     * Status Indicators
     */
    function initializeStatusIndicators() {
        const statusElements = document.querySelectorAll('.status-indicator');
        
        statusElements.forEach(element => {
            element.addEventListener('click', function() {
                const tooltip = this.getAttribute('data-tooltip');
                if (tooltip) {
                    showTooltip(this, tooltip);
                }
            });
        });
    }

    function showTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = text;
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
        
        setTimeout(() => {
            tooltip.remove();
        }, 3000);
    }

    /**
     * Accessibility Features
     */
    function initializeAccessibility() {
        // Keyboard navigation for tables
        const tables = document.querySelectorAll('.medication-table');
        
        tables.forEach(table => {
            const rows = table.querySelectorAll('tr[data-id]');
            
            rows.forEach(row => {
                row.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        const link = this.querySelector('a');
                        if (link) {
                            link.click();
                        }
                    }
                });
                
                row.setAttribute('tabindex', '0');
                row.setAttribute('role', 'button');
            });
        });

        // Screen reader announcements
        const announcements = document.querySelectorAll('[data-announce]');
        
        announcements.forEach(element => {
            element.addEventListener('change', function() {
                announceToScreenReader(this.getAttribute('data-announce'));
            });
        });
    }

    function announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            announcement.remove();
        }, 1000);
    }

    /**
     * Utility Functions
     */
    function getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    // Export functions for global access
    window.MedicationAdmin = {
        showNotification,
        announceToScreenReader,
        updateStockStatus,
        updateExpirationWarnings
    };

})(); 