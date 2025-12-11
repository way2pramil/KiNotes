# KiNotes Crash Safety - How It Works

## Overview

KiNotes has a **crash recovery system** that protects your data if KiCad crashes while you're working. It runs **safely in the background** without affecting normal operation.

## How Crash Safety Works

### 1. **Crash Detection**
- When KiNotes starts, it checks if the previous session crashed
- Crash indicator: `.crash_flag` file in `.kinotes/` folder
- If found → Safe Mode automatically activates

### 2. **Safe Mode** 
When a crash is detected:
- ✅ All your notes, todos, settings are **preserved**
- ⚠️ **Beta features disabled** (Visual Editor, Net Linker, Debug Panel)
- Uses **stable Markdown editor** only
- You can continue working safely

### 3. **Automatic Backups**
- **On startup:** Before loading any data
- **On version bump:** Full `.kinotes/` folder backup (keeps 3 recent)
- **On file write:** Atomic writes with temp file → rename (prevents corruption)

### 4. **Clean Shutdown**
- When you close KiNotes → `.crash_flag` is removed
- Indicates: "Session completed normally"

---

## File System

### New Files Created
```
.kinotes/
├── notes/                          ← Your notes (unchanged)
├── todos.json                      ← Tasks list (unchanged)
├── settings.json                   ← Your settings (unchanged)
│
└── [Crash Safety Files]
    ├── .crash_flag                 ← Present = unclean shutdown
    ├── .safe_mode                  ← Present = safe mode enabled
    ├── version.json                ← Plugin version tracking
    ├── crash_log.json              ← Crash history (last 10)
    │
    └── .kinotes_backup_v1.4.2_20241211_110523/  ← Version bump backups
       └── (full copy of .kinotes folder)
```

### What's Backed Up
✅ Notes files (`.md`)  
✅ Todos (`todos.json`)  
✅ Settings (`settings.json`)  
✅ Time tracking data  
✅ All metadata  

❌ Plugin code (can overwrite safely)

---

## What Happens When KiCad Crashes

### Scenario: KiCad crashes while you're editing notes

**Step 1: Crash Occurs**
```
[You're editing] → [KiCad crashes] → .crash_flag created
```

**Step 2: KiNotes Restarts**
```
KiCad restarts → KiNotes opens → Detects .crash_flag
```

**Step 3: Safe Mode Activates**
```
✓ All your notes preserved
✓ Settings preserved  
✓ Safe Mode enabled (beta features off)
✓ Recovery dialog shown
```

**Step 4: You Continue Working**
```
[Dialog] → Click "Continue"
[Use Markdown editor (stable)]
[When confident, re-enable beta features in Settings]
```

---

## Usage Guide

### Normal Operation (No Crash)
1. Start KiCad + KiNotes
2. Work normally (all features available)
3. Close KiNotes → clean shutdown (no files left)

### After a Crash
1. Restart KiCad
2. Open KiNotes → **Recovery dialog appears**
3. Dialog shows:
   - Crash count
   - Safe Mode is active
   - All data preserved
4. Options:
   - **"Continue"** → Use plugin in safe mode
   - **"Clear Crash History"** → Reset counter, disable safe mode
5. When confident: Settings → Re-enable beta features

---

## Recovery Dialog

**What you'll see:**
```
⚠ KiNotes Recovered from Crash

The previous KiNotes session ended unexpectedly.

Safe Mode is now active:
• Beta features temporarily disabled
• Using stable Markdown editor
• All project data preserved

Crash count: 1 recent incident(s)

[Clear Crash History]  [Continue]
```

### Button Actions

**"Continue"**
- Enters safe mode immediately
- Keep beta features disabled until you manually re-enable

**"Clear Crash History"**  
- Deletes crash log
- Disables safe mode
- Resets to normal operation
- **Restart KiCad for full effect**

---

## Disabling Safe Mode

**Method 1: Click Recovery Dialog Button**
```
Recovery Dialog → [Clear Crash History] → Restart KiCad
```

**Method 2: Settings Menu**
```
KiNotes → Settings → Look for "Safe Mode Status"
(If available) → Disable Safe Mode → Restart KiCad
```

**Method 3: Manual File Edit**
```
Delete: .kinotes/.safe_mode
Delete: .kinotes/crash_log.json
Restart KiCad
```

---

## Re-enabling Beta Features

