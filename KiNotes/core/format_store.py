"""
KiNotes Format Store - Preserves original markdown for round-trip fidelity
==========================================================================
Stores the original markdown source alongside the visual editor to ensure
perfect round-trip preservation of formatting. The visual editor displays
the content, but saves come from this store (with modifications tracked).

This solves the fundamental problem: RichTextCtrl → Markdown conversion
is lossy and unreliable. Instead, we keep the source markdown and only
update specific parts when the user makes changes.

Author: KiNotes Team (pcbtools.xyz)
License: Apache-2.0
"""

import re
from typing import Optional, List, Tuple


class FormatStore:
    """
    Stores original markdown and tracks changes for perfect round-trip.
    
    Usage:
        store = FormatStore()
        store.set_source(markdown_text)  # When loading
        markdown_out = store.get_source()  # When saving
        
        # When user edits, update specific parts:
        store.update_line(line_num, new_text)
        store.insert_image(line_num, image_path)
    """
    
    def __init__(self):
        self._lines: List[str] = []
        self._modified = False
    
    def set_source(self, markdown_text: str):
        """Set the original markdown source."""
        if markdown_text:
            self._lines = markdown_text.split('\n')
        else:
            self._lines = []
        self._modified = False
    
    def get_source(self) -> str:
        """Get the markdown source."""
        return '\n'.join(self._lines)
    
    def is_modified(self) -> bool:
        """Check if content has been modified."""
        return self._modified
    
    def get_line_count(self) -> int:
        """Get number of lines."""
        return len(self._lines)
    
    def get_line(self, line_num: int) -> Optional[str]:
        """Get a specific line (0-indexed)."""
        if 0 <= line_num < len(self._lines):
            return self._lines[line_num]
        return None
    
    def update_line(self, line_num: int, new_text: str):
        """Update a specific line."""
        if 0 <= line_num < len(self._lines):
            self._lines[line_num] = new_text
            self._modified = True
    
    def insert_line(self, line_num: int, text: str):
        """Insert a new line at position."""
        if line_num <= len(self._lines):
            self._lines.insert(line_num, text)
            self._modified = True
    
    def delete_line(self, line_num: int):
        """Delete a line."""
        if 0 <= line_num < len(self._lines):
            del self._lines[line_num]
            self._modified = True
    
    def append_line(self, text: str):
        """Append a line at the end."""
        self._lines.append(text)
        self._modified = True
    
    def insert_image(self, image_path: str, after_line: int = -1):
        """Insert an image line."""
        image_md = f"![Image]({image_path})"
        if after_line < 0 or after_line >= len(self._lines):
            self._lines.append(image_md)
        else:
            self._lines.insert(after_line + 1, image_md)
        self._modified = True
    
    def replace_all(self, new_markdown: str):
        """Replace all content (for full editor changes)."""
        self._lines = new_markdown.split('\n') if new_markdown else []
        self._modified = True
    
    def sync_from_plain_text(self, plain_text: str, visual_lines: List[dict]):
        """
        Sync format store from plain text editor content.
        
        This is called when we need to reconcile editor changes with
        the stored markdown. It preserves formatting markers where
        the text content matches.
        
        Args:
            plain_text: Plain text from editor (no formatting)
            visual_lines: List of dicts with line info from visual editor
        """
        new_lines = plain_text.split('\n')
        
        # Simple case: same number of lines, update content but keep format
        if len(new_lines) == len(self._lines):
            for i, new_line in enumerate(new_lines):
                old_line = self._lines[i]
                # If it's an image line, preserve it
                if old_line.strip().startswith('![') and '](' in old_line:
                    continue
                # If it's a heading, preserve the # prefix
                if old_line.strip().startswith('#'):
                    heading_match = re.match(r'^(#{1,3})\s*', old_line)
                    if heading_match:
                        prefix = heading_match.group(1)
                        # Strip formatting from new line and add heading prefix
                        clean_new = self._strip_formatting(new_line)
                        self._lines[i] = f"{prefix} {clean_new}"
                        continue
                # Otherwise use the new content
                self._lines[i] = new_line
        else:
            # Different line count - just replace all (loses some formatting)
            self._lines = new_lines
        
        self._modified = True
    
    def _strip_formatting(self, text: str) -> str:
        """Remove markdown formatting markers from text."""
        # Remove bold/italic markers
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        # Remove heading markers
        text = re.sub(r'^#{1,6}\s*', '', text)
        return text


# Singleton instance for the current editor session
_current_store: Optional[FormatStore] = None


def get_format_store() -> FormatStore:
    """Get the current format store (creates if needed)."""
    global _current_store
    if _current_store is None:
        _current_store = FormatStore()
    return _current_store


def reset_format_store():
    """Reset the format store (call when closing editor)."""
    global _current_store
    _current_store = None
