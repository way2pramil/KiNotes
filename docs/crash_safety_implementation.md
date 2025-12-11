# Crash Safety Implementation Guide

## Architecture

### Design Principles
1. **Non-blocking**: Initializes after UI is ready
2. **Graceful degradation**: Works fine if crash safety fails
3. **User-transparent**: No disruption to normal workflow
4. **Atomic writes**: Data never corrupted mid-write

### Initialization Flow

```
KiNotesMainPanel.__init__()
    ↓
_load_color_settings()      ← Load user preferences
    ↓
_init_ui()                   ← Create UI (may take time)
_load_all_data()             ← Load notes/todos
_start_auto_save_timer()     ← Start background save
    ↓
_init_crash_safety()         ← Initialize crash detection [AFTER UI ready]
    ↓
_show_crash_recovery_dialog() ← If crash detected
```

### Why Post-UI Initialization?

**Problem:** Original approach initialized crash safety in `__init__` before `_init_ui()`
```python
# OLD - CAUSES ERROR
def __init__(...):
    self.crash_safety = CrashSafetyManager(...)  # ← Can fail
    self._handle_crash_and_version_check()
    self._init_ui()                              # ← Too late to fix
```

**Solution:** Initialize after UI is complete
```python
# NEW - SAFE
def __init__(...):
    self.crash_safety = None
    self._init_ui()
    _init_crash_safety()  # ← After UI is ready, wrapped in try-except
```

---

## Core Components

### 1. CrashSafetyManager (`core/crash_safety.py`)

**Purpose:** Detect crashes, manage safe mode, track versions

**Key Methods:**

```python
# Crash Detection
mark_startup() → bool              # Returns True if crashed
mark_clean_shutdown()              # Clean shutdown (removes flag)

# Safe Mode Control
should_use_safe_mode() → bool      # Auto-detect if needed
get_safe_mode_config() → dict      # Returns safe settings
enable_safe_mode()                 # Manual enable
disable_safe_mode()                # Manual disable

# Version Management
check_version() → (bool, str, str) # Returns (changed, old, new)
update_version()                   # Update version.json
backup_on_version_bump() → bool    # Create backup on version change

# Diagnostics
get_crash_summary() → dict         # Crash stats for UI
clear_crash_history()              # Reset crash log
get_crash_summary()                # Return stats
```

**Files Used:**
```
.kinotes/
├── .crash_flag              # File exists = crash detected
├── .safe_mode               # File exists = safe mode on
├── version.json             # {plugin_version, data_version}
└── crash_log.json           # {crashes: [{timestamp, version}]}
```

### 2. Main Panel Integration (`ui/main_panel.py`)

**Crash Safety Instance Variables:**
```python
self.crash_safety: CrashSafetyManager  # Manager instance (or None)
self._safe_mode_active: bool           # Track if safe mode enabled
self._version_bumped: bool             # Track version changes
```

**Methods:**

```python
def _init_crash_safety(self):
    """Initialize crash safety after UI is ready."""
    if not HAS_CRASH_SAFETY or self.crash_safety is not None:
        return
    
    try:
        self.crash_safety = CrashSafetyManager(self.notes_manager.notes_dir)
        self._handle_crash_and_version_check()
        print("[KiNotes] Crash safety initialized")
    except Exception as e:
        print(f"[KiNotes] Crash safety init failed: {e}")
        self.crash_safety = None  # ← Graceful degradation

def _handle_crash_and_version_check(self):
    """Run version check and crash recovery (called after UI init)."""
    try:
        # 1. Check version
        version_changed, old_ver, new_ver = self.crash_safety.check_version()
        if version_changed:
            self.crash_safety.backup_on_version_bump()
        
        # 2. Mark startup (check for crash)
        crashed = self.crash_safety.mark_startup()
        
        # 3. Apply safe mode if needed
        if crashed and self.crash_safety.should_use_safe_mode():
            self._safe_mode_active = True
            safe_config = self.crash_safety.get_safe_mode_config()
            # Override beta settings
            for key, value in safe_config.items():
                setattr(self, f'_{key}', value)
        
        # 4. Update version
        self.crash_safety.update_version()
    except Exception as e:
        print(f"[KiNotes] Crash check failed: {e}")

def cleanup(self):
    """Called on shutdown - mark clean shutdown."""
    try:
        if self.crash_safety:
            self.crash_safety.mark_clean_shutdown()
    except Exception as e:
        print(f"[KiNotes] Cleanup warning: {e}")

def _show_crash_recovery_dialog(self):
    """Show recovery dialog to user after crash."""
    # Dialog with crash stats, options to clear history
```

---

## Safe Mode Configuration

### What Gets Disabled
```python
safe_config = {
    'use_visual_editor': False,      # Markdown stable
    'beta_features_enabled': False,  # All beta off
    'beta_table': False,
    'beta_markdown': True,           # Keep stable markdown
    'beta_bom': False,
    'beta_version_log': False,
    'beta_net_linker': False,
    'beta_debug_panel': False,
}
```

### Applied To
```python
# In _handle_crash_and_version_check():
for key, value in safe_config.items():
    setattr(self, f'_{key}', value)
```

This ensures:
- Visual Editor disabled (use Markdown)
- Net Linker disabled (safer)
- Debug Panel disabled (lighter)
- Core features still work

---

## Crash Detection Logic

### Startup Check
```
.crash_flag exists?
├── YES → Previous crash detected
│   ├── Log crash timestamp
│   ├── Check if 2+ crashes in 24h
│   └── Enable safe mode if threshold reached
├── NO → Clean startup
└── Create .crash_flag for this session
```

