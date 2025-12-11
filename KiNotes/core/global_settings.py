"""
KiNotes Global Settings Manager - User-wide settings fallback.

Provides global settings that apply across all projects when no local
project-specific settings exist.

Global settings location:
- Windows: %USERPROFILE%\.kinotes\global_settings.json
- Linux/Mac: ~/.kinotes/global_settings.json

Usage:
    from .global_settings import GlobalSettingsManager
    
    global_mgr = GlobalSettingsManager()
    settings = global_mgr.load_settings()  # Returns dict or None
    global_mgr.save_settings({"dark_mode": True, ...})
"""
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any


def _log(msg: str):
    """Log message to console."""
    try:
        if sys.stdout is not None:
            print(msg)
            sys.stdout.flush()
    except:
        pass


class GlobalSettingsManager:
    """Manages global (user-wide) KiNotes settings."""
    
    SETTINGS_FILENAME = "global_settings.json"
    KINOTES_DIR = ".kinotes"
    
    def __init__(self):
        """Initialize global settings manager."""
        self._settings_path = self._get_global_settings_path()
    
    def _get_global_settings_path(self) -> Path:
        """Get path to global settings file in user's home directory."""
        # Get user home directory (works on Windows, Linux, Mac)
        home = Path.home()
        kinotes_dir = home / self.KINOTES_DIR
        return kinotes_dir / self.SETTINGS_FILENAME
    
    def load_settings(self) -> Optional[Dict[str, Any]]:
        """
        Load global settings from user's home directory.
        Returns dict if found, None if no global settings exist.
        """
        try:
            if not self._settings_path.exists():
                _log("[KiNotes] No global settings found")
                return None
            
            with open(self._settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                _log(f"[KiNotes] Loaded global settings from {self._settings_path}")
                return settings
        except Exception as e:
            _log(f"[KiNotes] Error loading global settings: {e}")
            return None
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Save settings to global location (user's home directory).
        Creates .kinotes directory if needed.
        Returns True on success.
        """
        try:
            # Ensure directory exists
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            _log(f"[KiNotes] Saved global settings to {self._settings_path}")
            return True
        except Exception as e:
            _log(f"[KiNotes] Error saving global settings: {e}")
            return False
    
    def get_settings_path(self) -> str:
        """Return the path where global settings are stored."""
        return str(self._settings_path)
    
    def has_global_settings(self) -> bool:
        """Check if global settings file exists."""
        return self._settings_path.exists()


# Singleton instance for convenience
_global_manager: Optional[GlobalSettingsManager] = None


def get_global_settings_manager() -> GlobalSettingsManager:
    """Get singleton GlobalSettingsManager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = GlobalSettingsManager()
    return _global_manager


__all__ = ["GlobalSettingsManager", "get_global_settings_manager"]
