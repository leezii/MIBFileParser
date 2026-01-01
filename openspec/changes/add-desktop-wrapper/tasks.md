# Tasks: Desktop Application Wrapper

## Overview
Ordered list of implementation tasks for adding desktop application wrapper. Each task should be independently verifiable and deliver user-visible progress.

---

## Phase 1: Foundation (Day 1)

### Task 1.1: Create Desktop Launcher
**Priority**: P0 (Critical)
**Estimated**: 2 hours
**Dependencies**: None

**Description**:
Create the desktop launcher that starts Flask and opens PyWebView window.

**Implementation**:
- [ ] Create `desktop/app.py` with:
  - `start_flask()` function to run Flask in background thread
  - `DesktopAPI` class with basic methods (get_version, select_file)
  - `main()` function to orchestrate startup
- [ ] Add PyWebView dependency to `pyproject.toml`
- [ ] Test launcher works: `python desktop/app.py`

**Verification**:
- Running `python desktop/app.py` opens a desktop window
- Window displays the Flask web application
- All web features work in desktop window
- No console errors

**Acceptance Criteria**:
- Desktop window opens successfully
- Flask app loads in window
- User can interact with web app normally
- Clean shutdown on window close

---

### Task 1.2: Add Native File Dialog
**Priority**: P0 (Critical)
**Estimated**: 1 hour
**Dependencies**: Task 1.1

**Description**:
Integrate native file picker for MIB file uploads.

**Implementation**:
- [ ] Implement `DesktopAPI.select_file()` method
- [ ] Add JavaScript bridge in web frontend
- [ ] Modify upload page to use native dialog when in desktop mode
- [ ] Test file selection and upload flow

**Verification**:
- Clicking "Upload MIB" button opens native file dialog
- Selected file path is returned to JavaScript
- File uploads successfully to Flask API
- Works on all three platforms (Windows, macOS, Linux)

**Acceptance Criteria**:
- Native file dialog opens on all platforms
- File uploads work correctly
- User experience is better than browser file input

---

### Task 1.3: Add Application Icon
**Priority**: P1 (High)
**Estimated**: 2 hours
**Dependencies**: None

**Description**:
Create professional application icons for all platforms.

**Implementation**:
- [ ] Design/create SVG master icon (512x512)
- [ ] Convert to platform-specific formats:
  - Windows: `.ico` (multi-resolution)
  - macOS: `.icns` (multi-resolution)
  - Linux: `.png` (512x512)
- [ ] Create `desktop/icons/` directory
- [ ] Add icon parameter to `webview.create_window()`

**Verification**:
- Icons display correctly on each platform
- Icons are visually consistent across platforms
- Icons look professional at all sizes

**Acceptance Criteria**:
- Icons created for all platforms
- Icons display in taskbar/dock/window title
- Icons are visually appealing

---

## Phase 2: Packaging (Day 2)

### Task 2.1: Create PyInstaller Configuration
**Priority**: P0 (Critical)
**Estimated**: 2 hours
**Dependencies**: Task 1.1

**Description**:
Create PyInstaller spec file to package the application.

**Implementation**:
- [ ] Add PyInstaller to `pyproject.toml` (dev dependencies)
- [ ] Create `desktop/build.spec` with:
  - Data files (storage/, static/, templates/)
  - Hidden imports (Flask modules)
  - Excluded modules (tkinter, test frameworks)
  - Platform-specific settings
- [ ] Test build: `pyinstaller desktop/build.spec --onefile --windowed`

**Verification**:
- PyInstaller successfully creates executable
- Executable runs and displays desktop window
- All features work in packaged app
- No missing module errors

**Acceptance Criteria**:
- Executable builds successfully
- Packaged app works identically to development version
- Package size is reasonable (<100 MB)

---

### Task 2.2: Platform-Specific Packaging
**Priority**: P1 (High)
**Estimated**: 3 hours
**Dependencies**: Task 2.1

**Description**:
Configure platform-specific packaging and post-processing.

**Implementation**:

**Windows**:
- [ ] Set `console=False` in build.spec
- [ ] Use `.ico` icon
- [ ] Test on Windows 10/11

**macOS**:
- [ ] Create `macos/Info.plist` with bundle metadata
- [ ] Use `.icns` icon
- [ ] Set `BUNDLE` instead of `EXE` in build.spec
- [ ] Test on macOS 10.15+

