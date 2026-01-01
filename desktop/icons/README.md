# Application Icons

This directory contains application icons for the desktop wrapper.

## Icon Formats

### Source
- `icon.svg` - Master SVG icon (512x512)

### Generated Icons
The following icon files should be generated from the SVG master:

#### Windows
- `icon.ico` - Multi-resolution ICO file (16, 32, 48, 64, 128, 256)

#### macOS
- `icon.icns` - macOS icon bundle (multiple resolutions)

#### Linux
- `icon.png` - PNG file at 512x512

## Generating Icons

### Using ImageMagick

```bash
# Generate PNG
convert icon.svg -resize 512x512 icon.png

# Generate ICO (Windows)
# Need png2ico or ImageMagick with ICO support
convert icon.svg -define icon:auto-resize=256,128,64,48,32,16 icon.ico

# For macOS, use iconutil
# First create iconset directory
mkdir icon.iconset
# Generate different sizes
sips -z 16 16     icon.svg --out icon.iconset/icon_16x16.png
sips -z 32 32     icon.svg --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.svg --out icon.iconset/icon_32x32.png
sips -z 64 64     icon.svg --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   icon.svg --out icon.iconset/icon_128x128.png
sips -z 256 256   icon.svg --out icon.iconset/icon_128x128@2x.png
sips -z 256 256   icon.svg --out icon.iconset/icon_256x256.png
sips -z 512 512   icon.svg --out icon.iconset/icon_256x256@2x.png
sips -z 512 512   icon.svg --out icon.iconset/icon_512x512.png
# Create ICNS
iconutil -c icns icon.iconset
```

### Using Online Tools

1. **SVG to PNG**: https://cloudconvert.com/svg-to-png
2. **PNG to ICO**: https://convertio.co/png-ico/
3. **PNG to ICNS**: https://cloudconvert.com/png-to-icns

## Quick Generation Script

For macOS, you can use this script:

```bash
#!/bin/bash
cd "$(dirname "$0")"

# Generate PNG
sips -s format png icon.svg --out icon.png -z 512 512

# Generate iconset
mkdir -p icon.iconset
sips -s format png icon.svg --out icon.iconset/icon_16x16.png -z 16 16
sips -s format png icon.svg --out icon.iconset/icon_16x16@2x.png -z 32 32
sips -s format png icon.svg --out icon.iconset/icon_32x32.png -z 32 32
sips -s format png icon.svg --out icon.iconset/icon_32x32@2x.png -z 64 64
sips -s format png icon.svg --out icon.iconset/icon_128x128.png -z 128 128
sips -s format png icon.svg --out icon.iconset/icon_128x128@2x.png -z 256 256
sips -s format png icon.svg --out icon.iconset/icon_256x256.png -z 256 256
sips -s format png icon.svg --out icon.iconset/icon_256x256@2x.png -z 512 512
sips -s format png icon.svg --out icon.iconset/icon_512x512.png -z 512 512

# Create ICNS
iconutil -c icns icon.iconset
rm -rf icon.iconset

echo "Icons generated successfully!"
```

## Current Status

For now, we have the SVG master icon. Platform-specific icons will be generated during the build process.

## Usage in PyInstaller

In the PyInstaller spec file, reference the icons like this:

```python
# macOS
app = BUNDLE(
    ...
    icon='desktop/icons/icon.icns',
)

# Windows
exe = EXE(
    ...
    icon='desktop/icons/icon.ico',
)

# Linux
exe = EXE(
    ...
    icon='desktop/icons/icon.png',
)
```
