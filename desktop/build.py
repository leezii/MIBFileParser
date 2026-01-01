#!/usr/bin/env python3
"""
Automated build script for MIB Parser Desktop Application.

This script handles the complete build process:
1. Platform detection
2. Clean build directory
3. Run PyInstaller
4. Post-processing (signing, packaging)
5. Validation

Usage:
    python build.py [--clean] [--platform PLATFORM]
"""

import sys
import os
import subprocess
import shutil
import argparse
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log(msg, color=Colors.OKGREEN):
    """Print colored message."""
    print(f"{color}{msg}{Colors.ENDC}")

def log_error(msg):
    """Print error message."""
    log(msg, Colors.FAIL)

def log_warning(msg):
    """Print warning message."""
    log(msg, Colors.WARNING)

def log_info(msg):
    """Print info message."""
    log(msg, Colors.OKBLUE)

def detect_platform():
    """Detect current platform."""
    platform = sys.platform
    if platform == 'darwin':
        return 'macos'
    elif platform == 'win32':
        return 'windows'
    elif platform.startswith('linux'):
        return 'linux'
    else:
        return 'unknown'

def clean_build_dir(dist_dir, build_dir):
    """Clean build artifacts."""
    log_info("Cleaning build directory...")

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        log(f"  Removed {dist_dir}")

    if build_dir.exists():
        shutil.rmtree(build_dir)
        log(f"  Removed {build_dir}")

    log("✓ Clean complete")

def check_icon_files(desktop_root):
    """Check if icon files exist."""
    icons_dir = desktop_root / 'icons'

    if not icons_dir.exists():
        log_warning("  Icons directory not found")
        return False

    platform = detect_platform()

    if platform == 'macos':
        icon_file = icons_dir / 'icon.icns'
    elif platform == 'windows':
        icon_file = icons_dir / 'icon.ico'
    elif platform == 'linux':
        icon_file = icons_dir / 'icon.png'
    else:
        icon_file = None

    if icon_file and not icon_file.exists():
        log_warning(f"  {icon_file.name} not found, using default")
        return False

    if icon_file and icon_file.exists():
        log(f"  Found {icon_file.name}")
        return True

    return False

def run_pyinstaller(spec_file, desktop_root, clean=True):
    """Run PyInstaller to build the application."""
    log_info("Running PyInstaller...")

    cmd = [sys.executable, '-m', 'PyInstaller', str(spec_file)]

    # Note: PyInstaller will clean by default, but we already cleaned above if clean flag was set

    log(f"  Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=desktop_root,
            capture_output=True,
            text=True,
            check=True
        )

        log("✓ PyInstaller completed successfully")

        if result.stdout:
            print(result.stdout)

        return True

    except subprocess.CalledProcessError as e:
        log_error("✗ PyInstaller failed")
        print(e.stdout)
        print(e.stderr)
        return False

def post_process_macos(dist_dir, desktop_root):
    """Post-process for macOS: create DMG."""
    log_info("Post-processing for macOS...")

    app_path = dist_dir / 'MIBParser.app'

    if not app_path.exists():
        log_error(f"  MIBParser.app not found in {dist_dir}")
        return False

    log(f"  Found {app_path}")

    # TODO: Create DMG
    log_info("  DMG creation not implemented (manual step)")
    log_info("  You can create a DMG using:")
    log_info("    hdiutil create -volname 'MIB Parser' -srcfolder MIBParser.app -ov -format UDZO MIB-Parser.dmg")

    return True

def post_process_windows(dist_dir, desktop_root):
    """Post-process for Windows: code signing (optional)."""
    log_info("Post-processing for Windows...")

    exe_path = dist_dir / 'MIBParser' / 'MIBParser.exe'

    if not exe_path.exists():
        # Try standalone exe
        exe_path = dist_dir / 'MIBParser.exe'

    if not exe_path.exists():
        log_error(f"  MIBParser.exe not found in {dist_dir}")
        return False

    log(f"  Found {exe_path}")

    # TODO: Code signing (optional)
    log_info("  Code signing not configured (optional step)")

    return True

