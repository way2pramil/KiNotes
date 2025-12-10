"""
Build script for KiCad PCM (Plugin and Content Manager) package.

Creates a ZIP archive with the proper folder structure:
    Archive root
    |- plugins/
       |- KiNotes/
          |- __init__.py
          |- kinotes_action.py
          |- core/
          |- ui/
          |- resources/
             |- icon.png
             |- icons/
    |- resources/
       |- icon.png (64x64 for PCM display)
    |- metadata.json

Usage: python build_pcm_package.py
"""

import os
import shutil
import zipfile
import hashlib
import json
from pathlib import Path

# Configuration
VERSION = "1.4.1"
PACKAGE_NAME = "com.pcbtools.kinotes"
OUTPUT_DIR = Path("dist/pcm")
SOURCE_DIR = Path("KiNotes")

def get_sha256(filepath):
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def build_pcm_package():
    """Build the PCM-compliant ZIP package."""
    print(f"Building KiNotes PCM Package v{VERSION}")
    print("=" * 50)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create temporary build directory
    build_dir = OUTPUT_DIR / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    
    # Create folder structure
    plugins_dir = build_dir / "plugins" / "KiNotes"
    resources_dir = build_dir / "resources"
    plugins_dir.mkdir(parents=True)
    resources_dir.mkdir()
    
    # Copy plugin files to plugins/KiNotes/
    print("Copying plugin files...")
    
    # Copy Python files and directories
    for item in ["__init__.py", "kinotes_action.py", "core", "ui", "resources"]:
        src = SOURCE_DIR / item
        dst = plugins_dir / item
        if src.is_file():
            shutil.copy2(src, dst)
            print(f"  Copied {item}")
        elif src.is_dir():
            shutil.copytree(src, dst)
            print(f"  Copied {item}/")
    
    # Copy icon to root resources/ for PCM display (64x64)
    icon_src = SOURCE_DIR / "resources" / "icon.png"
    if icon_src.exists():
        shutil.copy2(icon_src, resources_dir / "icon.png")
        print("  Copied icon.png to resources/")
    
    # Copy metadata.json to root
    metadata_src = SOURCE_DIR / "metadata.json"
    shutil.copy2(metadata_src, build_dir / "metadata.json")
    print("  Copied metadata.json")
    
    # Remove __pycache__ directories
    print("Cleaning up cache files...")
    for cache_dir in build_dir.rglob("__pycache__"):
        shutil.rmtree(cache_dir)
    for pyc_file in build_dir.rglob("*.pyc"):
        pyc_file.unlink()
    
    # Create ZIP archive
    zip_filename = f"KiNotes-{VERSION}_kicad-pcm.zip"
    zip_path = OUTPUT_DIR / zip_filename
    
    print(f"Creating ZIP archive: {zip_filename}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in build_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(build_dir)
                zipf.write(file_path, arcname)
    
    # Calculate hash
    file_hash = get_sha256(zip_path)
    file_size = zip_path.stat().st_size
    
    print(f"\nPackage created successfully!")
    print(f"  File: {zip_path}")
    print(f"  Size: {file_size:,} bytes")
    print(f"  SHA256: {file_hash}")
    
    # Create metadata file for PCM submission (with download info)
    submission_metadata = {
        "$schema": "https://go.kicad.org/pcm/schemas/v1",
        "name": "KiNotes",
        "description": "Smart Engineering Notes for KiCad 9+ with @REF linking, BOM import, and PDF export",
        "description_full": "KiNotes brings real engineering notes directly inside KiCad pcbnew — with zero friction.\n\nFeatures:\n• Dual-Mode Editor: Visual WYSIWYG or Markdown\n• Auto-link designators: type @R1, @U3 → highlights component on PCB\n• Import board metadata: BOM, Stackup, Netlist, Layers, Diff Pairs\n• Dark/Light themes with custom colors\n• Export to PDF and Markdown\n• Per-task time tracking with work diary\n• Git-friendly .kinotes/ folder storage\n\nBuilt by PCBtools.xyz for modern KiCad workflows.",
        "identifier": PACKAGE_NAME,
        "type": "plugin",
        "author": {
            "name": "PCBtools.xyz",
            "contact": {
                "web": "https://pcbtools.xyz",
                "github": "https://github.com/way2pramil"
            }
        },
        "maintainer": {
            "name": "PCBtools.xyz",
            "contact": {
                "web": "https://pcbtools.xyz"
            }
        },
        "license": "MIT",
        "resources": {
            "homepage": "https://pcbtools.xyz",
            "repository": "https://github.com/way2pramil/KiNotes",
            "issues": "https://github.com/way2pramil/KiNotes/issues"
        },
        "versions": [
            {
                "version": VERSION,
                "status": "stable",
                "kicad_version": "9.0",
                "download_sha256": file_hash,
                "download_size": file_size,
                "download_url": f"https://github.com/way2pramil/KiNotes/releases/download/v{VERSION}/{zip_filename}",
                "install_size": sum(f.stat().st_size for f in build_dir.rglob("*") if f.is_file())
            }
        ]
    }
    
    submission_path = OUTPUT_DIR / f"metadata_submission_{VERSION}.json"
    with open(submission_path, 'w', encoding='utf-8') as f:
        json.dump(submission_metadata, f, indent=2)
    
    print(f"\nPCM submission metadata: {submission_path}")
    print("\nTo submit to KiCad PCM repository:")
    print("1. Create a GitHub release with the ZIP file")
    print("2. Update download_url in metadata_submission.json")
    print("3. Submit to https://gitlab.com/kicad/addons/metadata")
    
    # Cleanup build directory
    shutil.rmtree(build_dir)
    
    return zip_path

if __name__ == "__main__":
    build_pcm_package()
