# Crash Safety System

## Overview
KiNotes includes a comprehensive crash detection and recovery system that protects user data during plugin updates and unexpected crashes.

## Components

### 1. Crash Detection (`core/crash_safety.py`)

**Key Features:**
- **Crash Flag File**: `.crash_flag` created on startup, deleted on clean shutdown
- **Crash History**: Tracks last 10 crash timestamps in `crash_log.json`
- **Safe Mode**: Auto-activates after 2+ crashes in 24 hours
- **Version Tracking**: Detects plugin version bumps (stored in `version.json`)

**Version Info:**
- Plugin Version: `1.2.0` (PLUGIN_VERSION constant)
- Data Version: `1.0` (DATA_VERSION constant)

### 2. Auto-Backups

**On Version Bump:**
- Full `.kinotes/` directory backup to `.kinotes_backup_v{version}_{timestamp}/`
- Rotates to keep 3 most recent backups
- Includes all notes, todos, settings, time logs

**On File Write:**
- Atomic writes (temp file + rename) via `notes_manager._atomic_write()`
- Timestamped backups before overwrite (rotates to 10 max)
- Recovery from backup on load errors

### 3. Safe Mode

**Triggers:**
- Crash flag detected on startup
- 2+ crashes in recent history (24 hours)

**Safe Configuration:**
```python
{
    'use_visual_editor': False,      # Use stable Markdown editor
    'beta_features_enabled': False,  # Disable beta features
    'beta_markdown': True,           # Keep markdown (stable)
    'beta_bom': False,
    'beta_version_log': False,
    'beta_net_linker': False,
    'beta_debug_panel': False
}
```

### 4. Debug Panel Integration

**Event Logging:**
- `EventLevel.SUCCESS`: Version backup created
- `EventLevel.WARNING`: Safe mode activated, backup failed
- `EventLevel.ERROR`: Crash detected

**Crash Statistics:**
- Total crash count
- Recent crashes (24h window)
- Last crash timestamp
- Safe mode status

## User Experience Flow

### Normal Startup
1. Check for version bump → create backup if needed
2. Mark startup with crash flag
3. Load settings normally
4. Update version file
5. Continue startup

### After Crash
1. Detect crash flag from previous session
2. Log crash event to debug panel
3. Check if safe mode should activate
4. Apply safe mode config (disable beta features)
5. Show crash recovery dialog after UI loads
6. User can:
   - Continue in safe mode
   - Clear crash history
   - Re-enable features via Settings

### Clean Shutdown
1. Stop timers (`time_tracker`, `auto_save_timer`)
2. Force save all data
3. **Mark clean shutdown** (removes crash flag)
4. Destroy window

## Files Created

**In `.kinotes/` directory:**
```
.crash_flag              # Presence = unclean shutdown
version.json             # {plugin_version, data_version}
crash_log.json           # {crashes: [{timestamp, version}]}
.safe_mode               # Presence = safe mode enabled
```

**Backups:**
```
.kinotes_backup_v1.1.0_20240115_143022/  # Version bump backups
.kinotes_backup_v1.2.0_20240120_091545/
{file}.backup.1, .2, ...                 # Per-file backups (rotated)
```

## Implementation Details

### Startup Sequence (main_panel.__init__)
```python
self.crash_safety = CrashSafetyManager(notes_dir)
self._safe_mode_active = False
self._version_bumped = False

# Run BEFORE loading settings
self._handle_crash_and_version_check()

# Load settings (may be overridden by safe mode)
self._load_color_settings()
```

### Crash/Version Check Method
```python
def _handle_crash_and_version_check(self):
    # 1. Check version bump → create backup
    version_changed, old_ver, new_ver = self.crash_safety.check_version()
    if version_changed and old_ver:
        self.crash_safety.backup_on_version_bump()
    
    # 2. Mark startup and check crash
    crashed = self.crash_safety.mark_startup()
    
    # 3. Apply safe mode if needed
    if crashed and self.crash_safety.should_use_safe_mode():
        self._safe_mode_active = True
        safe_config = self.crash_safety.get_safe_mode_config()
        # Override beta settings
    
    # 4. Update version file
    self.crash_safety.update_version()
```

### Clean Shutdown Hook
```python
def cleanup(self):
    # Stop timers, save data
    ...
    # Mark clean shutdown
    self.crash_safety.mark_clean_shutdown()
```

## API Reference

### CrashSafetyManager Methods

**Crash Detection:**
- `mark_startup()` → bool: Returns True if crashed
- `mark_clean_shutdown()`: Removes crash flag
- `should_use_safe_mode()` → bool: Check if 2+ crashes
- `enable_safe_mode()`: Creates .safe_mode file
- `disable_safe_mode()`: Removes .safe_mode file

**Version Management:**
- `check_version()` → (changed, old, new): Detect bumps
- `update_version()`: Write current version to file
- `backup_on_version_bump()` → bool: Full .kinotes backup

**Diagnostics:**
- `get_crash_summary()` → dict: Statistics for UI
- `clear_crash_history()`: Reset crash log
- `get_safe_mode_config()` → dict: Safe settings

## Testing Crash Recovery

### Simulate Crash:
1. Start KiNotes plugin
2. Kill KiCad process (Task Manager or `taskkill /F /IM kicad.exe`)
3. Restart KiCad + open KiNotes
4. Should see: Crash recovery dialog, safe mode active

### Simulate Version Bump:
1. Edit `PLUGIN_VERSION` in `crash_safety.py` (e.g., "1.2.0" → "1.3.0")
2. Restart KiNotes
3. Check for backup: `.kinotes_backup_v1.2.0_<timestamp>/`
4. Verify debug panel shows: "Version backup created: 1.2.0 → 1.3.0"

### Clear Crash History:
1. Open crash recovery dialog
2. Click "Clear Crash History"
3. Safe mode disabled, can re-enable beta features

## Design Philosophy

**Fail-Safe Principles:**
1. **Never lose user data**: Backups before any destructive operation
2. **Detect failures early**: Crash flag on startup
3. **Degrade gracefully**: Safe mode disables unstable features
4. **Transparent to user**: Clear recovery dialog, event logging
5. **Easy recovery**: One-click crash history reset

**Why Safe Mode?**
- Plugin updates may introduce bugs affecting beta features
- Settings changes can corrupt state
- Safe mode ensures stable operation while investigating
- User can manually re-enable features when confident

## Future Enhancements

- [ ] Export crash logs for bug reports
- [ ] Backup restoration UI (browse/restore old backups)
- [ ] Per-feature crash tracking (identify specific beta culprits)
- [ ] Automatic bug report generation with crash context
- [ ] Crash analytics dashboard in debug panel
