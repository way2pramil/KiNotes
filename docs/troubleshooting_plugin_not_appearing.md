# KiNotes Plugin Not Appearing - Troubleshooting Guide

## Quick Checks

### 1. Verify Plugin Installation Location

KiCad 9 expects plugins in:
```
Windows: C:\Users\<username>\Documents\KiCad\9.0\3rdparty\plugins\
Linux: ~/.local/share/kicad/9.0/3rdparty/plugins/
macOS: ~/Library/Application Support/kicad/9.0/3rdparty/plugins/
```

**Correct structure:**
```
3rdparty/plugins/
└── KiNotes/
    ├── __init__.py           ← Must import and trigger registration
    ├── kinotes_action.py     ← Contains KiNotesActionPlugin class
    ├── resources/
    │   └── icon.png          ← 24x24 PNG icon (REQUIRED for toolbar)
    ├── ui/
    ├── core/
    └── ...
```

### 2. Check Icon File

**CRITICAL:** KiCad requires a 24x24 PNG icon to show the toolbar button.

```bash
# Check if icon exists:
dir resources\icon.png   # Windows
ls resources/icon.png    # Linux/macOS
```

If missing, the plugin won't appear in the toolbar (but may appear in Tools menu).

### 3. Verify Python Environment

KiCad 9 uses **embedded Python 3.9+** with **wxPython 4.2+**.

Open KiCad **Scripting Console** (Tools → Scripting Console):
```python
import sys
print(sys.version)  # Should show Python 3.9+

import wx
print(wx.version())  # Should show 4.2+

import pcbnew
print(dir(pcbnew.ActionPlugin))  # Verify ActionPlugin exists
```

### 4. Check for Import Errors

In KiCad Scripting Console:
```python
import KiNotes
print("KiNotes imported successfully")
```

If this fails, check error message:
- `ModuleNotFoundError`: Plugin not in correct location
- `ImportError`: Missing dependency or syntax error
- `AttributeError`: pcbnew version mismatch

### 5. Force Plugin Reload

KiCad caches plugins. After making changes:

**Method 1: Restart KiCad** (safest)

**Method 2: Reload via Scripting Console:**
```python
import sys
import importlib

# Remove cached modules
if 'KiNotes' in sys.modules:
    del sys.modules['KiNotes']
if 'KiNotes.kinotes_action' in sys.modules:
    del sys.modules['KiNotes.kinotes_action']

# Reimport
import KiNotes
print("Reloaded KiNotes")
```

**Method 3: Plugin Manager:**
- Tools → Plugin and Content Manager
- Click "Refresh" or "Reload Plugins"

## Common Issues

### Issue 1: Plugin Not in Tools Menu

**Symptom:** No "KiNotes" entry in Tools → External Plugins

**Causes:**
1. Plugin not in correct directory
2. `__init__.py` not importing `kinotes_action`
3. Import error (check scripting console)
4. `KiNotesActionPlugin().register()` not executed

**Fix:**
- Verify directory structure
- Check `__init__.py` imports `kinotes_action` module
- Run import test in scripting console
- Check for Python syntax errors

### Issue 2: Plugin in Menu But No Toolbar Button

**Symptom:** Plugin appears in Tools menu but not toolbar

**Causes:**
1. Missing `icon.png` file
2. Icon wrong format (must be PNG, 24x24)
3. `self.show_toolbar_button = False` in defaults()

**Fix:**
```python
# In kinotes_action.py, verify:
def defaults(self):
    self.show_toolbar_button = True  # Must be True
    icon_png = os.path.join(_plugin_dir, "resources", "icon.png")
    if os.path.exists(icon_png):
        self.icon_file_name = icon_png
```

Ensure `resources/icon.png` exists and is 24x24 PNG.

### Issue 3: Plugin Crashes on Click

**Symptom:** KiCad crashes or freezes when clicking plugin

**Causes:**
1. pcbnew API mismatch (KiCad version too old/new)
2. wxPython version mismatch
3. Python syntax error in plugin code
4. Missing required modules (e.g., richtext)

**Fix:**
- Check KiCad version: Help → About KiCad (need 9.0+)
- Test imports in scripting console
- Check Python console output for errors

### Issue 4: "No Board Open" Error

**Symptom:** Plugin runs but shows error about missing board

**Expected Behavior:** This is normal - KiNotes requires an open PCB file.

**Fix:**
- Open or create a PCB (.kicad_pcb file)
- Save the PCB to a writable location
- Then run KiNotes

