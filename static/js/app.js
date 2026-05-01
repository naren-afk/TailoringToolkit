// Tailoring Shop Management - Main JavaScript

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize PWA features
    initializePWA();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Initialize data tables
    initializeDataTables();
    
    // Initialize notifications
    initializeNotifications();
    
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
    
    // Initialize auto-save functionality
    initializeAutoSave();
    
    console.log('Tailoring Shop Management App initialized successfully');
}

// PWA Functions
function initializePWA() {
    // Check if app is installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
        console.log('App is running in standalone mode');
        document.body.classList.add('pwa-installed');
    }
    
    // Handle install prompt
    let deferredPrompt;
    
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        showInstallPrompt();
    });
    
    window.addEventListener('appinstalled', (evt) => {
        console.log('App was installed');
        hideInstallPrompt();
        showNotification('App installed successfully!', 'success');
    });
}

function showInstallPrompt() {
    const prompt = document.createElement('div');
    prompt.className = 'pwa-install-prompt show';
    prompt.innerHTML = `
        <div class="d-flex align-items-center justify-content-between">
            <div>
                <strong>Install App</strong>
                <br><small>Add to home screen for quick access</small>
            </div>
            <div class="ms-3">
                <button class="btn btn-sm btn-light me-2" onclick="installApp()">Install</button>
                <button class="btn btn-sm btn-outline-light" onclick="hideInstallPrompt()">×</button>
            </div>
        </div>
    `;
    document.body.appendChild(prompt);
}

function hideInstallPrompt() {
    const prompt = document.querySelector('.pwa-install-prompt');
    if (prompt) {
        prompt.remove();
    }
}

function installApp() {
    if (window.deferredPrompt) {
        window.deferredPrompt.prompt();
        window.deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted the install prompt');
                hideInstallPrompt();
            }
            window.deferredPrompt = null;
        });
    } else {
        // Fallback for browsers that don't support install prompt
        showNotification('To install: Open browser menu → "Add to Home Screen"', 'info');
    }
}

// Form Validation Functions
function initializeFormValidations() {
    // Add custom validation to all forms
    const forms = document.querySelectorAll('form[novalidate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                showFirstError(form);
            }
            form.classList.add('was-validated');
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
    });
}

function validateField(field) {
    const isValid = field.checkValidity();
    field.classList.toggle('is-valid', isValid);
    field.classList.toggle('is-invalid', !isValid);
    
    // Remove existing feedback
    const feedback = field.parentNode.querySelector('.invalid-feedback, .valid-feedback');
    if (feedback) {
        feedback.remove();
    }
    
    // Add new feedback
    if (!isValid) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'invalid-feedback';
        feedbackDiv.textContent = field.validationMessage || 'Please provide a valid value.';
        field.parentNode.appendChild(feedbackDiv);
    }
}

function showFirstError(form) {
    const firstInvalid = form.querySelector(':invalid');
    if (firstInvalid) {
        firstInvalid.focus();
        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Data Table Functions
function initializeDataTables() {
    // Add search functionality to tables
    const tables = document.querySelectorAll('.table');
    
    tables.forEach(table => {
        addTableSearch(table);
        addTableSorting(table);
    });
}

function addTableSearch(table) {
    const searchInput = table.closest('.card').querySelector('input[type="text"]');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
        
        updateTableStats(table);
    });
}

function addTableSorting(table) {
    const headers = table.querySelectorAll('th[data-sortable]');
    
    headers.forEach((header, index) => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(table, index, this.dataset.sortable);
        });
    });
}

function sortTable(table, columnIndex, dataType) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const isAscending = table.dataset.sortOrder !== 'asc';
    table.dataset.sortOrder = isAscending ? 'asc' : 'desc';
    
    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex].textContent.trim();
        const bVal = b.cells[columnIndex].textContent.trim();
        
        let comparison = 0;
        
        switch (dataType) {
            case 'number':
                comparison = parseFloat(aVal) - parseFloat(bVal);
                break;
            case 'date':
                comparison = new Date(aVal) - new Date(bVal);
                break;
            default:
                comparison = aVal.localeCompare(bVal);
        }
        
        return isAscending ? comparison : -comparison;
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

function updateTableStats(table) {
    const visibleRows = table.querySelectorAll('tbody tr[style=""]');
    const totalRows = table.querySelectorAll('tbody tr').length;
    
    const statsElement = table.closest('.card').querySelector('.table-stats');
    if (statsElement) {
        statsElement.textContent = `Showing ${visibleRows.length} of ${totalRows} items`;
    }
}

// Notification Functions
function initializeNotifications() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                fadeOut(alert);
            }
        }, 5000);
    });
}

function showNotification(message, type = 'info', duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 400px;';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (alertDiv.parentNode) {
            fadeOut(alertDiv);
        }
    }, duration);
}

function fadeOut(element) {
    element.style.transition = 'opacity 0.3s ease';
    element.style.opacity = '0';
    
    setTimeout(() => {
        if (element.parentNode) {
            element.remove();
        }
    }, 300);
}