def post_process_linux(dist_dir, desktop_root):
    """Post-process for Linux: create desktop entry."""
    log_info("Post-processing for Linux...")

    exe_path = dist_dir / 'mib-parser'

    if not exe_path.exists():
        log_error(f"  mib-parser not found in {dist_dir}")
        return False

    log(f"  Found {exe_path}")

    # Make executable
    os.chmod(exe_path, 0o755)
    log("  Made executable")

    # Create .desktop file
    desktop_entry = """[Desktop Entry]
Version=1.0
Type=Application
Name=MIB Parser
Comment=MIB File Parser and Viewer
Exec={path}
Icon=icon
Terminal=false
Categories=Development;Network;
"""

    desktop_file = dist_dir / 'mib-parser.desktop'
    with open(desktop_file, 'w') as f:
        f.write(desktop_entry.format(path=exe_path.absolute()))

    log(f"  Created {desktop_file}")

    # Copy icon if available
    icons_dir = desktop_root / 'icons'
    icon_src = icons_dir / 'icon.png'
    if icon_src.exists():
        icon_dst = dist_dir / 'icon.png'
        shutil.copy2(icon_src, icon_dst)
        log(f"  Copied icon to {icon_dst}")

    return True

def validate_build(dist_dir):
    """Validate the build by checking if executable exists."""
    log_info("Validating build...")

    platform = detect_platform()

    if platform == 'macos':
        artifact = dist_dir / 'MIBParser.app'
    elif platform == 'windows':
        artifact = dist_dir / 'MIBParser' / 'MIBParser.exe'
        if not artifact.exists():
            artifact = dist_dir / 'MIBParser.exe'
    elif platform == 'linux':
        artifact = dist_dir / 'mib-parser'
    else:
        log_warning("  Unknown platform, skipping validation")
        return False

    if artifact.exists():
        size = artifact.stat().st_size / (1024 * 1024)  # Size in MB
        log(f"✓ Build artifact: {artifact.name}")
        log(f"  Size: {size:.1f} MB")
        return True
    else:
        log_error(f"✗ Build artifact not found: {artifact}")
        return False

def main():
    """Main build function."""
    parser = argparse.ArgumentParser(description='Build MIB Parser Desktop Application')
    parser.add_argument('--clean', action='store_true', help='Clean build artifacts before building')
    parser.add_argument('--platform', type=str, choices=['macos', 'windows', 'linux'], help='Force platform (auto-detect if not specified)')
    parser.add_argument('--no-validation', action='store_true', help='Skip build validation')

    args = parser.parse_args()

    # Paths
    desktop_root = Path(__file__).parent.absolute()
    project_root = desktop_root.parent
    dist_dir = desktop_root / 'dist'
    build_dir = desktop_root / 'build'
    spec_file = desktop_root / 'build.spec'

    log("=" * 60)
    log("MIB Parser Desktop Application - Build Script")
    log("=" * 60)

    # Detect platform
    platform = args.platform or detect_platform()
    log(f"Platform: {platform}")

    if platform == 'unknown':
        log_error("Unknown platform, cannot build")
        return 1

    # Check spec file
    if not spec_file.exists():
        log_error(f"Spec file not found: {spec_file}")
        return 1

    # Clean if requested
    if args.clean:
        clean_build_dir(dist_dir, build_dir)

    # Check icons
    log_info("Checking icon files...")
    check_icon_files(desktop_root)

    # Run PyInstaller
    if not run_pyinstaller(spec_file, desktop_root, clean=args.clean):
        log_error("Build failed")
        return 1

    # Post-processing
    log_info("Post-processing...")

    if platform == 'macos':
        if not post_process_macos(dist_dir, desktop_root):
            log_warning("Post-processing had issues")
    elif platform == 'windows':
        if not post_process_windows(dist_dir, desktop_root):
            log_warning("Post-processing had issues")
    elif platform == 'linux':
        if not post_process_linux(dist_dir, desktop_root):
            log_warning("Post-processing had issues")

    # Validation
    if not args.no_validation:
        if not validate_build(dist_dir):
            log_error("Build validation failed")
            return 1

    # Success
    log("=" * 60)
    log("✓ Build completed successfully!")
    log("=" * 60)
    log(f"Build artifacts are in: {dist_dir}")
    log("")

    if platform == 'macos':
        log("To run the application:")
        log(f"  open {dist_dir / 'MIBParser.app'}")
    elif platform == 'windows':
        log("To run the application:")
        log(f"  {dist_dir / 'MIBParser' / 'MIBParser.exe'}")
    elif platform == 'linux':
        log("To run the application:")
        log(f"  {dist_dir / 'mib-parser'}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