### Issue 5: Read-Only Project Warning

**Symptom:** "Read-only project location" error

**Cause:** Project in `C:\Program Files` or KiCad demos folder

**Fix:**
- Save project to user directory (Documents, Desktop, etc.)
- KiNotes needs write access to create `.kinotes/` folder

## Testing Plugin Registration

### Step 1: Verify File Structure
```bash
cd C:\Users\<username>\Documents\KiCad\9.0\3rdparty\plugins\KiNotes
dir
```

Should see:
```
__init__.py
kinotes_action.py
resources\
core\
ui\
```

### Step 2: Test Import
Open KiCad Scripting Console:
```python
import sys
print(sys.path)  # Verify plugin directory is in path

import KiNotes
print(dir(KiNotes))  # Should show KiNotesActionPlugin

from KiNotes import KiNotesActionPlugin
print(KiNotesActionPlugin)  # Should show class
```

### Step 3: Manual Registration Test
```python
from KiNotes.kinotes_action import KiNotesActionPlugin
plugin = KiNotesActionPlugin()
plugin.register()
print("Plugin registered")
```

If this works, plugin should appear in Tools menu after restarting KiCad.

## Installation Checklist

- [ ] KiCad 9.0 or newer installed
- [ ] Plugin copied to `3rdparty/plugins/KiNotes/`
- [ ] `__init__.py` exists and imports `kinotes_action`
- [ ] `resources/icon.png` exists (24x24 PNG)
- [ ] No Python syntax errors (test imports)
- [ ] KiCad restarted after installation
- [ ] PCB file open and saved to writable location

## Debug Output

If plugin still not appearing, collect this info:

```python
# In KiCad Scripting Console:
import sys
print("Python version:", sys.version)
print("Python path:", sys.path)

import wx
print("wxPython version:", wx.version())

import pcbnew
print("pcbnew version:", pcbnew.Version())

# Try importing KiNotes
try:
    import KiNotes
    print("KiNotes imported OK")
    print("KiNotes location:", KiNotes.__file__)
except Exception as e:
    print("KiNotes import FAILED:", e)
    import traceback
    traceback.print_exc()
```

## Manual Installation Steps (Detailed)

### Windows:
1. Open File Explorer
2. Navigate to `C:\Users\<YourUsername>\Documents\KiCad\9.0\`
3. If `3rdparty\plugins\` doesn't exist, create it
4. Copy entire `KiNotes` folder into `plugins\`
5. Verify `KiNotes\__init__.py` exists
6. Verify `KiNotes\resources\icon.png` exists
7. Restart KiCad
8. Open a PCB file
9. Check Tools → External Plugins menu

### Linux:
```bash
mkdir -p ~/.local/share/kicad/9.0/3rdparty/plugins/
cp -r KiNotes ~/.local/share/kicad/9.0/3rdparty/plugins/
ls ~/.local/share/kicad/9.0/3rdparty/plugins/KiNotes/
# Should show __init__.py, kinotes_action.py, resources/, etc.
```

### macOS:
```bash
mkdir -p ~/Library/Application\ Support/kicad/9.0/3rdparty/plugins/
cp -r KiNotes ~/Library/Application\ Support/kicad/9.0/3rdparty/plugins/
ls ~/Library/Application\ Support/kicad/9.0/3rdparty/plugins/KiNotes/
```

## Still Not Working?

1. **Check KiCad console output:**
   - Windows: Run KiCad from Command Prompt to see console
   - Linux/macOS: Run from terminal

2. **Enable debug output:**
   Add to `kinotes_action.py` top:
   ```python
   print("[KiNotes DEBUG] Module loading...")
   ```

3. **Try minimal test plugin:**
   Create `test_plugin.py` in plugins folder:
   ```python
   import pcbnew
   
   class TestPlugin(pcbnew.ActionPlugin):
       def defaults(self):
           self.name = "Test Plugin"
           self.category = "Test"
           self.description = "Test"
       
       def Run(self):
           print("Test plugin running")
   
   TestPlugin().register()
   ```
   
   If this appears but KiNotes doesn't, issue is in KiNotes code.

## Contact

If none of these steps work, report issue with:
- KiCad version (Help → About)
- Python version (from scripting console)
- Installation path
- Error messages from scripting console import test
- Screenshot of plugin directory structure

Repository: https://github.com/way2pramil/KiNotes/issues
