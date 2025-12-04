/**
 * MIB Viewer - Main JavaScript Functions
 */

// Global variables
let currentTheme = 'light';
let treeVisualization = null;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Set up global event listeners
    setupGlobalEventListeners();

    // Initialize tooltips
    initializeTooltips();

    // Check for saved theme preference
    loadThemePreference();

    // Initialize performance monitoring
    initializePerformanceMonitoring();
}

/**
 * Set up global event listeners
 */
function setupGlobalEventListeners() {
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);

    // Error handling
    window.addEventListener('error', handleGlobalError);

    // Responsive navigation
    setupResponsiveNavigation();
}

/**
 * Handle keyboard shortcuts
 */
function handleKeyboardShortcuts(event) {
    // Ctrl+K or Cmd+K for search focus
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        focusSearchInput();
    }

    // Escape to clear search or close modals
    if (event.key === 'Escape') {
        clearSearchOrCloseModals();
    }

    // Ctrl+/ to show keyboard shortcuts help
    if ((event.ctrlKey || event.metaKey) && event.key === '/') {
        event.preventDefault();
        showKeyboardShortcuts();
    }
}

/**
 * Focus search input
 */
function focusSearchInput() {
    const searchInput = document.querySelector('input[name="q"], input[type="search"]');
    if (searchInput) {
        searchInput.focus();
        searchInput.select();
    }
}

/**
 * Clear search or close modals
 */
function clearSearchOrCloseModals() {
    // Close any open modals
    const modals = document.querySelectorAll('.modal.show');
    modals.forEach(modal => {
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) {
            bsModal.hide();
        }
    });

    // Clear search if focused
    const activeElement = document.activeElement;
    if (activeElement && (activeElement.type === 'search' || activeElement.name === 'q')) {
        activeElement.value = '';
    }
}

/**
 * Show keyboard shortcuts help
 */
function showKeyboardShortcuts() {
    const shortcuts = [
        { key: 'Ctrl+K', description: 'Focus search' },
        { key: 'Escape', description: 'Clear search / Close modals' },
        { key: 'Ctrl+/', description: 'Show shortcuts' },
        { key: 'Click node', description: 'Expand/collapse' },
        { key: 'Hover node', description: 'Show tooltip' }
    ];

    let modalHTML = `
        <div class="modal fade" id="shortcutsModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Keyboard Shortcuts</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="list-group">
    `;

    shortcuts.forEach(shortcut => {
        modalHTML += `
            <div class="list-group-item">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${shortcut.key}</h6>
                </div>
                <p class="mb-1">${shortcut.description}</p>
            </div>
        `;
    });

    modalHTML += `
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add modal to DOM if not exists
    if (!document.getElementById('shortcutsModal')) {
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('shortcutsModal'));
    modal.show();
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Handle global errors
 */
function handleGlobalError(event) {
    console.error('Global error:', event.error);

    // Show user-friendly error message
    showErrorToast('An unexpected error occurred. Please try again.');

    // In production, you might want to send this to an error tracking service
    if (typeof sendErrorToService === 'function') {
        sendErrorToService(event.error);
    }
}

/**
 * Setup responsive navigation
 */
function setupResponsiveNavigation() {
    // Handle navbar collapse on mobile
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');

    if (navbarToggler && navbarCollapse) {
        // Close navbar when clicking outside
        document.addEventListener('click', function(event) {
            const isClickInside = navbarToggler.contains(event.target) ||
                                navbarCollapse.contains(event.target);

            if (!isClickInside && navbarCollapse.classList.contains('show')) {
                navbarToggler.click();
            }
        });

        // Close navbar when clicking on a nav link
        const navLinks = navbarCollapse.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (navbarCollapse.classList.contains('show')) {
                    navbarToggler.click();
                }
            });
        });
    }
}

/**
 * Load theme preference
 */
function loadThemePreference() {
    const savedTheme = localStorage.getItem('mib-viewer-theme');
    if (savedTheme) {
        currentTheme = savedTheme;
        applyTheme(currentTheme);
    } else {
        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            currentTheme = 'dark';
            applyTheme('dark');
        }
    }
}

/**
 * Apply theme
 */
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    currentTheme = theme;
}

/**
 * Toggle theme
 */
function toggleTheme() {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);
    localStorage.setItem('mib-viewer-theme', newTheme);
}

/**
 * Show error toast
 */
function showErrorToast(message) {
    showToast(message, 'danger');
}

/**
 * Show success toast
 */
function showSuccessToast(message) {
    showToast(message, 'success');
}

/**
 * Show info toast
 */
function showInfoToast(message) {
    showToast(message, 'info');
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '1050';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);

    // Show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    toast.show();

    // Remove from DOM when hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

/**
 * Format bytes to human readable format
 */
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format date to human readable format
 */
function formatDate(dateString) {
    if (!dateString) return 'Unknown';

    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
        return 'Today';
    } else if (diffDays === 1) {
        return 'Yesterday';
    } else if (diffDays < 7) {
        return diffDays + ' days ago';
    } else if (diffDays < 30) {
        return Math.floor(diffDays / 7) + ' weeks ago';
    } else if (diffDays < 365) {
        return Math.floor(diffDays / 30) + ' months ago';
    } else {
        return Math.floor(diffDays / 365) + ' years ago';
    }
}

/**
 * Debounce function
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

/**
 * Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Initialize performance monitoring
 */
function initializePerformanceMonitoring() {
    // Monitor page load performance
    if ('performance' in window) {
        window.addEventListener('load', function() {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                if (perfData) {
                    console.log('Page Load Performance:', {
                        domComplete: perfData.domComplete,
                        loadEventEnd: perfData.loadEventEnd,
                        totalTime: perfData.loadEventEnd - perfData.loadEventStart
                    });
                }
            }, 0);
        });
    }
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        return new Promise((resolve, reject) => {
            try {
                document.execCommand('copy');
                resolve();
            } catch (err) {
                reject(err);
            } finally {
                textArea.remove();
            }
        });
    }
}

/**
 * Show copy confirmation
 */
function showCopyConfirmation(elementId, originalText) {
    const element = document.getElementById(elementId);
    if (element) {
        const originalHTML = element.innerHTML;
        element.innerHTML = '<i class="fas fa-check text-success"></i> Copied!';

        setTimeout(() => {
            element.innerHTML = originalHTML;
        }, 2000);
    }
}

/**
 * Export data to file
 */
function exportToFile(data, filename, type = 'application/json') {
    const blob = new Blob([data], { type: type });
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;

    document.body.appendChild(a);
    a.click();

    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

/**
 * Check if element is in viewport
 */
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Scroll element into view
 */
function scrollIntoView(element, options = {}) {
    if (element && !isInViewport(element)) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            ...options
        });
    }
}

// Export functions for use in other scripts
window.MibViewer = {
    showToast,
    showErrorToast,
    showSuccessToast,
    showInfoToast,
    formatBytes,
    formatDate,
    debounce,
    throttle,
    copyToClipboard,
    showCopyConfirmation,
    exportToFile,
    toggleTheme,
    focusSearchInput,
    showKeyboardShortcuts
};