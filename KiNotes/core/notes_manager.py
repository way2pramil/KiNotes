"""
KiNotes Notes Manager - Load/save notes to .kinotes folder
"""
import os
import json
from datetime import datetime


class NotesManager:
    """Manages loading and saving notes for a KiCad project."""
    
    NOTES_FOLDER = ".kinotes"
    NOTES_FILE = "notes.md"
    META_FILE = "meta.json"
    
    def __init__(self, project_dir):
        """Initialize with project directory path."""
        self.project_dir = project_dir
        self.notes_dir = os.path.join(project_dir, self.NOTES_FOLDER)
        self.notes_path = os.path.join(self.notes_dir, self.NOTES_FILE)
        self.meta_path = os.path.join(self.notes_dir, self.META_FILE)
        
        self._ensure_folder_exists()
    
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
