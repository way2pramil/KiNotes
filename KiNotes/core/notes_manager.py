"""
KiNotes Notes Manager - Load/save notes, todos, settings to .kinotes folder
"""
import os
import re
import json
from datetime import datetime


class NotesManager:
    """Manages loading and saving notes, todos, and settings for a KiCad project."""
    
    NOTES_FOLDER = ".kinotes"
    LEGACY_NOTES_FILE = "notes.md"  # Old filename for migration
    TODOS_FILE = "todos.json"
    SETTINGS_FILE = "settings.json"
    META_FILE = "meta.json"
    
    def __init__(self, project_dir):
        """Initialize with project directory path."""
        self.project_dir = project_dir
        self.project_name = self._get_project_name()
        self.notes_dir = os.path.join(project_dir, self.NOTES_FOLDER)
        self.notes_path = os.path.join(self.notes_dir, f"KiNotes_{self.project_name}.md")
        self.legacy_notes_path = os.path.join(self.notes_dir, self.LEGACY_NOTES_FILE)
        self.todos_path = os.path.join(self.notes_dir, self.TODOS_FILE)
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
        """Create .kinotes folder if it doesn't exist."""
        if not os.path.exists(self.notes_dir):
            os.makedirs(self.notes_dir)
    
    def load(self):
        """Load notes from file. Returns empty string if not exists."""
        try:
            if os.path.exists(self.notes_path):
                with open(self.notes_path, "r", encoding="utf-8") as f:
                    return f.read()
            return self._get_default_template()
        except Exception as e:
            print(f"KiNotes: Error loading notes: {e}")
            return ""
    
    def save(self, content):
        """Save notes to file."""
        try:
            self._ensure_folder_exists()
            with open(self.notes_path, "w", encoding="utf-8") as f:
                f.write(content)
            self._update_meta()
            return True
        except Exception as e:
            print(f"KiNotes: Error saving notes: {e}")
            return False
    
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
<!-- Add your project overview here -->

## To-Do
- [ ] Design review
- [ ] Check footprints
- [ ] Verify netlist

## Design Decisions
<!-- Document important design choices -->

## Component Notes
<!-- Use @R1 @U3 syntax to link components -->

## References
<!-- Add datasheet links, calculations, etc. -->

---
*Notes created by KiNotes - PCBtools.xyz*
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
            return []
        except Exception as e:
            print(f"KiNotes: Error loading todos: {e}")
            return []
    
    def save_todos(self, todos):
        """Save todos to JSON file."""
        try:
            self._ensure_folder_exists()
            with open(self.todos_path, "w", encoding="utf-8") as f:
                json.dump(todos, f, indent=2)
            return True
        except Exception as e:
            print(f"KiNotes: Error saving todos: {e}")
            return False
    
    # ========== Settings Management ==========
    
    def load_settings(self):
        """Load settings from JSON file."""
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return self._get_default_settings()
        except Exception as e:
            print(f"KiNotes: Error loading settings: {e}")
            return self._get_default_settings()
    
    def save_settings(self, settings):
        """Save settings to JSON file."""
        try:
            self._ensure_folder_exists()
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"KiNotes: Error saving settings: {e}")
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