After crash recovery, to use advanced features again:

1. **Ensure Safe Mode is disabled** (see above)
2. **Open Settings** (KiNotes → Settings)
3. **Beta Features section:**
   - ☑ Visual Editor (WYSIWYG mode)
   - ☑ Markdown Editor (advanced)
   - ☑ Net Linker (click nets)
   - ☑ Debug Panel (event log)
4. **Apply** → **Restart KiCad**

---

## Crash Safety Features

### ✅ What's Protected
- Your notes (never lost)
- Todos and task history  
- All settings and preferences
- Time tracking data
- Custom colors and themes

### ✅ What's Backed Up
- Full `.kinotes/` folder on version updates
- Automatic backup rotation (keeps 3 versions)
- Per-file backups on write (keeps 10)

### ✅ What's Automatic
- No user action needed
- Works silently in background
- No annoying prompts unless crash detected

---

## Advanced: Accessing Backups

### View Backup Folders
```
.kinotes/
├── .kinotes_backup_v1.4.2_20241211_110523/   ← Version bumps
├── .kinotes_backup_v1.4.1_20241210_093022/
└── .kinotes_backup_v1.4.0_20241205_151433/
```

### Restore from Backup (Manual)
1. Close KiCad completely
2. Backup current `.kinotes/` folder:
   ```
   Copy: .kinotes → .kinotes_mybackup
   ```
3. Restore desired backup:
   ```
   Copy: .kinotes_backup_v1.4.2_* → .kinotes
   ```
4. Restart KiCad

---

## Technical Details

### Crash Detection Method
- Startup: Check for `.crash_flag` file
- If exists → Previous session crashed
- Removed on clean shutdown

### Safe Mode Config
Temporarily disables:
```python
use_visual_editor: False       # Use Markdown (stable)
beta_features_enabled: False   # All beta off
beta_net_linker: False         # No net clicking
beta_debug_panel: False        # No event log
```

Keeps enabled:
```python
beta_markdown: True            # Stable Markdown editor
```

### Version Tracking
```json
// .kinotes/version.json
{
  "plugin_version": "1.4.2",
  "data_version": "1.0",
  "last_updated": "2024-12-11T11:05:23.123456"
}
```

### Crash Log
```json
// .kinotes/crash_log.json
{
  "crashes": [
    {
      "timestamp": "2024-12-11T10:45:12.345678",
      "version": "1.4.2"
    }
  ]
}
```

---

## FAQ

**Q: Will I lose my notes if KiCad crashes?**  
A: No. Notes are saved to disk immediately. Even if KiCad crashes during editing, your last saved version is preserved. Unsaved changes in the editor may be lost, but the file on disk is safe.

**Q: What if safe mode won't turn off?**  
A: Delete `.kinotes/.safe_mode` and `.kinotes/crash_log.json`, then restart KiCad.

**Q: How many crashes trigger safe mode?**  
A: 2 crashes within 24 hours = auto safe mode.

**Q: Can I work while in safe mode?**  
A: Yes! Safe mode only disables experimental features. Markdown editor, notes, todos all work normally.

**Q: What if crash safety fails?**  
A: If crash safety module can't load, plugin still works normally. Crash detection just won't be active. Your notes are always saved atomically.

**Q: Do I need to do anything manually?**  
A: No. It's all automatic. Recovery dialog appears only if crash detected.

---

## Testing Crash Safety (Optional)

**Simulate a crash (Linux/macOS):**
```bash
# Kill KiCad to simulate crash
pkill -9 kicad
```

**On Windows:**
- Task Manager → Find `kicad.exe` → End Task

**Then:**
1. Restart KiCad
2. Open KiNotes
3. Should see recovery dialog
4. Verify `.kinotes/.crash_flag` was created/detected

---

## Support

If you encounter issues with crash safety:

1. **Check console output** (run KiCad from terminal):
   ```
   Look for: "[KiNotes] Crash safety initialized"
   Or error messages starting with "[KiNotes]"
   ```

2. **Manual reset** (if stuck):
   ```
   Delete: .kinotes/.crash_flag
   Delete: .kinotes/.safe_mode  
   Delete: .kinotes/crash_log.json
   Restart KiCad
   ```

3. **Report issue** with:
   - KiCad version
   - KiNotes version (in plugin)
   - Contents of `.kinotes/crash_log.json`
   - Error messages from console
