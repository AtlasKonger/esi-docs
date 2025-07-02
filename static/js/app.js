// EVE Industry Tracker - Main JavaScript

// Global application object
const EveIndustryTracker = {
    // Configuration
    config: {
        syncInterval: 300000, // 5 minutes
        apiTimeout: 30000,    // 30 seconds
        toastDuration: 5000   // 5 seconds
    },

    // Initialize the application
    init: function() {
        this.setupEventListeners();
        this.initializeComponents();
        this.startPeriodicSync();
    },

    // Set up global event listeners
    setupEventListeners: function() {
        // Auto-dismiss alerts after 5 seconds
        document.querySelectorAll('.alert').forEach(alert => {
            if (alert.classList.contains('alert-dismissible')) {
                setTimeout(() => {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }, this.config.toastDuration);
            }
        });

        // Global sync button handler
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-action="sync-jobs"]')) {
                e.preventDefault();
                this.syncJobs();
            }
        });

        // Global form validation
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', this.validateForm);
        });

        // Auto-save form data to localStorage
        document.querySelectorAll('input, textarea, select').forEach(input => {
            if (input.name && !input.type.includes('password')) {
                this.setupAutoSave(input);
            }
        });
    },

    // Initialize Bootstrap components
    initializeComponents: function() {
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Initialize popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });

        // Initialize progress bars with animation
        this.animateProgressBars();
    },

    // Sync jobs with EVE API
    syncJobs: function() {
        const syncButtons = document.querySelectorAll('[data-action="sync-jobs"]');
        
        // Disable buttons and show loading state
        syncButtons.forEach(btn => {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
        });

        // Show toast notification
        this.showToast('Syncing jobs with EVE Online...', 'info');

        fetch('/api/sync-jobs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            timeout: this.config.apiTimeout
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.showToast('Jobs synced successfully!', 'success');
                // Refresh page after a short delay
                setTimeout(() => location.reload(), 1000);
            } else {
                throw new Error(data.message || 'Sync failed');
            }
        })
        .catch(error => {
            console.error('Sync error:', error);
            this.showToast('Failed to sync jobs: ' + error.message, 'danger');
        })
        .finally(() => {
            // Reset buttons
            syncButtons.forEach(btn => {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-sync"></i> Sync Jobs';
            });
        });
    },

    // Start periodic job synchronization
    startPeriodicSync: function() {
        if (window.location.pathname !== '/dashboard') return;
        
        setInterval(() => {
            // Only sync if page is visible and user is active
            if (!document.hidden && this.isUserActive()) {
                this.syncJobs();
            }
        }, this.config.syncInterval);
    },

    // Check if user is active (has interacted recently)
    isUserActive: function() {
        return (Date.now() - this.lastActivity) < 60000; // 1 minute
    },

    // Track user activity
    trackActivity: function() {
        this.lastActivity = Date.now();
    },

    // Form validation
    validateForm: function(e) {
        const form = e.target;
        let isValid = true;

        // Clear previous validation messages
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        form.querySelectorAll('.invalid-feedback').forEach(el => el.remove());

        // Validate required fields
        form.querySelectorAll('[required]').forEach(field => {
            if (!field.value.trim()) {
                EveIndustryTracker.showFieldError(field, 'This field is required');
                isValid = false;
            }
        });

        // Validate specific field types
        form.querySelectorAll('input[type="number"]').forEach(field => {
            const value = parseFloat(field.value);
            const min = parseFloat(field.min);
            const max = parseFloat(field.max);

            if (field.value && isNaN(value)) {
                EveIndustryTracker.showFieldError(field, 'Please enter a valid number');
                isValid = false;
            } else if (min !== undefined && value < min) {
                EveIndustryTracker.showFieldError(field, `Value must be at least ${min}`);
                isValid = false;
            } else if (max !== undefined && value > max) {
                EveIndustryTracker.showFieldError(field, `Value must be at most ${max}`);
                isValid = false;
            }
        });

        // Validate dates
        form.querySelectorAll('input[type="date"]').forEach(field => {
            if (field.value) {
                const date = new Date(field.value);
                const today = new Date();
                today.setHours(0, 0, 0, 0);

                if (field.min && date < new Date(field.min)) {
                    EveIndustryTracker.showFieldError(field, 'Date cannot be in the past');
                    isValid = false;
                }
            }
        });

        if (!isValid) {
            e.preventDefault();
            // Scroll to first error
            const firstError = form.querySelector('.is-invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
        }
    },

    // Show field validation error
    showFieldError: function(field, message) {
        field.classList.add('is-invalid');
        
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = message;
        
        field.parentNode.appendChild(feedback);
    },

    // Auto-save form data
    setupAutoSave: function(input) {
        const key = `eve_tracker_${window.location.pathname}_${input.name}`;
        
        // Load saved value
        const savedValue = localStorage.getItem(key);
        if (savedValue && !input.value) {
            input.value = savedValue;
        }

        // Save on change
        input.addEventListener('change', () => {
            if (input.value) {
                localStorage.setItem(key, input.value);
            } else {
                localStorage.removeItem(key);
            }
        });

        // Clear on form submit
        input.form?.addEventListener('submit', () => {
            localStorage.removeItem(key);
        });
    },

    // Show toast notification
    showToast: function(message, type = 'info') {
        // Create toast container if it doesn't exist
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        container.appendChild(toast);

        // Show toast
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: this.config.toastDuration
        });
        bsToast.show();

        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    // Animate progress bars
    animateProgressBars: function() {
        document.querySelectorAll('.progress-bar').forEach(bar => {
            const width = bar.style.width || bar.getAttribute('aria-valuenow') + '%';
            bar.style.width = '0%';
            
            setTimeout(() => {
                bar.style.width = width;
            }, 100);
        });
    },

    // Format numbers with commas
    formatNumber: function(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    // Format EVE time (UTC) to local time
    formatEveTime: function(utcTimeString) {
        const date = new Date(utcTimeString + 'Z'); // Ensure UTC
        return date.toLocaleString();
    },

    // Calculate time remaining
    getTimeRemaining: function(endDate) {
        const now = new Date();
        const end = new Date(endDate);
        const diff = end - now;

        if (diff <= 0) return 'Completed';

        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

        if (days > 0) return `${days}d ${hours}h`;
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    },

    // Filter table rows
    filterTable: function(tableId, filters) {
        const table = document.getElementById(tableId);
        if (!table) return;

        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            let visible = true;

            Object.entries(filters).forEach(([key, value]) => {
                if (value && visible) {
                    const cellValue = row.dataset[key] || '';
                    if (key === 'search') {
                        const searchText = row.textContent.toLowerCase();
                        visible = searchText.includes(value.toLowerCase());
                    } else {
                        visible = cellValue === value;
                    }
                }
            });

            row.style.display = visible ? '' : 'none';
        });

        // Update visible count
        const visibleCount = Array.from(rows).filter(row => row.style.display !== 'none').length;
        const countElement = document.querySelector(`#${tableId} + .table-info .visible-count`);
        if (countElement) {
            countElement.textContent = visibleCount;
        }
    },

    // Debounce function for search inputs
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Initialize activity tracking
    lastActivity: Date.now()
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    EveIndustryTracker.init();
});

// Track user activity
document.addEventListener('mousemove', EveIndustryTracker.trackActivity.bind(EveIndustryTracker));
document.addEventListener('keypress', EveIndustryTracker.trackActivity.bind(EveIndustryTracker));
document.addEventListener('scroll', EveIndustryTracker.trackActivity.bind(EveIndustryTracker));

// Global functions for backward compatibility
window.syncJobs = function() {
    EveIndustryTracker.syncJobs();
};

window.filterTable = function(filters) {
    EveIndustryTracker.filterTable('jobsTable', filters);
};

window.clearFilters = function() {
    document.querySelectorAll('select, input[type="text"]').forEach(input => {
        input.value = '';
    });
    EveIndustryTracker.filterTable('jobsTable', {});
};

// Utility functions
window.formatNumber = EveIndustryTracker.formatNumber;
window.formatEveTime = EveIndustryTracker.formatEveTime;
window.getTimeRemaining = EveIndustryTracker.getTimeRemaining;