### Shutdown
```
KiNotes closing
├── Save all data
├── Stop timers
├── Call mark_clean_shutdown()
│   └── Delete .crash_flag
└── Close successfully
```

### If KiCad Crashes
```
No mark_clean_shutdown() called
├── .crash_flag remains
├── Next startup detects it
└── Triggers recovery
```

---

## Version Bump Handling

### Detection
```python
current_version = "1.4.2"
stored_version = version.json.get("plugin_version")

if current_version != stored_version:
    # Version bump detected!
    backup_on_version_bump()
```

### Backup
```
Before: .kinotes/
After: .kinotes_backup_v1.4.1_20241211_110523/
       └── Complete copy of .kinotes/
```

### Rotation
```
Keep: 3 most recent version backups
Delete: Older backups automatically
```

---

## Error Handling

### Philosophy: Fail Gracefully

**Principle:** Crash safety is enhancement, not requirement

**If crash safety fails:**
```python
try:
    self.crash_safety = CrashSafetyManager(...)
    self._handle_crash_and_version_check()
except Exception as e:
    print(f"Crash safety init failed: {e}")
    self.crash_safety = None  # ← Continue anyway
    # Plugin still works, just no crash detection
```

**Never blocks startup:**
- Initialization after UI complete
- Wrapped in try-except
- Continues even if exception
- Console logs any errors

---

## Testing

### Unit Tests
```python
# Test crash detection
def test_crash_flag_detection():
    mgr = CrashSafetyManager(temp_dir)
    assert mgr.mark_startup() == False  # No crash
    # Simulate crash - leave flag
    # Next startup should detect
    assert mgr.mark_startup() == True   # Crash detected

# Test safe mode
def test_safe_mode_auto_enable():
    # Create 2+ crash entries
    # Should auto-enable safe mode
    assert mgr.should_use_safe_mode() == True

# Test version bump
def test_version_backup():
    # Change version in version.json
    # Call check_version()
    # Should create backup
    assert backup_folder_exists()
```

### Manual Testing
```bash
# Simulate crash
1. Run KiNotes
2. Kill KiCad process: pkill -9 kicad
3. Restart KiCad
4. Check: Recovery dialog appears
5. Check: .kinotes/.crash_flag existed
6. Check: .kinotes/crash_log.json updated
```

---

## Performance Impact

### Minimal Overhead
- Startup check: ~1-5ms (file exists?)
- Version check: ~5-10ms (JSON read)
- Backup creation: ~50-200ms (directory copy, runs after UI)
- Safe mode apply: <1ms (bool assignments)

### Memory Usage
- CrashSafetyManager: ~1KB (small Python object)
- Crash log: ~500B (last 10 crashes)
- Version file: ~200B

---

## Future Enhancements

### Planned
- [ ] Crash recovery wizard (restore from specific backup)
- [ ] Crash analytics (which features cause crashes?)
- [ ] Per-feature crash tracking
- [ ] Auto bug report generation

### Possible
- [ ] Compress old backups
- [ ] Cloud backup sync
- [ ] Crash notifications
- [ ] Feature rollback on repeated crashes

---

## Troubleshooting

### Crash Safety Won't Initialize
**Log:** `[KiNotes] Crash safety init failed: ...`

**Causes:**
1. Notes directory doesn't exist (fixed automatically)
2. Permission denied on `.kinotes/` folder
3. Disk full (can't create files)

**Fix:**
- Check `.kinotes/` folder exists and writable
- Check disk space
- Restart KiCad

### Safe Mode Won't Disable
**Problem:** Safe mode stays active even after clearing history

**Fix:**
1. Delete `.kinotes/.safe_mode` file manually
2. Delete `.kinotes/crash_log.json`
3. Restart KiCad

### Recovery Dialog Appears Every Time
**Indicates:** `mark_clean_shutdown()` not being called

**Causes:**
1. KiCad closing too fast (before cleanup)
2. Exception in cleanup
3. Multiple KiCad instances

**Fix:**
- Check for multiple KiCad processes
- Look for exceptions in console output
- Verify `.crash_flag` removal in cleanup

---

## Code Organization

```
core/crash_safety.py
├── CrashSafetyManager class
│   ├── __init__(notes_dir)
│   ├── mark_startup()
│   ├── mark_clean_shutdown()
│   ├── check_version()
│   ├── backup_on_version_bump()
│   ├── should_use_safe_mode()
│   ├── get_safe_mode_config()
│   ├── get_crash_summary()
│   └── clear_crash_history()
├── Constants
│   ├── PLUGIN_VERSION = "1.4.2"
│   └── DATA_VERSION = "1.0"
└── Helper functions
    └── _ensure_safe_dir()

ui/main_panel.py
├── Imports
│   └── from ..core.crash_safety import ...
├── Class variables
│   └── HAS_CRASH_SAFETY flag
├── Instance variables
│   ├── self.crash_safety
│   ├── self._safe_mode_active
│   └── self._version_bumped
├── Methods
│   ├── _init_crash_safety()
│   ├── _handle_crash_and_version_check()
│   ├── _show_crash_recovery_dialog()
│   ├── _on_clear_crash_history()
│   └── cleanup()
└── Integrated with
    ├── __init__() → calls _init_crash_safety()
    ├── cleanup() → calls mark_clean_shutdown()
    └── _init_ui() → shows recovery dialog
```

---

## Version History

### v1.4.2 (Current)
- Crash safety implemented
- Post-UI initialization
- Safe mode auto-enable
- Recovery dialog
- Full versioning support

### v1.4.1
- Pre-crash safety (errors on crash detection)

### v1.4.0
- No crash safety
