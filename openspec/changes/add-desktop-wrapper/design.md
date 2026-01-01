# Design: Desktop Application Wrapper

## Overview
This document describes the technical design for wrapping the Flask-based MIB Parser as a desktop application using PyWebView.

## Architecture Decisions

### 1. Threading Model

**Decision**: Run Flask in a background daemon thread, PyWebView in main thread

**Rationale**:
- PyWebView must run in the main thread (platform requirement)
- Flask can run in a background thread without issues
- Daemon thread ensures clean exit when main thread exits

**Implementation**:
```python
import threading
import webview
from flask_app import create_app

def start_flask(host='127.0.0.1', port=5000):
    app = create_app()
    app.run(host=host, port=port, debug=False, use_reloader=False)

flask_thread = threading.Thread(target=start_flask, daemon=True)
flask_thread.start()
```

**Trade-offs**:
- ✅ Simple implementation
- ✅ Clean exit handling
- ⚠️ Daemon thread cannot create child threads (not an issue for Flask)
- ⚠️ Need to ensure Flask starts before WebView opens (solved with sleep/event)

### 2. Port Management

**Decision**: Use fixed localhost port (5000) for desktop mode

**Rationale**:
- Desktop app is single-user, single-instance
- No port conflict risk (only one instance runs)
- Simplifies launcher code
- Matches existing Flask configuration

**Alternative considered**: Dynamic port allocation
- Rejected: Adds complexity without benefit
- Single-instance desktop app doesn't need multiple ports

### 3. Packaging Strategy

**Decision**: Use PyInstaller with `--onefile` mode

**Rationale**:
- Single executable is easier for users to manage
- No installation directory concerns
- Simpler distribution

**Trade-offs**:
- ✅ User-friendly (single file)
- ✅ Simpler distribution
- ⚠️ Slightly slower startup (unzipping to temp)
- ⚠️ Cannot share resources between instances (not needed)

**Alternative considered**: `--onedir` mode
- Rejected: Multiple files confuse non-technical users

### 4. Asset Handling

**Decision**: Bundle all assets (storage, static files) within executable

**Rationale**:
- True standalone application
- No external file dependencies
- User data stored in user home directory

**Implementation**:
```python
# PyInstaller spec
datas=[
    ('../storage', 'storage'),  # Include storage directory
    ('../src/flask_app/static', 'static'),
    ('../src/flask_app/templates', 'templates'),
]
```

**User Data Location**:
- Windows: `%APPDATA%/MIBParser/storage/`
- macOS: `~/Library/Application Support/MIBParser/storage/`
- Linux: `~/.config/mibparser/storage/`

### 5. Window Management

**Decision**: Use PyWebView's default window chrome

**Rationale**:
- Native look and feel on each platform
- Familiar to users
- Less maintenance burden
- PyWebView handles platform differences

**Window Configuration**:
```python
window = webview.create_window(
    title='MIB Parser',
    url='http://127.0.0.1:5000',
    width=1400,
    height=900,
    min_size=(1000, 600),
    resizable=True,
    fullscreen=False,
)
```

**Alternative considered**: Custom frameless window
- Rejected: More complex, less familiar to users, platform-specific issues

## Component Design

### 1. Desktop Launcher (`desktop/app.py`)

**Responsibilities**:
- Start Flask server in background thread
- Create PyWebView window
- Provide JS API for desktop features
- Handle application lifecycle (startup, shutdown)

**Key Classes/Functions**:
```python
class DesktopAPI:
    """API exposed to frontend via pywebview"""

    def select_file(self):
        """Native file dialog for MIB upload"""
        pass

    def show_notification(self, title, message):
        """System notification"""
        pass

    def get_app_info(self):
        """Application version and info"""
        pass

def main():
    """Application entry point"""
    pass
```

### 2. Build Configuration (`desktop/build.spec`)

