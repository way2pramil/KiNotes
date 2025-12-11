# NoneType Cleanup Errors - Fix Applied

## Problem Summary

During console testing of the plugin (4+ open/close cycles), two non-blocking warnings appeared:

```
[KiNotes] Todo save warning: 'NoneType' object has no attribute 'save_todos'
[KiNotes] Version log save warning: 'NoneType' object has no attribute 'save_version_log'
```

These warnings appeared after the "Cleanup complete" message, indicating they occurred during or after the cleanup sequence.

## Root Cause

The issue was a redundant `force_save()` call in the shutdown sequence:

1. **In `_on_close()` (kinotes_action.py line ~320)**:
   - `self.main_panel.force_save()` ← **First call (WORKS)** - notes_manager is still valid
   - `self.main_panel.cleanup()` ← Sets `self.notes_manager = None` (step 10 of cleanup)
   - `wx.CallAfter(self._safe_destroy)` ← Queues async destruction

2. **In `_safe_destroy()` (kinotes_action.py line ~356)**:
   - `self.main_panel.force_save()` ← **Second call (FAILS)** - notes_manager already set to None
   - This tries to call:
     - `self.notes_manager.save_todos()` → AttributeError (notes_manager is None)
     - `self.notes_manager.save_version_log()` → AttributeError (notes_manager is None)

The exceptions were caught by try-except blocks in `force_save()` (main_panel.py lines 2004-2032), resulting in the warnings rather than crashes.

## Solution Applied

**Removed the redundant `force_save()` call from `_safe_destroy()`**

Since `force_save()` is already called in `_on_close()` BEFORE cleanup runs, there's no need to call it again in `_safe_destroy()`. The second call was redundant and could only fail.

### Code Changes

**File: kinotes_action.py**
**Method: `_safe_destroy()` (lines 352-378)**

**Before:**
```python
def _safe_destroy(self):
    """Safely destroy the frame after pending events."""
    try:
        # Final save
        try:
            if hasattr(self, 'main_panel') and self.main_panel:
                self.main_panel.force_save()  ← REMOVED (redundant)
        except:
            pass
        
        # Unbind frame events before destroy
        # ... rest of method
```

**After:**
```python
def _safe_destroy(self):
    """Safely destroy the frame after pending events."""
    try:
        # NOTE: force_save() already called in _on_close() before cleanup()
        # Calling it again here would fail since cleanup() sets notes_manager = None
        # So we skip the redundant save and just proceed to destruction cleanup
        
        # Unbind frame events before destroy
        # ... rest of method
```

## Verification

The fix ensures:

✅ **No redundant saves** - Data is saved once in `_on_close()` when notes_manager is valid
✅ **No NoneType warnings** - Second force_save() call removed, eliminating the error source
✅ **Clean console output** - Cleanup sequence completes without warnings
✅ **Proper shutdown sequence** - Cleanup still executes all 13 steps
✅ **Frame destruction** - Still safely destroys the frame and unbinds events

## Next Steps

1. **Test the fix**: Run the console capture script again and perform 5+ open/close cycles
2. **Verify**: Check that the NoneType warnings are gone
3. **Confirm**: Plugin should still function normally with clean shutdown logs

## Impact

- **Safety**: ✅ No change to behavior - already guaranteed data save in _on_close()
- **Performance**: ✅ Slight improvement - removes unnecessary second save call
- **Stability**: ✅ Cleaner logs, easier debugging
- **User Impact**: ✅ None - transparent internal fix

## Related Code Paths

- **Shutdown Initiation**: `_on_close()` → `force_save()` → `cleanup()` → `wx.CallAfter(_safe_destroy)`
- **Save Methods** (main_panel.py):
  - `force_save()` lines 2004-2032
  - `_save_notes()` - Saves notes data
  - `_save_todos()` lines 1986-2002 (in todo_tab.py mixin)
  - `_save_version_log()` lines 219-240 (in version_log_tab.py mixin)
  - `_auto_export_diary_on_close()` - Auto-saves work diary
- **Cleanup Method** (main_panel.py lines 2033-2119):
  - 13-step cleanup sequence including clearing notes_manager

## Files Modified

- `kinotes_action.py` - Removed redundant force_save() from _safe_destroy()

---

**Status**: ✅ **APPLIED - Ready for testing**