**Linux**:
- [ ] Set `console=True` for debugging
- [ ] Use `.png` icon
- [ ] Create `.desktop` file for application menu
- [ ] Test on Ubuntu 20.04+

**Verification**:
- Application packages correctly on each platform
- Package is recognizable as desktop app
- Icons display correctly
- Application appears in start menu/launchers

**Acceptance Criteria**:
- Platform-specific packages created
- Apps install and run correctly
- Integration with desktop environment works

---

### Task 2.3: Optimize Package Size
**Priority**: P2 (Medium)
**Estimated**: 1 hour
**Dependencies**: Task 2.1

**Description**:
Reduce package size by excluding unnecessary dependencies.

**Implementation**:
- [ ] Analyze PyInstaller build log for unnecessary modules
- [ ] Add exclusions to build.spec:
  - `tkinter` (GUI toolkit we don't use)
  - `matplotlib` (if present)
  - `test` modules
  - `IPython`, `jupyter` (dev tools)
- [ ] Enable UPX compression (if available)
- [ ] Rebuild and measure size reduction

**Verification**:
- Package size < 100 MB per platform
- All features still work
- No missing module errors

**Acceptance Criteria**:
- Package size optimized
- No functionality broken
- Documentation notes exclusions

---

### Task 2.4: Create Build Automation Script
**Priority**: P2 (Medium)
**Estimated**: 2 hours
**Dependencies**: Task 2.2

**Description**:
Automate build process for all platforms.

**Implementation**:
- [ ] Create `desktop/build.py` with:
  - Platform detection
  - Clean build directory
  - Run PyInstaller
  - Platform-specific post-processing
  - Basic validation (executable runs)
- [ ] Add `--platform` flag to force specific platform build
- [ ] Add `--clean` flag to clean build artifacts
- [ ] Test build script on all platforms

**Verification**:
- `python desktop/build.py` builds for current platform
- Build script provides clear feedback
- Build artifacts are organized
- Errors are caught and reported clearly

**Acceptance Criteria**:
- Single command builds desktop app
- Build process is reproducible
- Documentation explains build process

---

## Phase 3: Polish & Testing (Day 3)

### Task 3.1: Add Desktop-Specific Features
**Priority**: P2 (Medium)
**Estimated**: 2 hours
**Dependencies**: Task 1.2

**Description**:
Add small desktop-specific enhancements.

**Implementation**:
- [ ] Add `DesktopAPI.show_notification()` for system notifications
- [ ] Add `DesktopAPI.get_app_info()` for version/platform info
- [ ] Add "About" dialog in web UI that calls desktop API
- [ ] Add window state persistence (size, position)

**Verification**:
- Notifications display correctly
- About dialog shows app info
- Window state persists across restarts

**Acceptance Criteria**:
- Desktop features enhance UX
- Features work on all platforms
- Features are discoverable by users

---

### Task 3.2: Update Documentation
**Priority**: P1 (High)
**Estimated**: 2 hours
**Dependencies**: Task 2.4

**Description**:
Document desktop application for users and developers.

**Implementation**:
- [ ] Update `README.md` with desktop app section
- [ ] Create `docs/desktop-installation.md` with:
  - Installation instructions per platform
  - Known issues/limitations
  - Troubleshooting guide
- [ ] Create `docs/desktop-development.md` with:
  - Build process
  - How to modify icons
  - How to add desktop features
- [ ] Add desktop app to CHANGELOG.md

**Verification**:
- Documentation is clear and accurate
- Installation instructions work
- Troubleshooting guide covers common issues

**Acceptance Criteria**:
- Users can install desktop app following docs
- Developers can build desktop app following docs
- Documentation is maintained with code changes

---

### Task 3.3: Cross-Platform Testing
**Priority**: P0 (Critical)
**Estimated**: 3 hours
**Dependencies**: Task 2.2

**Description**:
Test desktop application on all supported platforms.

**Implementation**:
- [ ] Test on Windows 10/11:
  - Installation and launch
  - All web features
  - Native file dialog
  - Window controls
  - Shutdown
- [ ] Test on macOS 10.15+:
  - Same tests as Windows
  - App bundle validation
  - Notarization (if configured)
- [ ] Test on Ubuntu 20.04+:
  - Same tests as Windows
  - .desktop file integration
- [ ] Document any platform-specific issues

**Verification**:
- Application works on all platforms
- All features tested
- Known issues documented

**Acceptance Criteria**:
- Desktop app tested on Windows, macOS, Linux
- Critical features verified
- Test results documented

---

### Task 3.4: Performance Optimization
**Priority**: P2 (Medium)
**Estimated**: 2 hours
**Dependencies**: Task 3.3

**Description**:
Optimize startup time and memory usage.

**Implementation**:
- [ ] Measure startup time on each platform
- [ ] Profile memory usage
- [ ] Optimize if needed:
  - Lazy import modules
  - Reduce bundled assets
  - Optimize Flask startup
- [ ] Document performance characteristics

**Verification**:
- Startup time < 5 seconds on all platforms
- Memory usage < 200 MB overhead
- Performance is acceptable for user needs

**Acceptance Criteria**:
- App starts in reasonable time
- Memory usage is acceptable
- Performance is documented

---

## Phase 4: Release Preparation (Optional)

### Task 4.1: Code Signing (Windows)
**Priority**: P3 (Low)
**Estimated**: 2 hours
**Dependencies**: Task 2.2

**Description**:
Sign Windows executable to prevent SmartScreen warnings.

**Implementation**:
- [ ] Obtain code signing certificate
- [ ] Configure signing in build process
- [ ] Sign executable
- [ ] Test on clean Windows machine

**Verification**:
- Executable shows publisher name
- No SmartScreen warnings on clean machine

**Acceptance Criteria**:
- Windows executable is signed
- Installation is smoother for users

---

### Task 4.2: Notarization (macOS)
**Priority**: P3 (Low)
**Estimated**: 3 hours
**Dependencies**: Task 2.2

**Description**:
Configure macOS app notarization for distribution.

**Implementation**:
- [ ] Enroll in Apple Developer Program
- [ ] Configure app signing
- [ ] Submit for notarization
- [ ] Stapling ticket to app
- [ ] Test on clean macOS machine

**Verification**:
- App installs without Gatekeeper warnings
- Notarization is successful

**Acceptance Criteria**:
- macOS app is notarized
- Distribution-ready package

---

### Task 4.3: Create Installers (Optional)
**Priority**: P3 (Low)
**Estimated**: 4 hours
**Dependencies**: Task 2.2

**Description**:
Create installers for better user experience.

**Implementation**:
- [ ] **Windows**: Create NSIS or InnoSetup installer
- [ ] **macOS**: Create DMG with background image
- [ ] **Linux**: Create AppImage (universal) or deb/rpm

**Verification**:
- Installers work correctly
- Uninstallation works
- Installation process is smooth

**Acceptance Criteria**:
- Professional installers for each platform
- Good user experience

---

## Task Summary

### Critical Path (Must complete for MVP)
1. Task 1.1: Create Desktop Launcher (2h)
2. Task 1.2: Add Native File Dialog (1h)
3. Task 2.1: Create PyInstaller Configuration (2h)
4. Task 2.2: Platform-Specific Packaging (3h)
5. Task 3.3: Cross-Platform Testing (3h)

**Total**: ~11 hours (1.5 days)

### Recommended for v1.0
Add to critical path:
- Task 1.3: Application Icons (2h)
- Task 3.2: Update Documentation (2h)

**Total**: ~15 hours (2 days)

### Future Enhancements (Phase 2)
- Task 3.1: Desktop-Specific Features
- Task 3.4: Performance Optimization
- Task 4.1-4.3: Code Signing, Notarization, Installers

---

## Dependencies Diagram

```
Task 1.1 (Desktop Launcher)
    ├─→ Task 1.2 (File Dialog)
    └─→ Task 2.1 (PyInstaller Config)
            └─→ Task 2.2 (Platform Packaging)
                    └─→ Task 2.3 (Optimize)
                    └─→ Task 2.4 (Build Script)
                    └─→ Task 3.3 (Testing)
                            └─→ Task 3.4 (Performance)

Task 1.3 (Icons) - Parallel

Task 3.1 (Desktop Features) - After 1.2
Task 3.2 (Documentation) - After 2.4

Task 4.1-4.3 (Release Prep) - After 2.2
```

---

## Progress Tracking

**Phase 1: Foundation** - 0/3 tasks
**Phase 2: Packaging** - 0/4 tasks
**Phase 3: Polish & Testing** - 0/4 tasks
**Phase 4: Release Preparation** - 0/3 tasks

**Overall**: 0/14 tasks complete (0%)