**PyInstaller Settings**:
```python
a = Analysis(
    ['app.py'],
    datas=[...],  # Asset files
    hiddenimports=[...],  # Hidden dependencies
    hookspath=[],
    excludes=['tkinter', 'matplotlib'],  # Exclude unused
)

exe = EXE(
    pyz,
    a.scripts,
    # ... platform-specific settings
    console=False,  # Hide console on Windows/macOS
    icon='assets/icon.icns'  # Platform-specific icon
)
```

### 3. Build Helper (`desktop/build.py`)

**Purpose**: Automate build process for all platforms

**Features**:
- Detect current platform
- Run PyInstaller with correct settings
- Post-processing (DMG creation, code signing, etc.)
- Validation (check if executable runs)

**Structure**:
```python
def build_platform():
    """Build for current platform"""
    platform = detect_platform()
    clean_build_dir()
    run_pyinstaller(platform)
    post_process(platform)
    validate_build()

def detect_platform():
    """Return 'windows', 'macos', or 'linux'"""
    pass

def post_process(platform):
    """Platform-specific post-processing"""
    if platform == 'macos':
        create_dmg()
    elif platform == 'windows':
        sign_exe()
```

### 4. Icon Resources (`desktop/icons/`)

**Requirements**:
- **Windows**: `.ico` file, multiple resolutions (16x16 to 256x256)
- **macOS**: `.icns` file, multiple resolutions
- **Linux**: `.png` file, 512x512 recommended

**Implementation**:
- Use SVG master icon
- Convert to platform-specific formats using tools:
  - ImageMagick (`convert`)
  - icoutils (Windows)
  - `iconutil` (macOS)

## Data Flow

### Startup Flow
```
1. User launches desktop app
   ↓
2. PyWebView main() starts
   ↓
3. Flask thread starts (127.0.0.1:5000)
   ↓
4. Wait 2 seconds for Flask initialization
   ↓
5. PyWebView creates window
   ↓
6. Window loads http://127.0.0.1:5000
   ↓
7. Flask serves web application
   ↓
8. User interacts with app normally
```

### File Upload Flow (Native Dialog)
```
1. User clicks "Upload MIB" button
   ↓
2. JavaScript calls pywebview.api.select_file()
   ↓
3. DesktopAPI.select_file() opens native file dialog
   ↓
4. User selects MIB file(s)
   ↓
5. File path returned to JavaScript
   ↓
6. JavaScript fetch() uploads to Flask API
   ↓
7. Flask processes file normally
```

### Shutdown Flow
```
1. User closes window
   ↓
2. PyWebView receives close event
   ↓
3. Main thread exits
   ↓
4. Daemon Flask thread automatically terminates
   ↓
5. Application exits cleanly
```

## Security Considerations

### 1. Localhost Binding
- Flask binds to `127.0.0.1` only
- Not accessible from network
- Safe for desktop use

### 2. CORS Configuration
- Current CORS allows all origins (`*`)
- Desktop app: Can restrict to `http://127.0.0.1:5000`
- Minor security improvement

### 3. File Access
- Native file dialog controlled by PyWebView
- User explicitly selects files
- No arbitrary file system access

### 4. Code Signing (Future)
- **Windows**: Code signing certificate (prevents SmartScreen warnings)
- **macOS**: Developer ID and notarization (required for distribution)
- **Linux**: GPG signing (optional but recommended)

## Performance Considerations

### 1. Startup Time
**Target**: < 5 seconds

**Breakdown**:
- Python startup: ~1 second
- Flask initialization: ~1-2 seconds
- PyWebView window creation: ~1 second
- Page load: ~1 second

**Optimization**:
- Use PyInstaller `--onefile` (slower startup, but simpler)
- Consider `--onedir` if startup too slow
- Lazy-load heavy modules

### 2. Memory Usage
**Target**: < 200 MB overhead

**Components**:
- Python runtime: ~30 MB
- Flask + dependencies: ~50 MB
- PyWebView: ~20 MB
- System WebView: Variable (OS-managed)
- Total: ~100-150 MB typical

