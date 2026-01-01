# Specification: Desktop Application Wrapper

**Change ID**: `add-desktop-wrapper`
**Capability**: `desktop-app`
**Version**: 1.0.0

---

## ADDED Requirements

### Requirement: Desktop Application Launch

The system MUST provide a standalone desktop application launcher that starts the Flask web application in a native desktop window.

#### Scenario: User launches desktop application on Windows

**Given** the user has installed the MIB Parser desktop application
**When** the user double-clicks `MIBParser.exe`
**Then** a native desktop window opens
**And** the window displays the Flask web application
**And** the application window has the title "MIB Parser"
**And** the window size is 1400x900 pixels
**And** the window is resizable with minimum size 1000x600

#### Scenario: User launches desktop application on macOS

**Given** the user has installed the MIB Parser desktop application
**When** the user double-clicks `MIBParser.app` in Finder or Launchpad
**Then** a native macOS window opens
**And** the window displays the Flask web application
**And** the application icon appears in the Dock
**And** the window meets the same size requirements as Windows

#### Scenario: User launches desktop application on Linux

**Given** the user has installed the MIB Parser desktop application
**And** the user has installed WebKitGTK libraries
**When** the user launches the application from the desktop menu or terminal
**Then** a native window opens
**And** the window displays the Flask web application
**And** the application appears in the system application menu

---

### Requirement: Flask Background Thread Execution

The system MUST run the Flask application in a background daemon thread while PyWebView runs in the main thread.

#### Scenario: Flask starts before WebView window

**Given** the desktop launcher is started
**When** the launcher creates the Flask background thread
**Then** Flask starts on `127.0.0.1:5000`
**And** the launcher waits up to 2 seconds for Flask to initialize
**And** the launcher creates the WebView window only after Flask is ready
**And** the WebView window loads `http://127.0.0.1:5000`

#### Scenario: Flask daemon thread terminates on application exit

**Given** the desktop application is running
**When** the user closes the application window
**Then** the main thread exits
**And** the Flask daemon thread automatically terminates
**And** no zombie processes remain

---

### Requirement: Native File Dialog Integration

The system MUST provide native file picker dialogs for MIB file uploads when running in desktop mode.

#### Scenario: User uploads MIB file using native file dialog

**Given** the user is viewing the MIB upload page in the desktop application
**When** the user clicks the "Select Files" button
**Then** the native file dialog opens (not browser file input)
**And** the dialog filters for `.mib`, `.my`, and `.txt` files
**And** the user can select one or multiple files
**When** the user selects files and confirms
**Then** the file paths are returned to the web application
**And** the files are uploaded to the Flask API via HTTP POST
**And** the files are processed normally by Flask

#### Scenario: File dialog is cancelled by user

**Given** the native file dialog is open
**When** the user cancels the dialog
**Then** no files are selected
**And** the web application receives an empty result
**And** no upload occurs

---

### Requirement: Application Packaging

The system MUST be packageable as a single executable for each supported platform.

#### Scenario: Windows executable packaging

**Given** the PyInstaller build configuration is set up
**When** the developer runs `pyinstaller desktop/build.spec --onefile --windowed`
**Then** a single `MIBParser.exe` file is created in `dist/`
**And** the executable includes the Python runtime
**And** the executable includes all Flask dependencies
**And** the executable includes storage/, static/, and templates/ directories
**And** the executable size is less than 100 MB
**And** the executable displays the application icon

#### Scenario: macOS application bundle packaging

**Given** the PyInstaller build configuration is set up for macOS
**When** the developer runs `pyinstaller desktop/build.spec`
**Then** an `MIBParser.app` bundle is created in `dist/`
**And** the app bundle contains the executable
**And** the app bundle includes the application icon in `.icns` format
**And** the app bundle has proper `Info.plist` metadata
**And** the app can be double-clicked to launch

#### Scenario: Linux binary packaging

**Given** the PyInstaller build configuration is set up for Linux
**When** the developer runs `pyinstaller desktop/build.spec --onefile`
**Then** a single `mib-parser` executable is created in `dist/`
**And** the executable has execute permissions
**And** the executable can be run from terminal
**And** a `.desktop` file is created for application menu integration

---

### Requirement: Application Icons

The system MUST display professional application icons on all platforms.

#### Scenario: Application icon on Windows

**Given** the desktop application is built for Windows
**When** the user views the executable in File Explorer
**Then** the executable displays the application icon
**And** when the application runs, the icon appears in the taskbar
**And** the icon appears in the window title bar
**And** the icon is in `.ico` format with multiple resolutions (16x16 to 256x256)

#### Scenario: Application icon on macOS

**Given** the desktop application is built for macOS
**When** the user views the app bundle in Finder
**Then** the app displays the application icon
**And** when the application runs, the icon appears in the Dock
**And** the icon bounces during launch
**And** the icon is in `.icns` format with multiple resolutions

#### Scenario: Application icon on Linux

