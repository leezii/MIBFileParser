/**
 * Desktop API Bridge for MIB Parser
 *
 * Provides JavaScript interface to PyWebView desktop features.
 * Only active when running in desktop mode (window.pywebview exists).
 */

(function(window) {
    'use strict';

    /**
     * Check if running in desktop mode
     */
    function isDesktopMode() {
        return typeof window.pywebview !== 'undefined' && window.pywebview !== null;
    }

    /**
     * Desktop API wrapper
     */
    const DesktopAPI = {
        /**
         * Check if desktop mode is active
         */
        isAvailable: isDesktopMode(),

        /**
         * Get application information
         * @returns {Promise<Object>} App info object
         */
        getAppInfo: function() {
            if (!this.isAvailable) {
                return Promise.resolve({
                    desktop_mode: false,
                    platform: 'web'
                });
            }
            return window.pywebview.api.get_app_info();
        },

        /**
         * Open native file dialog for selecting files
         * @param {boolean} multiple - Allow multiple file selection
         * @returns {Promise<Array<string>>} Array of file paths
         */
        selectFiles: function(multiple = true) {
            if (!this.isAvailable) {
                return Promise.reject('Desktop mode not available');
            }
            return window.pywebview.api.select_file();
        },

        /**
         * Show system notification
         * @param {string} title - Notification title
         * @param {string} message - Notification message
         * @returns {Promise<void>}
         */
        showNotification: function(title, message) {
            if (!this.isAvailable) {
                console.log('Notification (desktop mode not available):', title, '-', message);
                return Promise.resolve();
            }
            return window.pywebview.api.show_notification(title, message);
        }
    };

    // Export to window object
    window.DesktopAPI = DesktopAPI;

    // Log desktop mode status
    if (DesktopAPI.isAvailable) {
        console.log('✓ Desktop mode active - PyWebView API available');

        // Get and log app info
        DesktopAPI.getAppInfo().then(function(info) {
            console.log('App Info:', info);
            // Store app info for later use
            window.mibParserAppInfo = info;
        }).catch(function(err) {
            console.error('Failed to get app info:', err);
        });
    } else {
        console.log('ℹ Running in browser mode');
    }

})(window);

/**
 * Desktop file upload helper
 *
 * Enhances file upload functionality in desktop mode
 */
(function(window) {
    'use strict';

    /**
     * Setup desktop file upload for an upload area element
     * @param {jQuery|string} selector - Upload area selector or element
     * @param {Function} onFilesSelected - Callback function(files) when files are selected
     */
    function setupDesktopUpload(selector, onFilesSelected) {
        // Wait for DOM to be ready if needed
        if (typeof jQuery === 'undefined') {
            console.error('Desktop upload requires jQuery');
            return;
        }

        const $uploadArea = typeof selector === 'string' ? $(selector) : selector;

        if ($uploadArea.length === 0) {
            console.warn('Upload area element not found');
            return;
        }

        // Only setup if in desktop mode
        if (!window.DesktopAPI.isAvailable) {
            console.log('Desktop upload not available (browser mode)');
            return;
        }

        console.log('Setting up desktop file upload');

        // Override click handler to use native dialog
        $uploadArea.on('click.desktop', function(e) {
            e.preventDefault();
            e.stopPropagation();

            // Show native file dialog
            window.DesktopAPI.selectFiles(true).then(function(filePaths) {
                if (filePaths && filePaths.length > 0) {
                    console.log('Selected files:', filePaths);

                    // Convert file paths to File objects
                    // Note: This requires a fetch to get the file content
                    const filePromises = filePaths.map(function(filePath) {
                        return fetch('/api/desktop/file-info?path=' + encodeURIComponent(filePath))
                            .then(function(response) {
                                return response.json();
                            })
                            .then(function(data) {
                                // Create a File-like object
                                // Note: Browser security prevents direct file path access
                                // So we need to work with what the browser provides
                                return {
                                    name: data.name,
                                    path: data.path,
                                    size: data.size,
                                    // We'll need a custom upload method for this
                                    isDesktopFile: true
                                };
                            })
                            .catch(function(err) {
                                console.error('Error getting file info:', err);
                                return null;
                            });
                    });

                    // Wait for all file info to be loaded
                    Promise.all(filePromises).then(function(files) {
                        // Filter out failed files
                        const validFiles = files.filter(function(f) { return f !== null; });

                        if (validFiles.length > 0 && typeof onFilesSelected === 'function') {
                            onFilesSelected(validFiles);
                        }
                    });
                }
            }).catch(function(err) {
                console.error('File dialog error:', err);
            });
        });

        // Store original click handler for cleanup
        $uploadArea.data('desktop-upload-setup', true);
    }

    // Export to window object
    window.setupDesktopUpload = setupDesktopUpload;

})(window);
