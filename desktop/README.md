# MIB Parser - Desktop Application

This directory contains the desktop application wrapper for MIB Parser using PyWebView.

## Supported Platforms

- ✅ **macOS** (10.15+) - Application bundle (.app)
- ✅ **Windows** (10/11) - Executable (.exe)
- ✅ **Linux** - Standalone binary

## Quick Start

### Development Mode

Run the desktop application directly from source:

```bash
# From the project root
python desktop/app.py
```

Or using uv:

```bash
uv run python desktop/app.py
```

This will:
1. Start the Flask server in the background
2. Open a native desktop window
3. Load the MIB Parser web interface

### Building the Desktop Application

To create a standalone executable:

```bash
# From the desktop directory
python build.py

# Or from project root
python desktop/build.py

# With clean build
python desktop/build.py --clean
```

The build script will:
- Detect your platform (Windows, macOS, or Linux)
- Clean previous build artifacts (with `--clean`)
- Run PyInstaller to package the application
- Perform platform-specific post-processing
- Validate the build

## Build Artifacts

After building, you'll find the desktop application in `desktop/dist/`:

### macOS
- **MIBParser.app** - macOS application bundle
- To run: `open desktop/dist/MIBParser.app`
- To create DMG: `hdiutil create -volname "MIB Parser" -srcfolder desktop/dist/MIBParser.app -ov -format UDZO MIB-Parser.dmg`

### Windows
- **MIBParser/MIBParser.exe** - Windows executable in a folder
- To run: `desktop\dist\MIBParser\MIBParser.exe`
- 📖 **Detailed Guide**: See [BUILD_WINDOWS.md](BUILD_WINDOWS.md) for complete Windows build instructions

#### Quick Build on Windows

```powershell
# Install uv (if not already installed)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone and build
git clone <repository-url>
cd MIBFileParser
uv sync --extra desktop
cd desktop
uv run python build.py --clean
```

The executable will be in `desktop/dist/MIBParser/`.

### Linux
- **mib-parser** - Linux executable
- To run: `./desktop/dist/mib-parser`
- A .desktop file is also created for integration with your desktop environment

## Features

### Desktop-Specific Features

When running in desktop mode, the application has access to:

- **Native File Dialogs**: File picker uses the operating system's native dialog
- **System Notifications**: Can display system notifications (platform-dependent)
- **Desktop Window**: Standalone application window (not in browser)

### API Bridge

The desktop application provides a JavaScript API bridge (`window.DesktopAPI`):

```javascript
// Check if in desktop mode
if (window.DesktopAPI && window.DesktopAPI.isAvailable) {
    // Get app info
    window.DesktopAPI.getAppInfo().then(info => {
        console.log('Running on', info.platform);
    });

    // Show notification
    window.DesktopAPI.showNotification('Title', 'Message');

    // Open file dialog
    window.DesktopAPI.selectFiles(true).then(files => {
        console.log('Selected files:', files);
    });
}
```

## Architecture

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
           │  HTTP (localhost:5000)
           │
┌─────────────────────────────────┐
│   Python Process                │
│   - Flask Server                │
│   - MIB Parser Service          │
│   - All existing logic          │
└─────────────────────────────────┘
```

## Configuration

### Window Settings

Window configuration is in `desktop/app.py`:

```python
window = webview.create_window(
    title='MIB Parser & Viewer',
    url='http://127.0.0.1:5000',
    width=1400,
    height=900,
    min_size=(1000, 600),
    resizable=True,
    fullscreen=False,
)
```

### PyInstaller Settings

PyInstaller configuration is in `desktop/build.spec`:

- Included data files (storage, templates, static)
- Hidden imports (Flask modules, dependencies)
- Excluded modules (tkinter, test frameworks)
- Platform-specific settings

## Icons

Application icons are in `desktop/icons/`:

- `icon.svg` - Master SVG file (512x512)
- `icon.png` - PNG for Linux
- `icon.icns` - macOS icon bundle (to be generated)
- `icon.ico` - Windows icon (to be generated)

See `desktop/icons/README.md` for instructions on generating platform-specific icons.

## Dependencies

Desktop application dependencies are in `pyproject.toml`:

```toml
[project.optional-dependencies]
desktop = [
    "pywebview>=5.0.0",
    "pyinstaller>=6.0.0",
]
```

Install with:

```bash
uv sync --extra desktop
```

## Troubleshooting

### Application Won't Start

**Symptom**: Desktop window doesn't appear

**Possible causes**:
1. Flask server failed to start
   - Check console output for errors
   - Verify Flask app works: `python -m flask_app.app`
2. PyWebView not installed
   - Run: `uv sync --extra desktop`

### File Dialog Doesn't Work

**Symptom**: Native file dialog doesn't open

**Solution**:
- Ensure you're running in desktop mode (not browser)
- Check browser console for JavaScript errors
- Verify `window.DesktopAPI` is defined

### Build Fails

**Symptom**: PyInstaller build fails

**Common issues**:
1. Missing dependencies
   - Run: `uv sync --extra desktop`
2. Icon file missing
   - Check `desktop/icons/` has appropriate icon
   - Or build without icon (comment out in `build.spec`)
3. Permission errors
   - Ensure write permissions in `desktop/` directory

### Package Size Too Large

**Current size**: ~30-50 MB (expected)

If larger:
1. Check what's included in the package
2. Review exclusions in `build.spec`
3. Ensure test dependencies are excluded

## Platform-Specific Notes

### Windows

**Requirements**:
- Windows 10 1809+ (for Edge WebView2)
- Edge WebView2 Runtime (pre-installed on Win10 1809+)

**Known Issues**:
- First launch may show SmartScreen warning (normal for unsigned executables)
- Console window hidden (use `console=True` in `build.spec` for debugging)

### macOS

**Requirements**:
- macOS 10.15 Catalina+

**Known Issues**:
- Gatekeeper may warn on first launch (right-click → Open)
- For distribution, consider code signing and notarization

### Linux

**Requirements**:
- WebKitGTK development libraries

**Installation**:

**Ubuntu/Debian**:
```bash
sudo apt-get install python3-gi python3-gi-cairo gir1.2-webkit2-4.1
```

**Fedora**:
```bash
sudo dnf install python3-gobject python3-webkit2gtk
```

**Known Issues**:
- Console window visible (for debugging)
- Desktop file may need manual installation

## Development

### Testing Desktop Features

Test if desktop mode is active:

```python
# In browser console
console.log(window.DesktopAPI ? 'Desktop mode' : 'Browser mode');
```

### Adding New Desktop Features

1. Add method to `DesktopAPI` class in `desktop/app.py`
2. Add JavaScript wrapper in `src/flask_app/static/js/desktop.js`
3. Use in frontend code:

```javascript
if (window.DesktopAPI && window.DesktopAPI.isAvailable) {
    window.DesktopAPI.yourNewMethod();
}
```

## Future Enhancements

Possible future improvements:
- System tray icon
- Auto-update mechanism
- Single instance enforcement
- URL scheme handlers (`mibparser://`)
- File associations (double-click .mib files)
- Code signing and notarization

## Support

For issues or questions:
1. Check this README
2. Review technical analysis: `docs/桌面化技术方案分析.md`
3. Check OpenSpec proposal: `openspec/changes/add-desktop-wrapper/`

## License

Same as the main MIB Parser project.
