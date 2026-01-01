# Proposal: Add Desktop Application Wrapper

## Change ID
`add-desktop-wrapper`

## Summary
Add a desktop application wrapper using PyWebView to package the existing Flask web application as a standalone desktop application for Windows, macOS, and Linux.

## Problem Statement
The MIB Parser is currently a web-based application that requires users to:
- Manually start a Flask server
- Open a browser and navigate to localhost
- Have Python environment set up

This creates friction for users who prefer a traditional desktop application experience with:
- Single-click launcher
- Standalone application window (not in browser)
- No Python environment setup required
- Better integration with desktop environment

## Proposed Solution
Use **PyWebView** to wrap the existing Flask application into a desktop application. PyWebView is chosen because:
- **Zero code changes**: Existing Flask code works as-is
- **Lightweight**: Uses system WebView (30-50 MB final size)
- **Cross-platform**: Supports Windows, macOS, and Linux
- **Python native**: No new language to learn
- **Fast to implement**: 1-2 day development time

## Scope

### In Scope ✅
1. **Desktop launcher** - Single executable that launches the app
2. **Native window** - Standalone application window (not browser tab)
3. **File dialog integration** - Native file picker for MIB uploads
4. **Application packaging** - Windows (EXE), macOS (APP/DMG), Linux (binary)
5. **Application icon** - Professional desktop app icons
6. **Basic desktop features**:
   - Window controls (minimize, maximize, close)
   - Resizable window with minimum size
   - System notifications (optional)
   - Basic JS API for desktop-specific features

### Out of Scope ❌
1. System tray integration (future enhancement)
2. Auto-update mechanism (future enhancement)
3. Offline mode modifications (Flask remains the same)
4. Custom window chrome/decorations (use system defaults)
5. Deep OS integration (file associations, protocol handlers)

## Technical Approach

### Architecture
```
┌─────────────────────────────────┐
│   Desktop Application Window    │
│  ┌───────────────────────────┐  │
│  │   System WebView          │  │
│  │  ┌─────────────────────┐  │  │
│  │  │  Flask Web App      │  │  │
│  │  │  (existing code)    │  │  │
│  │  └─────────────────────┘  │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
           ↑
           │  HTTP (localhost)
           │
┌─────────────────────────────────┐
│   Python Process                │
│   - Flask Server (127.0.0.1)    │
│   - MIB Parser Service          │
│   - All existing logic          │
└─────────────────────────────────┘
```

### Implementation Strategy
1. **Launcher script** (`desktop/app.py`) - Starts Flask in background thread, creates WebView window
2. **PyInstaller config** - Packages Python + dependencies into single executable
3. **Application resources** - Icons, metadata, config files
4. **Build scripts** - Platform-specific packaging scripts

### Key Technologies
- **PyWebView 5.0+** - Desktop wrapper framework
- **PyInstaller 6.0+** - Application packaging
- **Existing Flask app** - No changes required
- **Thread-based architecture** - Flask runs in background thread

## Success Criteria

### Functional Requirements
- [ ] Application launches as standalone desktop window
- [ ] All existing web features work identically
- [ ] File uploads use native file picker dialogs
- [ ] Application can be packaged for Windows, macOS, Linux
- [ ] Application icon displays correctly on all platforms
- [ ] Window is resizable with sensible minimum size (1000x600)

### Non-Functional Requirements
- [ ] Application startup time < 5 seconds
- [ ] Memory overhead < 200 MB (in addition to Flask)
- [ ] Package size < 100 MB per platform
- [ ] No code changes required to existing Flask application
- [ ] Desktop app works offline (after installation)

### User Experience Goals
- [ ] Single-click launch from desktop/start menu
- [ ] No visible console window (except on Linux for debugging)
- [ ] Native window controls work correctly
- [ ] Application behaves like other native desktop apps

## Dependencies

### Technical Dependencies
- PyWebView 5.0+ must support all target platforms
- PyInstaller must successfully package the application
- System WebView must be available (Edge on Windows 10+, WebKit on macOS, WebKitGTK on Linux)

### Code Changes Required
- **New files**:
  - `desktop/app.py` - Desktop launcher
  - `desktop/build.spec` - PyInstaller configuration
  - `desktop/build.py` - Build helper script
  - `desktop/icons/` - Application icons
- **Modified files**:
  - `pyproject.toml` - Add PyWebView and PyInstaller dependencies
  - `.gitignore` - Exclude build artifacts
- **No Flask code changes needed**

### Impact on Existing Code
- **Zero impact** - Flask application remains unchanged
- **Optional DESKTOP_MODE flag** - Can be used to detect desktop mode in Flask (for future enhancements)

## Alternatives Considered

### 1. Electron
**Pros**: More mature ecosystem, deeper OS integration
**Cons**: Large size (150+ MB), requires Node.js middle layer, more complex
**Decision**: Rejected due to size and complexity

### 2. Tauri
**Pros**: Smallest size (~15 MB), Rust performance
**Cons**: Requires rewriting backend in Rust, high development cost
**Decision**: Rejected due to rewrite effort

### 3. CEF Python
**Pros**: Full Chromium features
**Cons**: Large size, complex configuration, smaller community
**Decision**: Rejected due to complexity

### 4. Simple Browser Launcher
**Pros**: Minimal changes, very fast
**Cons**: Runs in browser tab, poor UX
**Decision**: Rejected due to user experience

## Risks and Mitigations

### Risk 1: PyInstaller compatibility issues
**Mitigation**: Test early with all three platforms, use proven PyInstaller config patterns

### Risk 2: System WebView compatibility
**Mitigation**: Require minimum OS versions (Windows 10+, macOS 10.15+, Ubuntu 20.04+)

### Risk 3: Package size too large
**Mitigation**: Use PyInstaller exclusions, optimize dependencies, test with `--onefile`

### Risk 4: Flask blocking the main thread
**Mitigation**: Run Flask in daemon thread, use proper thread synchronization

## Open Questions

1. **Should we support system tray icon?**
   - Recommendation: Start without, add in future if users request it
   - Impact: Low (PyWebView supports this)

2. **Should we implement auto-updates?**
   - Recommendation: No for v1, evaluate based on user feedback
   - Impact: Medium (would require update server/client logic)

3. **What should the default window size be?**
   - Recommendation: 1400x900 (matches most modern laptop screens)
   - Impact: Low (easy to change)

4. **Should we support command-line arguments?**
   - Recommendation: Yes, basic ones like `--port`, `--debug`
   - Impact: Low

## Timeline Estimate

**Total: 2-3 days**

- Day 1: Core integration (PyWebView launcher, basic packaging)
- Day 2: Packaging and testing (all three platforms, icons)
- Day 3: Polish and documentation (build scripts, user docs)

## Related Changes
None - This is a standalone feature addition

## References
- Technical analysis document: `docs/桌面化技术方案分析.md`
- PyWebView documentation: https://pywebview.flowrl.com/
- PyInstaller documentation: https://pyinstaller.org/
