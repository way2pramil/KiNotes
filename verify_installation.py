"""
KiNotes Plugin Installation Verification Script

Run this in KiCad Scripting Console (Tools → Scripting Console)
to verify KiNotes plugin is properly installed.

Copy and paste the entire script into the console.
"""

print("=" * 60)
print("KiNotes Installation Verification")
print("=" * 60)

# 1. Check Python version
import sys
print(f"\n✓ Python Version: {sys.version.split()[0]}")
if sys.version_info < (3, 9):
    print("  ⚠ WARNING: Python 3.9+ required")

# 2. Check wxPython
try:
    import wx
    print(f"✓ wxPython Version: {wx.version()}")
    if wx.version() < "4.2":
        print("  ⚠ WARNING: wxPython 4.2+ recommended")
except ImportError as e:
    print(f"✗ wxPython NOT FOUND: {e}")

# 3. Check pcbnew
try:
    import pcbnew
    print(f"✓ pcbnew Version: {pcbnew.Version()}")
    print(f"✓ ActionPlugin Available: {hasattr(pcbnew, 'ActionPlugin')}")
except Exception as e:
    print(f"✗ pcbnew ERROR: {e}")

# 4. Check KiNotes installation
print(f"\n{'=' * 60}")
print("KiNotes Module Check")
print("=" * 60)

try:
    # Try importing KiNotes
    import KiNotes
    print(f"✓ KiNotes Module Found")
    print(f"  Location: {KiNotes.__file__}")
    print(f"  Version: {getattr(KiNotes, '__version__', 'Unknown')}")
    
    # Check for required classes
    has_plugin = hasattr(KiNotes, 'KiNotesActionPlugin')
    has_frame = hasattr(KiNotes, 'KiNotesFrame')
    
    print(f"✓ KiNotesActionPlugin: {'Found' if has_plugin else 'MISSING'}")
    print(f"✓ KiNotesFrame: {'Found' if has_frame else 'MISSING'}")
    
    # Try to instantiate plugin
    if has_plugin:
        try:
            from KiNotes import KiNotesActionPlugin
            plugin = KiNotesActionPlugin()
            plugin.defaults()
            print(f"\n✓ Plugin Registration:")
            print(f"  Name: {plugin.name}")
            print(f"  Category: {plugin.category}")
            print(f"  Toolbar Button: {plugin.show_toolbar_button}")
            print(f"  Icon: {plugin.icon_file_name}")
            
            # Check icon file
            import os
            if os.path.exists(plugin.icon_file_name):
                print(f"  ✓ Icon file exists")
            else:
                print(f"  ✗ Icon file MISSING: {plugin.icon_file_name}")
            
            print(f"\n✓ KiNotes is properly installed!")
            print(f"\nTo use:")
            print(f"  1. Close this console")
            print(f"  2. Restart KiCad (if plugin just installed)")
            print(f"  3. Open a PCB file")
            print(f"  4. Look for KiNotes in:")
            print(f"     - Tools → External Plugins → KiNotes")
            print(f"     - Toolbar button (if icon exists)")
            
        except Exception as e:
            print(f"\n✗ Plugin instantiation failed:")
            print(f"  {e}")
            import traceback
            traceback.print_exc()
    
except ImportError as e:
    print(f"✗ KiNotes Module NOT FOUND")
    print(f"  Error: {e}")
    print(f"\nTroubleshooting:")
    print(f"  1. Verify installation path:")
    print(f"     Windows: C:\\Users\\<user>\\Documents\\KiCad\\9.0\\3rdparty\\plugins\\KiNotes\\")
    print(f"     Linux: ~/.local/share/kicad/9.0/3rdparty/plugins/KiNotes/")
    print(f"     macOS: ~/Library/Application Support/kicad/9.0/3rdparty/plugins/KiNotes/")
    print(f"  2. Ensure __init__.py exists in KiNotes folder")
    print(f"  3. Restart KiCad")
    print(f"\nCurrent Python search path:")
    for path in sys.path:
        print(f"  - {path}")

except Exception as e:
    print(f"✗ Unexpected error:")
    print(f"  {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'=' * 60}")
print("Verification Complete")
print("=" * 60)