// Keyboard Shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + S: Save (prevent default browser save)
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const saveBtn = document.querySelector('button[type="submit"], .btn-primary');
            if (saveBtn && !saveBtn.disabled) {
                saveBtn.click();
            }
        }
        
        // Ctrl/Cmd + N: New item
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            const newBtn = document.querySelector('.btn[href*="add"], .btn[href*="new"]');
            if (newBtn) {
                window.location.href = newBtn.href;
            }
        }
        
        // Escape: Close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const closeBtn = openModal.querySelector('.btn-close, [data-bs-dismiss="modal"]');
                if (closeBtn) {
                    closeBtn.click();
                }
            }
        }
        
        // Ctrl/Cmd + F: Focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            const searchInput = document.querySelector('input[type="search"], input[placeholder*="search" i]');
            if (searchInput) {
                e.preventDefault();
                searchInput.focus();
            }
        }
    });
}

// Auto-save Functions
function initializeAutoSave() {
    const forms = document.querySelectorAll('form[data-autosave]');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('input', debounce(() => {
                autoSaveForm(form);
            }, 2000));
        });
        
        // Load saved data on page load
        loadAutoSavedData(form);
    });
}

function autoSaveForm(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    const storageKey = `autosave_${form.id || 'form'}`;
    localStorage.setItem(storageKey, JSON.stringify(data));
    
    showNotification('Draft saved automatically', 'info', 2000);
}

function loadAutoSavedData(form) {
    const storageKey = `autosave_${form.id || 'form'}`;
    const savedData = localStorage.getItem(storageKey);
    
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            
            Object.keys(data).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input && !input.value) {
                    input.value = data[key];
                }
            });
            
            showNotification('Draft restored', 'info', 2000);
        } catch (e) {
            console.error('Error loading auto-saved data:', e);
        }
    }
}

function clearAutoSave(form) {
    const storageKey = `autosave_${form.id || 'form'}`;
    localStorage.removeItem(storageKey);
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 0
    }).format(amount);
}

function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    return new Intl.DateTimeFormat('en-IN', { ...defaultOptions, ...options }).format(new Date(date));
}

// Form Helpers
function calculateBalance() {
    const costInput = document.getElementById('stitching_cost');
    const advanceInput = document.getElementById('advance_paid');
    const balanceDisplay = document.getElementById('balance_display');
    
    if (costInput && advanceInput && balanceDisplay) {
        const cost = parseFloat(costInput.value) || 0;
        const advance = parseFloat(advanceInput.value) || 0;
        const balance = Math.max(0, cost - advance);
        
        balanceDisplay.textContent = balance.toFixed(2);
        
        // Update validation
        if (advance > cost) {
            advanceInput.setCustomValidity('Advance cannot exceed total cost');
        } else {
            advanceInput.setCustomValidity('');
        }
    }
}

// Customer search functionality
function initializeCustomerSearch() {
    const customerSelect = document.getElementById('customer_id');
    if (customerSelect) {
        customerSelect.addEventListener('change', function() {
            loadCustomerMeasurements(this.value);
        });
    }
}

function loadCustomerMeasurements(customerId) {
    if (!customerId) return;
    
    // This would typically make an AJAX call to load measurements
    // For now, we'll just show a placeholder
    const measurementsSection = document.getElementById('measurements-preview');
    if (measurementsSection) {
        measurementsSection.style.display = 'block';
        measurementsSection.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">Customer Measurements</h5>
                </div>
                <div class="card-body">
                    <p class="text-muted">Loading customer measurements...</p>
                </div>
            </div>
        `;
    }
}

// Bulk operations
function initializeBulkOperations() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const itemCheckboxes = document.querySelectorAll('.item-checkbox');
    const bulkActionBtn = document.getElementById('bulkActionBtn');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            itemCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionButton();
        });
    }
    
    itemCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateBulkActionButton);
    });
    
    function updateBulkActionButton() {
        const selectedItems = document.querySelectorAll('.item-checkbox:checked');
        if (bulkActionBtn) {
            bulkActionBtn.disabled = selectedItems.length === 0;
            bulkActionBtn.textContent = `Action (${selectedItems.length} selected)`;
        }
    }
}

// Network status handling
function initializeNetworkHandling() {
    function updateNetworkStatus() {
        const isOnline = navigator.onLine;
        const statusIndicator = document.getElementById('network-status');
        
        if (statusIndicator) {
            statusIndicator.className = isOnline ? 'online' : 'offline';
            statusIndicator.textContent = isOnline ? 'Online' : 'Offline';
        }
        
        if (!isOnline) {
            showNotification('You are offline. Some features may not work.', 'warning', 0);
        }
    }
    
    window.addEventListener('online', updateNetworkStatus);
    window.addEventListener('offline', updateNetworkStatus);
    updateNetworkStatus();
}

// Export functions for global use
window.TailoringApp = {
    showNotification,
    formatCurrency,
    formatDate,
    calculateBalance,
    installApp,
    hideInstallPrompt,
    clearAutoSave
};

// Initialize additional features when needed
document.addEventListener('htmx:afterRequest', function(event) {
    // Re-initialize features after HTMX requests
    initializeFormValidations();
    initializeDataTables();
});

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', function() {
        setTimeout(function() {
            const perfData = performance.getEntriesByType('navigation')[0];
            console.log('Page load time:', perfData.loadEventEnd - perfData.fetchStart, 'ms');
        }, 0);
    });
}