### 3. Package Size
**Target**: < 100 MB per platform

**Optimization**:
- Exclude unused dependencies (tkinter, test modules)
- Use UPX compression (PyInstaller default)
- Minimize bundled assets

## Platform-Specific Details

### Windows
**Executable**: `MIBParser.exe`

**Requirements**:
- Windows 10 1809+ (for Edge WebView2)
- Edge WebView2 Runtime (pre-installed on Win10 1809+)

**PyInstaller Config**:
```python
exe = EXE(
    # ...
    console=False,  # No console window
    icon='icons/mib-parser.ico',
    manifest='windows/manifest.xml',  # UAC level, compatibility
)
```

**Post-processing**:
- Optional: Code signing
- Optional: Create installer (NSIS, InnoSetup)

### macOS
**Application Bundle**: `MIBParser.app`

**Requirements**:
- macOS 10.15 Catalina+
- Xcode (for build tools)

**PyInstaller Config**:
```python
app = BUNDLE(
    exe,
    name='MIBParser.app',
    icon='icons/mib-parser.icns',
    bundle_identifier='com.mibparser.app',
    info_plist='macos/Info.plist',
)
```

**Post-processing**:
- Create DMG: `hdiutil create`
- Code signing: `codesign --sign`
- Notarization: `xcrun notarytool`
- Stapling: `xcrun stapler staple`

### Linux
**Executable**: `mib-parser` (binary)

**Requirements**:
- Ubuntu 20.04+ / Debian 11+ / equivalent
- WebKitGTK development libraries

**PyInstaller Config**:
```python
exe = EXE(
    # ...
    console=True,  # Keep console for debugging
    icon='icons/mib-parser.png',
)
```

**Post-processing**:
- Create .desktop file for application menu
- Optional: AppImage for universal distribution
- Optional: Package for specific distros (deb, rpm)

## Testing Strategy

### Unit Testing
- Test DesktopAPI methods
- Test thread startup/shutdown
- Test platform detection logic

### Integration Testing
- Manual testing on each platform
- Verify all Flask features work
- Test file dialog integration
- Test window controls

### Build Testing
- Verify executable runs on clean VM
- Test on minimum supported OS version
- Validate package size
- Check for missing dependencies

## Future Enhancements

### Phase 2 Features (Not in v1)
1. **System Tray Icon**: Minimize to tray, background operation
2. **Auto-Updates**: Check for updates, download and install
3. **Single Instance**: Ensure only one instance running
4. **URL Scheme**: `mibparser://` protocol handler
5. **File Association**: Open .mib files with desktop app

### Implementation Notes
- PyWebView supports system tray (pywebview.menu)
- Auto-updates would need update server/client
- Single instance: Platform-specific (mutex, file lock, etc.)
- URL schemes: Registry (Windows), Info.plist (macOS), .desktop (Linux)

## Rollout Plan

### Phase 1: Core Implementation (Days 1-2)
- Create desktop launcher
- Basic PyInstaller config
- Test on all platforms

### Phase 2: Polish (Day 3)
- Add icons
- Optimize build
- Create build scripts
- Write documentation

### Phase 3: Distribution (Future)
- Set up signing certificates
- Configure notarization (macOS)
- Create installers (optional)
- Host downloads

## Monitoring and Maintenance

### Metrics to Track
- Download counts (if hosted)
- Bug reports by platform
- Startup time by platform
- Package size trends

### Maintenance Tasks
- Update dependencies (PyWebView, PyInstaller)
- Test on new OS versions
- Renew code signing certificates
- Refresh icons for new design standards

## Documentation Requirements

1. **User Documentation**:
   - Installation instructions per platform
   - Known issues
   - Troubleshooting guide

2. **Developer Documentation**:
   - Build process
   - How to update icons
   - How to add new desktop features

3. **Release Notes**:
   - Platform-specific notes
   - Known limitations
   - Upgrade instructions
