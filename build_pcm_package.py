"""
Build KiCad PCM package for KiNotes.

Creates: dist/KiNotes-{version}-pcm.zip
"""
import os
import shutil
import zipfile
import json
from pathlib import Path

def build():
    # Read version from metadata
    with open("KiNotes/metadata.json") as f:
        meta = json.load(f)
    version = meta["versions"][0]["version"]
    
    print(f"Building KiNotes PCM Package v{version}")
    
    dist = Path("dist")
    dist.mkdir(exist_ok=True)
    
    zip_name = dist / f"KiNotes-{version}-pcm.zip"
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add plugins/KiNotes/
        src = Path("KiNotes")
        for f in src.rglob("*"):
            if f.is_file() and "__pycache__" not in str(f):
                arcname = f"plugins/{f.relative_to(src.parent)}"
                zf.write(f, arcname)
                print(f"  + {arcname}")
        
        # Add root metadata.json
        zf.write("KiNotes/metadata.json", "metadata.json")
        print("  + metadata.json (root)")
        
        # Add resources/icon.png (64x64 for PCM)
        icon = Path("KiNotes/resources/icons/icon.png")
        if icon.exists():
            zf.write(icon, "resources/icon.png")
            print("  + resources/icon.png")
    
    print(f"\n✅ Created: {zip_name}")
    print(f"   Size: {zip_name.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    build()
