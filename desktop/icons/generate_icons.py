#!/usr/bin/env python3
"""
Generate application icons for all platforms.

This script generates:
- icon.ico: Windows icon (multiple sizes)
- icon.icns: macOS icon
- icon.png: Linux/Fallback icon
"""

from PIL import Image
import sys
from pathlib import Path


def generate_windows_icon(source_png: Path, output_ico: Path):
    """Generate Windows .ico file with multiple sizes."""
    print(f"Generating Windows icon: {output_ico}")

    img = Image.open(source_png)

    # Windows icon needs multiple sizes for best quality
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]

    # Create a list of images for different sizes
    icon_images = []
    for size in sizes:
        # Resize image to this size
        resized = img.resize(size, Image.Resampling.LANCZOS)
        icon_images.append(resized)

    # Save as ICO with all sizes
    icon_images[0].save(
        output_ico,
        format='ICO',
        sizes=[size for size, _ in zip(sizes, icon_images)]
    )

    print(f"  ✓ Created {output_ico} ({len(sizes)} sizes)")


def generate_macos_icon(source_png: Path, output_icns: Path):
    """Generate macOS .icns file using iconutil."""
    print(f"Generating macOS icon: {output_icns}")

    import subprocess
    import tempfile
    import shutil

    # Create temporary iconset directory
    with tempfile.TemporaryDirectory() as temp_dir:
        iconset_path = Path(temp_dir) / "icon.iconset"
        iconset_path.mkdir()

        # Generate required sizes for macOS
        sizes = [
            (16, 'icon_16x16.png'),
            (32, 'icon_16x16@2x.png'),
            (32, 'icon_32x32.png'),
            (64, 'icon_32x32@2x.png'),
            (128, 'icon_128x128.png'),
            (256, 'icon_128x128@2x.png'),
            (256, 'icon_256x256.png'),
            (512, 'icon_256x256@2x.png'),
            (512, 'icon_512x512.png'),
            (1024, 'icon_512x512@2x.png'),
        ]

        img = Image.open(source_png)

        for size, filename in sizes:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            output_path = iconset_path / filename
            resized.save(output_path, format='PNG')

        # Use iconutil to create .icns
        subprocess.run([
            'iconutil',
            '-c', 'icns',
            '-o', str(output_icns),
            str(iconset_path)
        ], check=True)

    print(f"  ✓ Created {output_icns}")


def generate_linux_icon(source_png: Path, output_png: Path):
    """Generate Linux icon (PNG at 512x512)."""
    print(f"Generating Linux icon: {output_png}")

    img = Image.open(source_png)
    img = img.resize((512, 512), Image.Resampling.LANCZOS)
    img.save(output_png, format='PNG', optimize=True)

    print(f"  ✓ Created {output_png}")


def main():
    """Generate all icons."""
    icons_dir = Path(__file__).parent
    source_svg = icons_dir / 'icon.svg'
    source_png = icons_dir / 'icon_512.png'

    if not source_png.exists():
        print(f"Error: Source PNG not found: {source_png}")
        print("Please ensure icon_512.png exists")
        sys.exit(1)

    print("=" * 60)
    print("MIB Parser - Icon Generator")
    print("=" * 60)

    # Generate Windows icon
    try:
        generate_windows_icon(source_png, icons_dir / 'icon.ico')
    except Exception as e:
        print(f"  ✗ Failed: {e}")

    # Generate macOS icon
    try:
        if sys.platform == 'darwin':
            generate_macos_icon(source_png, icons_dir / 'icon.icns')
        else:
            print("Skipping macOS icon (not on macOS)")
    except Exception as e:
        print(f"  ✗ Failed: {e}")

    # Generate Linux icon
    try:
        generate_linux_icon(source_png, icons_dir / 'icon.png')
    except Exception as e:
        print(f"  ✗ Failed: {e}")

    print("=" * 60)
    print("Icon generation complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
