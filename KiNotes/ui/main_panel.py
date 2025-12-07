"""
KiNotes Main Panel - The primary notes editor UI
"""
import wx
import wx.richtext as rt
import re
import os


class KiNotesMainPanel(wx.Panel):
    """Main notes panel with iOS-inspired styling and full features."""
    
    # Regex for designator links: @R1, @U3, @C5, etc.
    DESIGNATOR_PATTERN = re.compile(r'@([A-Z]+\d+[A-Z]?)', re.IGNORECASE)
    
    # Regex for todo items: - [ ] or - [x]
    TODO_PATTERN = re.compile(r'^(\s*)-\s*\[([ xX])\]\s*(.*)$', re.MULTILINE)
    
    def __init__(self, parent, notes_manager, designator_linker, metadata_extractor, pdf_exporter):
        super().__init__(parent)
        
        self.notes_manager = notes_manager
        self.designator_linker = designator_linker
        self.metadata_extractor = metadata_extractor
        self.pdf_exporter = pdf_exporter
        
        self._auto_save_timer = None
        self._modified = False
        
        self._init_ui()
        self._load_notes()
        self._start_auto_save_timer()
    
    def _init_ui(self):
        """Initialize the main panel UI."""
        from .styles import KiNotesStyles as Styles
        from .toolbar import KiNotesToolbar
        
        Styles.apply_panel_style(self)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar
        self.toolbar = KiNotesToolbar(
            self,
            on_save=self._on_save,
            on_export_pdf=self._on_export_pdf,
            on_import_metadata=self._on_import_metadata,
            on_bom_config=self._on_bom_config  # IBOM-style dialog
        )
        main_sizer.Add(self.toolbar, 0, wx.EXPAND)
        
        # Separator line
        separator = wx.Panel(self, size=(-1, 1))
        separator.SetBackgroundColour(Styles.get_border_color())
        main_sizer.Add(separator, 0, wx.EXPAND)
        
        # Notes editor - using wx.TextCtrl with rich features
        self.text_editor = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_RICH2 | wx.TE_PROCESS_TAB | wx.BORDER_NONE
        )
        Styles.apply_text_style(self.text_editor)
        
        # Set placeholder text style
        self.text_editor.SetHint("Start typing your notes here...\n\nTips:\n• Use - [ ] for todo items\n• Use @R1 to link components\n• Click Import to add board metadata")
        
        main_sizer.Add(self.text_editor, 1, wx.EXPAND | wx.ALL, Styles.PADDING_NORMAL)
        
        # Footer with branding
        footer = self._create_footer()
        main_sizer.Add(footer, 0, wx.EXPAND)
        
        self.SetSizer(main_sizer)
        
        # Bind events
        self.text_editor.Bind(wx.EVT_TEXT, self._on_text_changed)
        self.text_editor.Bind(wx.EVT_LEFT_DOWN, self._on_text_click)
        self.text_editor.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
    
    def _create_footer(self):
        """Create footer panel with PCBtools branding."""
        from .styles import KiNotesStyles as Styles
        
        footer = wx.Panel(self, size=(-1, 24))
        footer.SetBackgroundColour(Styles.get_toolbar_bg_color())
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Status text (left)
        self.status_label = wx.StaticText(footer, label="Ready")
        self.status_label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.status_label.SetForegroundColour(Styles.get_text_secondary_color())
        sizer.Add(self.status_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, Styles.PADDING_NORMAL)
        
        sizer.AddStretchSpacer(1)
        
        # Branding (right)
        branding = wx.StaticText(footer, label="Built with ❤️ by PCBtools.xyz")
        branding.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        branding.SetForegroundColour(Styles.get_text_secondary_color())
        sizer.Add(branding, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, Styles.PADDING_NORMAL)
        
        footer.SetSizer(sizer)
        return footer
    
    def _start_auto_save_timer(self):
        """Start timer for periodic auto-save."""
        self._auto_save_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_auto_save_timer, self._auto_save_timer)
        self._auto_save_timer.Start(5000)  # Auto-save every 5 seconds if modified
    
    def _load_notes(self):
        """Load notes from file."""
        try:
            content = self.notes_manager.load()
            if content:
                self.text_editor.SetValue(content)
                self._modified = False
                self._update_status("Loaded")
        except Exception as e:
            self._update_status(f"Load error: {str(e)}")
    
    def _save_notes(self):
        """Save notes to file."""
        try:
            content = self.text_editor.GetValue()
            self.notes_manager.save(content)
            self._modified = False
            self._update_status("Saved ✓")
        except Exception as e:
            self._update_status(f"Save error: {str(e)}")
    
    def _update_status(self, message):
        """Update status bar message."""
        self.status_label.SetLabel(message)
        # Reset to "Ready" after 3 seconds
        wx.CallLater(3000, lambda: self.status_label.SetLabel("Ready") if self.status_label else None)
    
    def _on_text_changed(self, event):
        """Handle text changes - mark as modified."""
        self._modified = True
        self._save_notes()  # Auto-save on every change
        event.Skip()
    
    def _on_auto_save_timer(self, event):
        """Periodic auto-save timer callback."""
        if self._modified:
            self._save_notes()
    
    def _on_save(self):
        """Manual save button callback."""
        self._save_notes()
        wx.MessageBox("Notes saved!", "KiNotes", wx.OK | wx.ICON_INFORMATION)
    
    def _on_export_pdf(self):
        """Export notes to PDF."""
        try:
            content = self.text_editor.GetValue()
            filepath = self.pdf_exporter.export(content)
            if filepath:
                self._update_status(f"Exported to {os.path.basename(filepath)}")
                wx.MessageBox(f"Notes exported to:\n{filepath}", "Export Complete", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Export failed: {str(e)}", "Export Error", wx.OK | wx.ICON_ERROR)
    
    def _on_import_metadata(self, meta_type):
        """Import metadata from PCB."""
        try:
            metadata_text = self.metadata_extractor.extract(meta_type)
            if metadata_text:
                # Insert at cursor position
                pos = self.text_editor.GetInsertionPoint()
                current_text = self.text_editor.GetValue()
                new_text = current_text[:pos] + "\n" + metadata_text + "\n" + current_text[pos:]
                self.text_editor.SetValue(new_text)
                self.text_editor.SetInsertionPoint(pos + len(metadata_text) + 2)
                self._update_status(f"Imported {meta_type}")
        except Exception as e:
            wx.MessageBox(f"Import failed: {str(e)}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _on_bom_config(self):
        """Show IBOM-style BOM configuration dialog."""
        try:
            from .bom_dialog import show_bom_dialog
            
            bom_text = show_bom_dialog(self)
            if bom_text:
                # Insert at cursor position
                pos = self.text_editor.GetInsertionPoint()
                current_text = self.text_editor.GetValue()
                new_text = current_text[:pos] + "\n" + bom_text + "\n" + current_text[pos:]
                self.text_editor.SetValue(new_text)
                self.text_editor.SetInsertionPoint(pos + len(bom_text) + 2)
                self._update_status("BOM inserted")
        except Exception as e:
            wx.MessageBox(f"BOM generation failed: {str(e)}", "BOM Error", wx.OK | wx.ICON_ERROR)
    
    def _on_text_click(self, event):
        """Handle clicks in text - check for @designator links."""
        # Get click position
        pos = self.text_editor.HitTestPos(event.GetPosition())[1]
        if pos >= 0:
            # Get the word at click position
            text = self.text_editor.GetValue()
            word = self._get_word_at_position(text, pos)
            
            # Check if it's a designator link
            if word.startswith('@'):
                designator = word[1:]  # Remove @ prefix
                self._highlight_component(designator)
                return
        
        event.Skip()
    
    def _on_key_down(self, event):
        """Handle key events for todo checkbox toggling."""
        key_code = event.GetKeyCode()
        
        # Check for Enter key on a checkbox line
        if key_code == wx.WXK_RETURN:
            line_num = self.text_editor.GetValue()[:self.text_editor.GetInsertionPoint()].count('\n')
            lines = self.text_editor.GetValue().split('\n')
            if line_num < len(lines):
                current_line = lines[line_num]
                # If current line has checkbox, add new checkbox on next line
                if re.match(r'^\s*-\s*\[[ xX]\]', current_line):
                    indent = re.match(r'^(\s*)', current_line).group(1)
                    self._insert_at_cursor(f"\n{indent}- [ ] ")
                    return
        
        # Check for Ctrl+Enter to toggle checkbox
        if key_code == wx.WXK_RETURN and event.ControlDown():
            self._toggle_current_checkbox()
            return
        
        event.Skip()
    
    def _get_word_at_position(self, text, pos):
        """Get the word at the given position in text."""
        if pos < 0 or pos >= len(text):
            return ""
        
        # Find word boundaries
        start = pos
        end = pos
        
        while start > 0 and (text[start-1].isalnum() or text[start-1] in '@_'):
            start -= 1
        while end < len(text) and (text[end].isalnum() or text[end] in '@_'):
            end += 1
        
        return text[start:end]
    
    def _highlight_component(self, designator):
        """Highlight component on PCB."""
        try:
            success = self.designator_linker.highlight(designator)
            if success:
                self._update_status(f"Highlighted {designator}")
            else:
                self._update_status(f"Component {designator} not found")
        except Exception as e:
            self._update_status(f"Error: {str(e)}")
    
    def _toggle_current_checkbox(self):
        """Toggle checkbox on current line."""
        pos = self.text_editor.GetInsertionPoint()
        text = self.text_editor.GetValue()
        lines = text.split('\n')
        
        line_num = text[:pos].count('\n')
        if line_num < len(lines):
            line = lines[line_num]
            match = re.match(r'^(\s*-\s*\[)([ xX])(\].*)$', line)
            if match:
                # Toggle checkbox
                new_state = ' ' if match.group(2).lower() == 'x' else 'x'
                lines[line_num] = match.group(1) + new_state + match.group(3)
                self.text_editor.SetValue('\n'.join(lines))
                self.text_editor.SetInsertionPoint(pos)
    
    def _insert_at_cursor(self, text):
        """Insert text at current cursor position."""
        pos = self.text_editor.GetInsertionPoint()
        current = self.text_editor.GetValue()
        new_text = current[:pos] + text + current[pos:]
        self.text_editor.SetValue(new_text)
        self.text_editor.SetInsertionPoint(pos + len(text))
    
    def force_save(self):
        """Force save notes (called on close/deactivate)."""
        self._save_notes()
    
    def cleanup(self):
        """Cleanup resources."""
        if self._auto_save_timer:
            self._auto_save_timer.Stop()
        self._save_notes()
