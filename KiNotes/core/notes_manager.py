"""
KiNotes Notes Manager - Load/save notes, todos, settings to .kinotes folder
With crash-safe atomic writes and backup rotation
"""
import os
import re
import json
import shutil
import tempfile
from datetime import datetime


class NotesManager:
    """Manages loading and saving notes, todos, version log, and settings for a KiCad project."""
    
    NOTES_FOLDER = ".kinotes"
    BACKUP_FOLDER = "backups"
    LEGACY_NOTES_FILE = "notes.md"  # Old filename for migration
    TODOS_FILE = "todos.json"
    VERSION_LOG_FILE = "version_log.json"
    SETTINGS_FILE = "settings.json"
    META_FILE = "meta.json"
    MAX_BACKUPS = 10  # Keep last N backups
    
    def __init__(self, project_dir):
        """Initialize with project directory path."""
        self.project_dir = project_dir
        self.project_name = self._get_project_name()
        self.notes_dir = os.path.join(project_dir, self.NOTES_FOLDER)
        self.backup_dir = os.path.join(self.notes_dir, self.BACKUP_FOLDER)
        self.notes_path = os.path.join(self.notes_dir, f"KiNotes_{self.project_name}.md")
        self.legacy_notes_path = os.path.join(self.notes_dir, self.LEGACY_NOTES_FILE)
        self.todos_path = os.path.join(self.notes_dir, self.TODOS_FILE)
        self.version_log_path = os.path.join(self.notes_dir, self.VERSION_LOG_FILE)
        self.settings_path = os.path.join(self.notes_dir, self.SETTINGS_FILE)
        self.meta_path = os.path.join(self.notes_dir, self.META_FILE)
        
        # First ensure folder exists, then migrate
        self._ensure_folder_exists()
        self._migrate_legacy_notes()
    
    def _get_project_name(self) -> str:
        """Get sanitized project name from directory."""
        name = os.path.basename(self.project_dir)
        # Sanitize: remove special characters, replace spaces with underscores
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        name = name.replace(' ', '_')
        # Remove leading/trailing underscores
        name = name.strip('_')
        return name if name else "project"
    
    def _migrate_legacy_notes(self):
        """Migrate from old notes.md to new KiNotes_<project>.md format."""
        # Only migrate if legacy exists and new file doesn't
        if os.path.exists(self.legacy_notes_path) and not os.path.exists(self.notes_path):
            try:
                # Read content from legacy file
                with open(self.legacy_notes_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Write to new filename
                with open(self.notes_path, "w", encoding="utf-8") as f:
                    f.write(content)
                # Rename legacy file to .bak to avoid re-migration
                backup_path = self.legacy_notes_path + ".bak"
                os.rename(self.legacy_notes_path, backup_path)
                print(f"KiNotes: Migrated notes.md to {os.path.basename(self.notes_path)}")
            except Exception as e:
                print(f"KiNotes: Error migrating notes: {e}")
    
    def _ensure_folder_exists(self):
        """Create .kinotes folder and backup subfolder if they don't exist."""
        try:
            if not os.path.exists(self.notes_dir):
                os.makedirs(self.notes_dir)
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)
        except Exception as e:
            print(f"KiNotes: Error creating folders: {e}")
    
    # ========== ATOMIC FILE OPERATIONS ==========
    
    def _atomic_write(self, filepath, content, is_json=False):
        """
        Write file atomically: write to temp file, then rename.
        This prevents data corruption if KiCad crashes mid-write.
        """
        try:
            self._ensure_folder_exists()
            
            # Create temp file in same directory (same filesystem for atomic rename)
            dir_name = os.path.dirname(filepath)
            fd, temp_path = tempfile.mkstemp(
                suffix='.tmp', 
                prefix='kinotes_', 
                dir=dir_name
            )
            
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    if is_json:
                        json.dump(content, f, indent=2)
                    else:
                        f.write(content)
                
                # On Windows, we need to remove target first
                if os.path.exists(filepath):
                    # Create backup before overwriting
                    self._create_backup(filepath)
                    os.remove(filepath)
                
                # Atomic rename
                os.rename(temp_path, filepath)
                return True
                
            except Exception as e:
                # Clean up temp file on failure
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
                raise e
                
        except Exception as e:
            print(f"KiNotes: Atomic write failed for {filepath}: {e}")
            return False
    
    def _create_backup(self, filepath):
        """Create a timestamped backup of a file."""
        try:
            if not os.path.exists(filepath):
                return
            
            filename = os.path.basename(filepath)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{timestamp}_{filename}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            shutil.copy2(filepath, backup_path)
            
            # Rotate old backups
            self._rotate_backups(filename)
            
        except Exception as e:
            print(f"KiNotes: Backup creation warning: {e}")
    
    def _rotate_backups(self, filename_suffix):
        """Keep only MAX_BACKUPS most recent backups for a file type."""
        try:
            if not os.path.exists(self.backup_dir):
                return
            
            # Find all backups for this file type
            backups = []
            for f in os.listdir(self.backup_dir):
                if f.endswith(filename_suffix):
                    full_path = os.path.join(self.backup_dir, f)
                    backups.append((os.path.getmtime(full_path), full_path))
            
            # Sort by modification time (newest first)
            backups.sort(reverse=True)
            
            # Remove old backups beyond MAX_BACKUPS
            for _, backup_path in backups[self.MAX_BACKUPS:]:
                try:
                    os.remove(backup_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"KiNotes: Backup rotation warning: {e}")
    
    def load(self):
        """Load notes from file. Returns empty string if not exists."""
        try:
            if os.path.exists(self.notes_path):
                with open(self.notes_path, "r", encoding="utf-8") as f:
                    return f.read()
            # Try to recover from backup if main file missing
            recovered = self._try_recover_from_backup(self.notes_path)
            if recovered:
                return recovered
            return self._get_default_template()
        except Exception as e:
            print(f"KiNotes: Error loading notes: {e}")
            # Try backup recovery on any load error
            recovered = self._try_recover_from_backup(self.notes_path)
            if recovered:
                return recovered
            return ""
    
    def _try_recover_from_backup(self, filepath):
        """Attempt to recover a file from its most recent backup."""
        try:
            filename = os.path.basename(filepath)
            if not os.path.exists(self.backup_dir):
                return None
            
            # Find most recent backup
            backups = []
            for f in os.listdir(self.backup_dir):
                if f.endswith(filename):
                    full_path = os.path.join(self.backup_dir, f)
                    backups.append((os.path.getmtime(full_path), full_path))
            
            if not backups:
                return None
            
            backups.sort(reverse=True)
            newest_backup = backups[0][1]
            
            with open(newest_backup, "r", encoding="utf-8") as f:
                content = f.read()
            
            print(f"KiNotes: Recovered from backup: {os.path.basename(newest_backup)}")
            return content
            
        except Exception as e:
            print(f"KiNotes: Backup recovery failed: {e}")
            return None
    
    def save(self, content):
        """Save notes to file using atomic write."""
        return self._atomic_write(self.notes_path, content, is_json=False)
    
    def _update_meta(self):
        """Update metadata file with last modified time."""
        try:
            meta = {}
            if os.path.exists(self.meta_path):
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            
            meta["last_modified"] = datetime.now().isoformat()
            meta["version"] = "1.0"
            
            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
        except Exception as e:
            print(f"KiNotes: Error updating meta: {e}")
    
    def _get_default_template(self):
        """Return default notes template."""
        project_name = os.path.basename(self.project_dir)
        return f"""# {project_name} - Design Notes

## Overview
<!-- Brief description of the PCB project -->

## Schematic Notes
<!-- Key circuit blocks, design rationale -->

## Layout Considerations
<!-- Layer stackup, impedance, keep-outs -->

## Component Notes
<!-- Click on designators like R1, C5, U3 to highlight on PCB -->

## Power Distribution
<!-- Power rails, decoupling strategy -->

## Signal Integrity
<!-- Critical nets, routing constraints -->

## References
<!-- Datasheets, application notes, calculations -->

---
*KiNotes - PCBtools.xyz*
"""
    
    def get_notes_path(self):
        """Return the full path to notes file."""
        return self.notes_path
    
    def get_project_name(self):
        """Return project directory name."""
        return os.path.basename(self.project_dir)
    
    # ========== Todo List Management ==========
    
    def load_todos(self):
        """Load todos from JSON file."""
        try:
            if os.path.exists(self.todos_path):
                with open(self.todos_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            # Try backup recovery
            recovered = self._try_recover_json_from_backup(self.todos_path)
            if recovered is not None:
                return recovered
            return []
        except Exception as e:
            print(f"KiNotes: Error loading todos: {e}")
            recovered = self._try_recover_json_from_backup(self.todos_path)
            if recovered is not None:
                return recovered
            return []
    
    def _try_recover_json_from_backup(self, filepath):
        """Attempt to recover a JSON file from backup."""
        try:
            filename = os.path.basename(filepath)
            if not os.path.exists(self.backup_dir):
                return None
            
            backups = []
            for f in os.listdir(self.backup_dir):
                if f.endswith(filename):
                    full_path = os.path.join(self.backup_dir, f)
                    backups.append((os.path.getmtime(full_path), full_path))
            
            if not backups:
                return None
            
            backups.sort(reverse=True)
            newest_backup = backups[0][1]
            
            with open(newest_backup, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            print(f"KiNotes: Recovered JSON from backup: {os.path.basename(newest_backup)}")
            return data
            
        except Exception as e:
            print(f"KiNotes: JSON backup recovery failed: {e}")
            return None
    
    def save_todos(self, todos):
        """Save todos to JSON file using atomic write."""
        return self._atomic_write(self.todos_path, todos, is_json=True)
    
    # ========== Version Log Management ==========
    
    def load_version_log(self):
        """Load version log from JSON file."""
        try:
            if os.path.exists(self.version_log_path):
                with open(self.version_log_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return self._get_default_version_log()
        except Exception as e:
            print(f"KiNotes: Error loading version log: {e}")
            recovered = self._try_recover_json_from_backup(self.version_log_path)
            if recovered is not None:
                return recovered
            return self._get_default_version_log()
    
    def save_version_log(self, version_log):
        """Save version log to JSON file using atomic write."""
        return self._atomic_write(self.version_log_path, version_log, is_json=True)
    
    def _get_default_version_log(self):
        """Return default version log structure."""
        return {
            "current_version": "0.1.0",
            "entries": []
        }
    
    def export_changelog(self):
        """Export version log to CHANGELOG.md format (Keep a Changelog standard)."""
        try:
            data = self.load_version_log()
            entries = data.get("entries", [])
            current_version = data.get("current_version", "0.1.0")
            
            lines = [
                f"# Changelog - {self.project_name}",
                "",
                "All notable changes to this project will be documented in this file.",
                "",
                "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),",
                "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
                "",
            ]
            
            # Group entries by version
            versions = {}
            for entry in entries:
                ver = entry.get("version", current_version)
                if ver not in versions:
                    versions[ver] = {"Added": [], "Changed": [], "Fixed": [], "Removed": [], "date": entry.get("date", "")}
                change_type = entry.get("type", "Changed")
                description = entry.get("description", "")
                if description:
                    versions[ver][change_type].append(description)
                # Keep the most recent date for this version
                if entry.get("date", "") > versions[ver]["date"]:
                    versions[ver]["date"] = entry.get("date", "")
            
            # Sort versions by semantic versioning (newest first)
            def version_key(v):
                parts = v.split(".")
                return tuple(int(p) if p.isdigit() else 0 for p in parts)
            
            sorted_versions = sorted(versions.keys(), key=version_key, reverse=True)
            
            for ver in sorted_versions:
                ver_data = versions[ver]
                date_str = ver_data.get("date", "")[:10] if ver_data.get("date") else ""
                lines.append(f"## [{ver}] - {date_str}")
                lines.append("")
                
                for change_type in ["Added", "Changed", "Fixed", "Removed"]:
                    items = ver_data.get(change_type, [])
                    if items:
                        lines.append(f"### {change_type}")
                        for item in items:
                            lines.append(f"- {item}")
                        lines.append("")
            
            lines.append("---")
            lines.append("*Generated by KiNotes - PCBtools.xyz*")
            
            return "\n".join(lines)
        except Exception as e:
            print(f"KiNotes: Error exporting changelog: {e}")
            return ""
    
    # ========== Settings Management ==========
    
    def load_settings(self):
        """
        Load settings with fallback: Local -> Global -> Defaults.
        
        Priority:
        1. Local project settings (.kinotes/settings.json)
        2. Global user settings (~/.kinotes/global_settings.json)
        3. Hardcoded defaults
        """
        try:
            # First try local project settings
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    print("[KiNotes] Loaded local project settings")
                    return settings
            
            # No local settings - try global settings fallback
            try:
                from .global_settings import get_global_settings_manager
                global_mgr = get_global_settings_manager()
                global_settings = global_mgr.load_settings()
                if global_settings:
                    print("[KiNotes] Using global settings (no local settings found)")
                    return global_settings
            except ImportError:
                pass  # global_settings module not available
            
            # No global settings either - use defaults
            print("[KiNotes] Using default settings (no local or global settings)")
            return self._get_default_settings()
        except Exception as e:
            print(f"KiNotes: Error loading settings: {e}")
            return self._get_default_settings()
    
    def save_settings(self, settings):
        """Save settings to local project JSON file using atomic write."""
        return self._atomic_write(self.settings_path, settings, is_json=True)
    
    def save_settings_globally(self, settings):
        """Save settings to global user location (~/.kinotes/)."""
        try:
            from .global_settings import get_global_settings_manager
            global_mgr = get_global_settings_manager()
            return global_mgr.save_settings(settings)
        except Exception as e:
            print(f"[KiNotes] Error saving global settings: {e}")
            return False
    
    def has_local_settings(self) -> bool:
        """Check if local project settings exist."""
        return os.path.exists(self.settings_path)
    
    def has_global_settings(self) -> bool:
        """Check if global settings exist."""
        try:
            from .global_settings import get_global_settings_manager
            return get_global_settings_manager().has_global_settings()
        except ImportError:
            return False
    
    def _get_default_settings(self):
        """Return default settings."""
        return {
            'autosave_interval': 5,
            'font_size': 11,
            'bom_exclude_dnp': True,
            'bom_exclude_fid': True,
            'bom_exclude_tp': True,
            'bom_group': 0,
            'sort_order': ['C', 'R', 'L', 'D', 'U', 'Y', 'X', 'F', 'SW', 'A', 'J', 'TP'],
            'blacklist': '',
            'blacklist_virtual': True,
            'blacklist_empty': False,
            'background_color': 'Snow Gray',
            'text_color': 'Carbon Black',
        }

