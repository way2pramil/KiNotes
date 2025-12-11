"""
KiNotes Crash Safety Manager
Handles version tracking, crash detection, safe mode, and recovery.
"""
import os
import json
import shutil
from datetime import datetime
from typing import Optional, Dict, Tuple


# Current plugin version - bump this when releasing
PLUGIN_VERSION = "1.2.0"
DATA_VERSION = "1.0"


class CrashSafetyManager:
    """
    Manages crash detection, safe mode, and version migrations.
    
    Features:
    - Version bump detection with auto-backup
    - Crash flag to detect unclean shutdowns
    - Safe mode that disables risky beta features
    - Recovery suggestions and diagnostics
    """
    
    CRASH_FLAG_FILE = ".crash_flag"
    SAFE_MODE_FILE = ".safe_mode"
    VERSION_FILE = "version.json"
    
    def __init__(self, notes_dir: str):
        """
        Initialize crash safety manager.
        
        Args:
            notes_dir: Path to .kinotes directory
        """
        self.notes_dir = notes_dir
        self.crash_flag_path = os.path.join(notes_dir, self.CRASH_FLAG_FILE)
        self.safe_mode_path = os.path.join(notes_dir, self.SAFE_MODE_FILE)
        self.version_path = os.path.join(notes_dir, self.VERSION_FILE)
        
        self._ensure_dir_exists()
    
    def _ensure_dir_exists(self):
        """Ensure notes directory exists."""
        try:
            if not os.path.exists(self.notes_dir):
                os.makedirs(self.notes_dir)
        except Exception as e:
            print(f"[CrashSafety] Error creating directory: {e}")
    
    # ========== Crash Detection ==========
    
    def mark_startup(self) -> bool:
        """
        Mark that plugin is starting up.
        Creates crash flag file. If flag already exists, previous run crashed.
        
        Returns:
            True if previous run crashed, False if clean startup
        """
        try:
            # Check if crash flag already exists
            crashed = os.path.exists(self.crash_flag_path)
            
            if crashed:
                print("[CrashSafety] ⚠ Detected unclean shutdown (crash)")
                self._log_crash_event()
            
            # Create new crash flag
            with open(self.crash_flag_path, 'w') as f:
                f.write(datetime.now().isoformat())
            
            return crashed
            
        except Exception as e:
            print(f"[CrashSafety] Error marking startup: {e}")
            return False
    
    def mark_clean_shutdown(self):
        """Remove crash flag on clean exit."""
        try:
            if os.path.exists(self.crash_flag_path):
                os.remove(self.crash_flag_path)
        except Exception as e:
            print(f"[CrashSafety] Error marking clean shutdown: {e}")
    
    def _log_crash_event(self):
        """Log crash event for diagnostics."""
        try:
            crash_log_path = os.path.join(self.notes_dir, "crash_log.json")
            
            # Load existing log
            crashes = []
            if os.path.exists(crash_log_path):
                with open(crash_log_path, 'r') as f:
                    crashes = json.load(f)
            
            # Add new crash entry
            crashes.append({
                "timestamp": datetime.now().isoformat(),
                "plugin_version": PLUGIN_VERSION,
            })
            
            # Keep only last 10 crashes
            crashes = crashes[-10:]
            
            # Save
            with open(crash_log_path, 'w') as f:
                json.dump(crashes, f, indent=2)
                
        except Exception as e:
            print(f"[CrashSafety] Error logging crash: {e}")
    
    # ========== Safe Mode ==========
    
    def should_use_safe_mode(self) -> bool:
        """
        Check if safe mode should be enabled.
        Safe mode is enabled after crashes or when manually activated.
        
        Returns:
            True if safe mode should be active
        """
        try:
            # Check for manual safe mode activation
            if os.path.exists(self.safe_mode_path):
                return True
            
            # Check recent crash history
            crash_log_path = os.path.join(self.notes_dir, "crash_log.json")
            if os.path.exists(crash_log_path):
                with open(crash_log_path, 'r') as f:
                    crashes = json.load(f)
                
                # If 2+ crashes in last 3 entries, enable safe mode
                if len(crashes) >= 2 and len(crashes[-3:]) >= 2:
                    return True
            
            return False
            
        except Exception as e:
            print(f"[CrashSafety] Error checking safe mode: {e}")
            return False
    
    def enable_safe_mode(self):
        """Manually enable safe mode."""
        try:
            with open(self.safe_mode_path, 'w') as f:
                f.write(datetime.now().isoformat())
            print("[CrashSafety] Safe mode enabled")
        except Exception as e:
            print(f"[CrashSafety] Error enabling safe mode: {e}")
    
    def disable_safe_mode(self):
        """Disable safe mode."""
        try:
            if os.path.exists(self.safe_mode_path):
                os.remove(self.safe_mode_path)
            print("[CrashSafety] Safe mode disabled")
        except Exception as e:
            print(f"[CrashSafety] Error disabling safe mode: {e}")
    
    def get_safe_mode_config(self) -> Dict[str, bool]:
        """
        Get safe configuration that disables risky beta features.
        
        Returns:
            Dict with safe settings (all beta features disabled)
        """
        return {
            'use_visual_editor': False,  # Fallback to markdown
            'beta_features_enabled': False,
            'beta_table': False,
            'beta_markdown': True,  # Use safe markdown mode
            'beta_bom': False,
            'beta_version_log': False,
            'beta_net_linker': False,
            'beta_debug_panel': False,
        }
    
    # ========== Version Management ==========
    
    def check_version(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check for version changes and handle migrations.
        
        Returns:
            (version_changed, old_version, new_version)
        """
        try:
            old_version = None
            
            if os.path.exists(self.version_path):
                with open(self.version_path, 'r') as f:
                    version_data = json.load(f)
                    old_version = version_data.get('plugin_version')
            
            new_version = PLUGIN_VERSION
            version_changed = old_version != new_version
            
            if version_changed and old_version:
                print(f"[CrashSafety] Version bump detected: {old_version} → {new_version}")
            
            return version_changed, old_version, new_version
            
        except Exception as e:
            print(f"[CrashSafety] Error checking version: {e}")
            return False, None, PLUGIN_VERSION
    
    def update_version(self):
        """Update version file to current plugin version."""
        try:
            version_data = {
                'plugin_version': PLUGIN_VERSION,
                'data_version': DATA_VERSION,
                'updated_at': datetime.now().isoformat(),
            }
            
            with open(self.version_path, 'w') as f:
                json.dump(version_data, f, indent=2)
                
        except Exception as e:
            print(f"[CrashSafety] Error updating version: {e}")
    
    def backup_on_version_bump(self) -> bool:
        """
        Create full backup of .kinotes folder on version bump.
        
        Returns:
            True if backup succeeded
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_v{PLUGIN_VERSION}_{timestamp}"
            backup_path = os.path.join(
                os.path.dirname(self.notes_dir),
                f".kinotes_{backup_name}"
            )
            
            # Copy entire .kinotes directory
            shutil.copytree(self.notes_dir, backup_path)
            
            print(f"[CrashSafety] ✓ Backup created: {backup_name}")
            
            # Rotate old version backups (keep last 3)
            self._rotate_version_backups()
            
            return True
            
        except Exception as e:
            print(f"[CrashSafety] Error creating version backup: {e}")
            return False
    
    def _rotate_version_backups(self):
        """Keep only last 3 version backups."""
        try:
            parent_dir = os.path.dirname(self.notes_dir)
            backups = []
            
            for item in os.listdir(parent_dir):
                if item.startswith('.kinotes_backup_v'):
                    full_path = os.path.join(parent_dir, item)
                    if os.path.isdir(full_path):
                        backups.append((os.path.getmtime(full_path), full_path))
            
            # Sort by time (newest first)
            backups.sort(reverse=True)
            
            # Remove old backups beyond 3
            for _, backup_path in backups[3:]:
                try:
                    shutil.rmtree(backup_path)
                    print(f"[CrashSafety] Removed old backup: {os.path.basename(backup_path)}")
                except:
                    pass
                    
        except Exception as e:
            print(f"[CrashSafety] Error rotating backups: {e}")
    
    # ========== Recovery & Diagnostics ==========
    
    def get_crash_summary(self) -> Dict:
        """
        Get summary of recent crashes for diagnostics.
        
        Returns:
            Dict with crash statistics
        """
        try:
            crash_log_path = os.path.join(self.notes_dir, "crash_log.json")
            
            if not os.path.exists(crash_log_path):
                return {
                    'total_crashes': 0,
                    'recent_crashes': [],
                }
            
            with open(crash_log_path, 'r') as f:
                crashes = json.load(f)
            
            return {
                'total_crashes': len(crashes),
                'recent_crashes': crashes[-5:],  # Last 5
                'safe_mode_recommended': len(crashes) >= 2,
            }
            
        except Exception as e:
            print(f"[CrashSafety] Error getting crash summary: {e}")
            return {'total_crashes': 0, 'recent_crashes': []}
    
    def clear_crash_history(self):
        """Clear crash log (after successful recovery)."""
        try:
            crash_log_path = os.path.join(self.notes_dir, "crash_log.json")
            if os.path.exists(crash_log_path):
                os.remove(crash_log_path)
            print("[CrashSafety] Crash history cleared")
        except Exception as e:
            print(f"[CrashSafety] Error clearing crash history: {e}")
