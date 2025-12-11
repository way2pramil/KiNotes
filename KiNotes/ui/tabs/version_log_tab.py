"""
KiNotes Version Log Tab - Changelog management.

Provides a mixin class for version log/changelog functionality.
"""
import wx
import wx.lib.scrolledpanel as scrolled
import datetime

from ..themes import hex_to_colour
from ..components import RoundedButton, Icons


class VersionLogTabMixin:
    """
    Mixin class providing version log tab functionality.
    
    Requires the host class to have:
    - self._theme: Current theme dict
    - self._dark_mode: bool
    - self._current_version: str
    - self._version_log_items: list
    - self._version_log_id_counter: int
    - self.notes_manager: NotesManager instance
    - self._modified: bool
    """
    
    def _create_version_log_tab(self, parent):
        """Create Version Log tab with changelog entries."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar
        toolbar = wx.Panel(panel)
        toolbar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        toolbar.SetMinSize((-1, 60))
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tb_sizer.AddSpacer(16)
        
        # Version display/edit
        ver_label = wx.StaticText(toolbar, label="Version:")
        ver_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        ver_label.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        tb_sizer.Add(ver_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        self.version_input = wx.TextCtrl(toolbar, value=self._current_version, size=(100, 32), style=wx.BORDER_SIMPLE)
        self.version_input.SetBackgroundColour(hex_to_colour(self._theme["bg_button"]))
        self.version_input.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        self.version_input.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.version_input.Bind(wx.EVT_TEXT, self._on_version_change)
        tb_sizer.Add(self.version_input, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
        
        # Add entry button
        self.add_log_btn = RoundedButton(
            toolbar, label="+ Add Entry", icon="", size=(130, 42),
            bg_color=self._theme["accent_green"], fg_color="#FFFFFF",
            corner_radius=10, font_size=11, font_weight=wx.FONTWEIGHT_BOLD
        )
        self.add_log_btn.Bind_Click(self._on_add_version_log)
        tb_sizer.Add(self.add_log_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        # Export changelog button
        self.export_changelog_btn = RoundedButton(
            toolbar, label="Export", icon="", size=(100, 42),
            bg_color=self._theme["bg_button"], fg_color=self._theme["text_primary"],
            corner_radius=10, font_size=11, font_weight=wx.FONTWEIGHT_NORMAL
        )
        self.export_changelog_btn.Bind_Click(self._on_export_changelog)
        tb_sizer.Add(self.export_changelog_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        tb_sizer.AddStretchSpacer()
        
        # Entry counter
        self.version_log_count = wx.StaticText(toolbar, label="0 entries")
        self.version_log_count.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        self.version_log_count.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        tb_sizer.Add(self.version_log_count, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 20)
        
        toolbar.SetSizer(tb_sizer)
        sizer.Add(toolbar, 0, wx.EXPAND)
        
        # Scroll area for entries
        self.version_log_scroll = scrolled.ScrolledPanel(panel)
        self.version_log_scroll.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        self.version_log_scroll.SetupScrolling(scroll_x=False)
        
        self.version_log_sizer = wx.BoxSizer(wx.VERTICAL)
        self.version_log_sizer.AddSpacer(12)
        self.version_log_scroll.SetSizer(self.version_log_sizer)
        sizer.Add(self.version_log_scroll, 1, wx.EXPAND | wx.ALL, 12)
        
        panel.SetSizer(sizer)
        return panel
    
    def _add_version_log_item(self, version="", change_type="Added", description="", date=""):
        """Add a version log entry."""
        item_id = self._version_log_id_counter
        self._version_log_id_counter += 1
        
        if not date:
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if not version:
            version = self._current_version
        
        # Container panel
        container = wx.Panel(self.version_log_scroll)
        if self._dark_mode:
            container_bg = "#3A3A3A"
            input_bg = "#4A4A4A"
        else:
            container_bg = "#FAFAFA"
            input_bg = "#FFFFFF"
        container.SetBackgroundColour(hex_to_colour(container_bg))
        container_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Row 1: Type selector + Description
        row1 = wx.Panel(container)
        row1.SetBackgroundColour(hex_to_colour(container_bg))
        row1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Change type dropdown (Keep a Changelog standard)
        type_choice = wx.Choice(row1, choices=["Added", "Changed", "Fixed", "Removed"])
        type_idx = {"Added": 0, "Changed": 1, "Fixed": 2, "Removed": 3}.get(change_type, 0)
        type_choice.SetSelection(type_idx)
        type_choice.SetMinSize((100, 32))
        type_choice.Bind(wx.EVT_CHOICE, lambda e, iid=item_id: self._on_log_type_change(iid))
        row1_sizer.Add(type_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 12)
        
        # Description input
        desc_input = wx.TextCtrl(row1, value=description, style=wx.BORDER_SIMPLE | wx.TE_PROCESS_ENTER)
        desc_input.SetBackgroundColour(hex_to_colour(input_bg))
        desc_input.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        desc_input.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        desc_input.SetHint("Describe the change...")
        desc_input.Bind(wx.EVT_TEXT, lambda e, iid=item_id: self._on_log_desc_change(iid))
        desc_input.Bind(wx.EVT_TEXT_ENTER, lambda e: self._on_add_version_log(None))
        row1_sizer.Add(desc_input, 1, wx.EXPAND | wx.ALL, 8)
        
        # Version label for this entry
        ver_label = wx.StaticText(row1, label=f"v{version}")
        ver_label.SetForegroundColour(hex_to_colour(self._theme["accent_blue"]))
        ver_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        ver_label.SetMinSize((70, -1))
        row1_sizer.Add(ver_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        # Date label
        date_label = wx.StaticText(row1, label=date[:10])
        date_label.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        date_label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        date_label.SetMinSize((80, -1))
        row1_sizer.Add(date_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        # Delete button
        del_btn = wx.Button(row1, label=Icons.DELETE, size=(40, 40), style=wx.BORDER_NONE)
        del_btn.SetBackgroundColour(hex_to_colour(container_bg))
        del_btn.SetForegroundColour(hex_to_colour(self._theme["accent_red"]))
        del_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        del_btn.Bind(wx.EVT_BUTTON, lambda e, iid=item_id: self._on_delete_version_log(iid))
        row1_sizer.Add(del_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        row1.SetSizer(row1_sizer)
        container_sizer.Add(row1, 0, wx.EXPAND)
        container.SetSizer(container_sizer)
        
        self._version_log_items.append({
            "id": item_id,
            "container": container,
            "type_choice": type_choice,
            "desc_input": desc_input,
            "ver_label": ver_label,
            "date_label": date_label,
            "version": version,
            "date": date
        })
        
        self.version_log_sizer.Add(container, 0, wx.EXPAND | wx.BOTTOM, 8)
        self.version_log_scroll.FitInside()
        self.version_log_scroll.Layout()
        self._update_version_log_count()
        return desc_input
    
    def _on_add_version_log(self, event):
        """Add new version log entry."""
        desc_input = self._add_version_log_item(version=self._current_version)
        desc_input.SetFocus()
        self._save_version_log()
    
    def _on_version_change(self, event):
        """Handle version number change."""
        self._current_version = self.version_input.GetValue()
        self._save_version_log()
    
    def _on_log_type_change(self, item_id):
        """Handle change type selection."""
        self._save_version_log()
    
    def _on_log_desc_change(self, item_id):
        """Handle description text change."""
        self._modified = True
    
    def _on_delete_version_log(self, item_id):
        """Delete a version log entry."""
        for item in self._version_log_items:
            if item["id"] == item_id:
                item["container"].Destroy()
                self._version_log_items.remove(item)
                break
        self.version_log_scroll.FitInside()
        self.version_log_scroll.Layout()
        self._update_version_log_count()
        self._save_version_log()
    
    def _update_version_log_count(self):
        """Update the entry counter."""
        count = len(self._version_log_items)
        self.version_log_count.SetLabel(f"{count} {'entry' if count == 1 else 'entries'}")
    
    def _save_version_log(self):
        """Save version log to JSON."""
        try:
            entries = []
            for item in self._version_log_items:
                type_idx = item["type_choice"].GetSelection()
                change_type = ["Added", "Changed", "Fixed", "Removed"][type_idx]
                entries.append({
                    "version": item["version"],
                    "type": change_type,
                    "description": item["desc_input"].GetValue(),
                    "date": item["date"]
                })
            data = {
                "current_version": self._current_version,
                "entries": entries
            }
            self.notes_manager.save_version_log(data)
        except Exception as e:
            print(f"[KiNotes] Version log save warning: {e}")
    
    def _load_version_log(self):
        """Load version log from JSON."""
        try:
            data = self.notes_manager.load_version_log()
            self._current_version = data.get("current_version", "0.1.0")
            if hasattr(self, 'version_input'):
                self.version_input.SetValue(self._current_version)
            
            entries = data.get("entries", [])
            for entry in entries:
                self._add_version_log_item(
                    version=entry.get("version", self._current_version),
                    change_type=entry.get("type", "Added"),
                    description=entry.get("description", ""),
                    date=entry.get("date", "")
                )
        except Exception as e:
            print(f"[KiNotes] Version log load warning: {e}")
    
    def _on_export_changelog(self, event):
        """Export changelog to CHANGELOG.md file."""
        import os
        try:
            # First save current state
            self._save_version_log()
            
            # Generate changelog content
            changelog = self.notes_manager.export_changelog()
            if not changelog:
                wx.MessageBox("No changelog entries to export.", "Export Changelog", wx.OK | wx.ICON_INFORMATION)
                return
            
            # Get project directory
            project_dir = self.notes_manager.project_dir
            changelog_path = os.path.join(project_dir, ".kinotes", "CHANGELOG.md")
            
            # Write to file
            with open(changelog_path, "w", encoding="utf-8") as f:
                f.write(changelog)
            
            wx.MessageBox(f"Changelog exported to:\n{changelog_path}", "Export Changelog", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Error exporting changelog: {str(e)}", "Export Error", wx.OK | wx.ICON_ERROR)