**Given** the desktop application is installed on Linux
**When** the user views the application in the file manager
**Then** the executable displays the application icon
**And** the icon appears in the application launcher/menu
**And** the icon is in `.png` format with minimum size of 512x512

---

### Requirement: Desktop Feature API

The system MUST provide a JavaScript API for desktop-specific features via PyWebView.

#### Scenario: Frontend retrieves application version

**Given** the web application is running in desktop mode
**When** the JavaScript calls `pywebview.api.get_app_info()`
**Then** the system returns an object with:
  - `version`: Application version string (e.g., "1.0.0")
  - `platform`: Operating system ("windows", "macos", "linux")
  - `desktop_mode`: Always `true` for desktop app

#### Scenario: Frontend displays system notification

**Given** the web application is running in desktop mode
**When** the JavaScript calls `pywebview.api.show_notification(title, message)`
**Then** the operating system displays a notification
**And** the notification shows the provided title and message
**And** the notification uses the application icon

#### Scenario: Frontend checks if running in desktop mode

**Given** the web application is loaded
**When** the JavaScript checks if `window.pywebview` is defined
**Then** `window.pywebview` is available in desktop mode
**And** `window.pywebview` is undefined in browser mode
**And** the application can adapt behavior accordingly

---

### Requirement: Window State Management

The system MUST provide sensible default window behavior and allow user customization.

#### Scenario: Window resizing

**Given** the desktop application window is open
**When** the user resizes the window
**Then** the window resizes smoothly
**And** the web content reflows responsively
**And** the window cannot be resized below 1000x600 pixels

#### Scenario: Window fullscreen toggle

**Given** the desktop application window is open
**When** the user toggles fullscreen (F11 or platform-specific shortcut)
**Then** the window enters fullscreen mode
**And** the web content fills the entire screen
**When** the user exits fullscreen
**Then** the window returns to previous size

#### Scenario: Window controls (minimize, maximize, close)

**Given** the desktop application is running
**When** the user clicks the minimize button
**Then** the window minimizes to the taskbar/dock
**When** the user clicks the maximize button
**Then** the window maximizes to fill the screen
**When** the user clicks the close button
**Then** the application exits cleanly

---

### Requirement: Performance Constraints

The desktop application MUST meet reasonable performance targets.

#### Scenario: Application startup time

**Given** the user launches the desktop application
**When** the application window opens
**Then** the time from launch to window fully loaded is less than 5 seconds
**And** this is measured on a modern laptop (SSD, 8GB RAM)

#### Scenario: Memory usage

**Given** the desktop application is running
**And** the user has loaded a large MIB tree (1000+ nodes)
**When** memory usage is measured
**Then** total memory usage is less than 200 MB overhead
**And** overhead is measured relative to browser-based usage

#### Scenario: Package size

**Given** the desktop application is built
**When** the package size is measured
**Then** the Windows executable is less than 100 MB
**And** the macOS app bundle is less than 100 MB
**And** the Linux executable is less than 100 MB

---

### Requirement: Backward Compatibility

The desktop application wrapper MUST NOT break existing web application functionality.

#### Scenario: All web features work in desktop mode

**Given** the desktop application is running
**When** the user interacts with any web feature
**Then** all features that work in browser also work in desktop app:
  - MIB file upload and parsing
  - Tree visualization and navigation
  - OID search and lookup
  - Device management
  - Annotations
  - Fullscreen tree view
  - Statistics and analytics

#### Scenario: No Flask code changes required

**Given** the existing Flask web application code
**When** the desktop launcher is created
**Then** zero lines of Flask code need to be modified
**And** the Flask application works identically in both modes

---

### Requirement: Development and Build Tools

The system MUST provide tooling for building the desktop application.

#### Scenario: Automated build script

**Given** the developer wants to build the desktop application
**When** the developer runs `python desktop/build.py`
**Then** the script detects the current platform
**And** the script cleans previous build artifacts
**And** the script runs PyInstaller with correct configuration
**And** the script performs platform-specific post-processing
**And** the script validates the generated executable

#### Scenario: Development mode testing

**Given** the developer is working on the desktop launcher
**When** the developer runs `python desktop/app.py`
**Then** the application launches in development mode
**And** the Flask app runs with debug=False (for stability)
**And** console output shows startup and shutdown messages

---

## MODIFIED Requirements

*None - This change adds new desktop capability without modifying existing functionality.*

---

## REMOVED Requirements

*None - This is a purely additive change.*

---

## Cross-References

### Related Capabilities
- **flask-api-tests**: Desktop app must support all existing Flask API endpoints
- **web-interface**: Desktop app displays the same web interface

### Dependencies
- Requires Python 3.9+ runtime (packaged with app)
- Requires PyWebView 5.0+
- Requires PyInstaller 6.0+

### Notes
- Desktop mode can be detected by checking if `window.pywebview` is defined
- Future enhancements could include system tray, auto-updates, single-instance enforcement
- Code signing and notarization are optional for development but recommended for distribution
