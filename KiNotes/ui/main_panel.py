"""
KiNotes Main Panel - Multi-tab UI with proper wxPython Notebook
"""
import wx
import wx.lib.scrolledpanel as scrolled
import re
import os
import json


class KiNotesMainPanel(wx.Panel):
    """
    Main KiNotes panel with multi-tab interface.
    Tabs: Notes | Todo List | Settings
    """
    
    # Minimum sizes
    MIN_WIDTH = 380
    MIN_HEIGHT = 500
    
    def __init__(self, parent, notes_manager, designator_linker, metadata_extractor, pdf_exporter):
        super().__init__(parent)
        
        self.notes_manager = notes_manager
        self.designator_linker = designator_linker
        self.metadata_extractor = metadata_extractor
        self.pdf_exporter = pdf_exporter
        
        self._auto_save_timer = None
        self._modified = False
        self._todo_items = []
        self._todo_id_counter = 0
        self._current_tab = 0
        
        self.SetMinSize((self.MIN_WIDTH, self.MIN_HEIGHT))
        self.SetBackgroundColour(wx.Colour(248, 249, 250))
        
        self._init_ui()
        self._load_all_data()
        self._start_auto_save_timer()
    
    def _init_ui(self):
        """Initialize the multi-tab UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header with title
        header = self._create_header()
        main_sizer.Add(header, 0, wx.EXPAND)
        
        # Tab bar (custom implementation for reliability)
        self.tab_bar = self._create_tab_bar()
        main_sizer.Add(self.tab_bar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        
        # Content panels (stacked, show one at a time)
        self.content_panel = wx.Panel(self)
        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create tab content panels
        self.notes_panel = self._create_notes_panel(self.content_panel)
        self.todo_panel = self._create_todo_panel(self.content_panel)
        self.settings_panel = self._create_settings_panel(self.content_panel)
        
        self.content_sizer.Add(self.notes_panel, 1, wx.EXPAND)
        self.content_sizer.Add(self.todo_panel, 1, wx.EXPAND)
        self.content_sizer.Add(self.settings_panel, 1, wx.EXPAND)
        
        self.content_panel.SetSizer(self.content_sizer)
        main_sizer.Add(self.content_panel, 1, wx.EXPAND | wx.ALL, 8)
        
        # Initially show Notes tab
        self._show_tab(0)
        
        # Footer
        footer = self._create_footer()
        main_sizer.Add(footer, 0, wx.EXPAND)
        
        self.SetSizer(main_sizer)
    
    def _create_header(self):
        """Create header with KiNotes title."""
        header = wx.Panel(self)
        header.SetBackgroundColour(wx.Colour(255, 255, 255))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Logo/Title
        title = wx.StaticText(header, label="KiNotes")
        title.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        title.SetForegroundColour(wx.Colour(33, 37, 41))
        sizer.Add(title, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 12)
        
        sizer.AddStretchSpacer()
        
        header.SetSizer(sizer)
        return header
    
    def _create_tab_bar(self):
        """Create custom tab bar for reliability."""
        tab_bar = wx.Panel(self)
        tab_bar.SetBackgroundColour(wx.Colour(248, 249, 250))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.tab_buttons = []
        tabs = [
            ("📝 Notes", 0),
            ("☑️ Todo", 1),
            ("⚙️ Settings", 2),
        ]
        
        for label, idx in tabs:
            btn = wx.Button(tab_bar, label=label, size=(-1, 32))
            btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            btn.Bind(wx.EVT_BUTTON, lambda e, i=idx: self._on_tab_click(i))
            self.tab_buttons.append(btn)
            sizer.Add(btn, 1, wx.EXPAND | wx.ALL, 2)
        
        tab_bar.SetSizer(sizer)
        return tab_bar
    
    def _on_tab_click(self, idx):
        """Handle tab button click."""
        self._show_tab(idx)
    
    def _show_tab(self, idx):
        """Show the selected tab panel."""
        self._current_tab = idx
        
        # Update button styles
        for i, btn in enumerate(self.tab_buttons):
            if i == idx:
                btn.SetBackgroundColour(wx.Colour(0, 123, 255))
                btn.SetForegroundColour(wx.Colour(255, 255, 255))
            else:
                btn.SetBackgroundColour(wx.Colour(233, 236, 239))
                btn.SetForegroundColour(wx.Colour(73, 80, 87))
            btn.Refresh()
        
        # Hide all panels first
        self.notes_panel.Hide()
        self.todo_panel.Hide()
        self.settings_panel.Hide()
        
        # Show selected panel
        if idx == 0:
            self.notes_panel.Show()
        elif idx == 1:
            self.todo_panel.Show()
            # Refresh todo scroll
            self.todo_scroll.FitInside()
        elif idx == 2:
            self.settings_panel.Show()
            self.settings_panel.FitInside()
        
        # Force layout update
        self.content_panel.Layout()
        self.content_sizer.Layout()
        self.Layout()
        self.Refresh()
        self.Update()
    
    def _create_notes_panel(self, parent):
        """Create the Notes editor panel."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar
        toolbar = wx.Panel(panel)
        toolbar.SetBackgroundColour(wx.Colour(248, 249, 250))
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Import button with dropdown
        self.import_btn = wx.Button(toolbar, label="📥 Import", size=(85, 30))
        self.import_btn.SetToolTip("Import board metadata")
        self.import_btn.Bind(wx.EVT_BUTTON, self._on_import_click)
        tb_sizer.Add(self.import_btn, 0, wx.ALL, 4)
        
        # PDF export button
        pdf_btn = wx.Button(toolbar, label="📄 PDF", size=(70, 30))
        pdf_btn.SetToolTip("Export to PDF")
        pdf_btn.Bind(wx.EVT_BUTTON, lambda e: self._on_export_pdf())
        tb_sizer.Add(pdf_btn, 0, wx.ALL, 4)
        
        tb_sizer.AddStretchSpacer()
        
        # Save button
        save_btn = wx.Button(toolbar, label="💾 Save", size=(70, 30))
        save_btn.SetToolTip("Save notes")
        save_btn.Bind(wx.EVT_BUTTON, lambda e: self._on_manual_save())
        tb_sizer.Add(save_btn, 0, wx.ALL, 4)
        
        toolbar.SetSizer(tb_sizer)
        sizer.Add(toolbar, 0, wx.EXPAND)
        
        # Separator
        sep = wx.StaticLine(panel)
        sizer.Add(sep, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        
        # Text editor with padding
        editor_panel = wx.Panel(panel)
        editor_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        editor_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.text_editor = wx.TextCtrl(
            editor_panel,
            style=wx.TE_MULTILINE | wx.TE_RICH2 | wx.TE_PROCESS_TAB | wx.BORDER_SIMPLE
        )
        self.text_editor.SetFont(wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.text_editor.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.text_editor.Bind(wx.EVT_TEXT, self._on_text_changed)
        self.text_editor.Bind(wx.EVT_LEFT_DOWN, self._on_text_click)
        
        editor_sizer.Add(self.text_editor, 1, wx.EXPAND | wx.ALL, 8)
        editor_panel.SetSizer(editor_sizer)
        
        sizer.Add(editor_panel, 1, wx.EXPAND)
        
        panel.SetSizer(sizer)
        return panel
    
    def _create_todo_panel(self, parent):
        """Create the Todo List panel with interactive checkboxes."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar
        toolbar = wx.Panel(panel)
        toolbar.SetBackgroundColour(wx.Colour(248, 249, 250))
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Add task button
        add_btn = wx.Button(toolbar, label="➕ Add Task", size=(95, 30))
        add_btn.Bind(wx.EVT_BUTTON, self._on_add_todo)
        tb_sizer.Add(add_btn, 0, wx.ALL, 4)
        
        # Clear done button
        clear_btn = wx.Button(toolbar, label="🗑️ Clear Done", size=(105, 30))
        clear_btn.Bind(wx.EVT_BUTTON, self._on_clear_done_todos)
        tb_sizer.Add(clear_btn, 0, wx.ALL, 4)
        
        tb_sizer.AddStretchSpacer()
        
        # Progress label
        self.todo_progress = wx.StaticText(toolbar, label="0/0 done")
        self.todo_progress.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.todo_progress.SetForegroundColour(wx.Colour(108, 117, 125))
        tb_sizer.Add(self.todo_progress, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        toolbar.SetSizer(tb_sizer)
        sizer.Add(toolbar, 0, wx.EXPAND)
        
        # Separator
        sep = wx.StaticLine(panel)
        sizer.Add(sep, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        
        # Scrollable todo list
        self.todo_scroll = scrolled.ScrolledPanel(panel)
        self.todo_scroll.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.todo_scroll.SetupScrolling(scroll_x=False, scrollToTop=False)
        
        self.todo_list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.todo_scroll.SetSizer(self.todo_list_sizer)
        
        sizer.Add(self.todo_scroll, 1, wx.EXPAND | wx.ALL, 8)
        
        panel.SetSizer(sizer)
        return panel
    
    def _create_settings_panel(self, parent):
        """Create the Settings panel."""
        panel = scrolled.ScrolledPanel(parent)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        panel.SetupScrolling(scroll_x=False)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add padding
        inner_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # === General Settings ===
        general_box = wx.StaticBox(panel, label="General")
        general_box.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        general_sizer = wx.StaticBoxSizer(general_box, wx.VERTICAL)
        
        # Auto-save interval
        autosave_sizer = wx.BoxSizer(wx.HORIZONTAL)
        autosave_sizer.Add(wx.StaticText(panel, label="Auto-save interval (sec):"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.autosave_spin = wx.SpinCtrl(panel, min=1, max=60, initial=5, size=(70, -1))
        autosave_sizer.Add(self.autosave_spin, 0)
        general_sizer.Add(autosave_sizer, 0, wx.ALL, 8)
        
        # Font size
        font_sizer = wx.BoxSizer(wx.HORIZONTAL)
        font_sizer.Add(wx.StaticText(panel, label="Editor font size:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.fontsize_spin = wx.SpinCtrl(panel, min=8, max=24, initial=11, size=(70, -1))
        self.fontsize_spin.Bind(wx.EVT_SPINCTRL, self._on_fontsize_change)
        font_sizer.Add(self.fontsize_spin, 0)
        general_sizer.Add(font_sizer, 0, wx.ALL, 8)
        
        inner_sizer.Add(general_sizer, 0, wx.EXPAND | wx.ALL, 8)
        
        # === BOM Settings ===
        bom_box = wx.StaticBox(panel, label="BOM Defaults")
        bom_box.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        bom_sizer = wx.StaticBoxSizer(bom_box, wx.VERTICAL)
        
        self.bom_exclude_dnp = wx.CheckBox(panel, label="Exclude DNP components")
        self.bom_exclude_dnp.SetValue(True)
        bom_sizer.Add(self.bom_exclude_dnp, 0, wx.ALL, 6)
        
        self.bom_exclude_fid = wx.CheckBox(panel, label="Exclude fiducials (FID*)")
        self.bom_exclude_fid.SetValue(True)
        bom_sizer.Add(self.bom_exclude_fid, 0, wx.ALL, 6)
        
        self.bom_exclude_tp = wx.CheckBox(panel, label="Exclude test points (TP*)")
        self.bom_exclude_tp.SetValue(True)
        bom_sizer.Add(self.bom_exclude_tp, 0, wx.ALL, 6)
        
        # Group by dropdown
        group_sizer = wx.BoxSizer(wx.HORIZONTAL)
        group_sizer.Add(wx.StaticText(panel, label="Group by:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.bom_group = wx.Choice(panel, choices=["Value + Footprint", "Value only", "Footprint only", "No grouping"])
        self.bom_group.SetSelection(0)
        group_sizer.Add(self.bom_group, 1, wx.EXPAND)
        bom_sizer.Add(group_sizer, 0, wx.EXPAND | wx.ALL, 6)
        
        inner_sizer.Add(bom_sizer, 0, wx.EXPAND | wx.ALL, 8)
        
        # === Component Sort Order ===
        sort_box = wx.StaticBox(panel, label="Component Sort Order")
        sort_box.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sort_sizer = wx.StaticBoxSizer(sort_box, wx.VERTICAL)
        
        sort_inner = wx.BoxSizer(wx.HORIZONTAL)
        self.sort_list = wx.ListBox(panel, choices=['C', 'R', 'L', 'D', 'U', 'Q', 'J', 'SW', 'F', 'TP'],
                                    style=wx.LB_SINGLE, size=(-1, 100))
        sort_inner.Add(self.sort_list, 1, wx.EXPAND | wx.RIGHT, 8)
        
        btn_sizer = wx.BoxSizer(wx.VERTICAL)
        up_btn = wx.Button(panel, label="▲", size=(30, 30))
        up_btn.Bind(wx.EVT_BUTTON, self._on_sort_up)
        btn_sizer.Add(up_btn, 0, wx.BOTTOM, 4)
        down_btn = wx.Button(panel, label="▼", size=(30, 30))
        down_btn.Bind(wx.EVT_BUTTON, self._on_sort_down)
        btn_sizer.Add(down_btn, 0)
        sort_inner.Add(btn_sizer, 0, wx.ALIGN_CENTER_VERTICAL)
        
        sort_sizer.Add(sort_inner, 0, wx.EXPAND | wx.ALL, 6)
        inner_sizer.Add(sort_sizer, 0, wx.EXPAND | wx.ALL, 8)
        
        # === Blacklist ===
        bl_box = wx.StaticBox(panel, label="Component Blacklist")
        bl_box.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        bl_sizer = wx.StaticBoxSizer(bl_box, wx.VERTICAL)
        
        bl_sizer.Add(wx.StaticText(panel, label="Glob patterns (e.g. MH*, TP*)"), 0, wx.ALL, 4)
        self.blacklist_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 50))
        self.blacklist_text.SetHint("MH*\nTP*")
        bl_sizer.Add(self.blacklist_text, 0, wx.EXPAND | wx.ALL, 6)
        
        self.blacklist_virtual = wx.CheckBox(panel, label="Blacklist virtual components")
        self.blacklist_virtual.SetValue(True)
        bl_sizer.Add(self.blacklist_virtual, 0, wx.ALL, 6)
        
        inner_sizer.Add(bl_sizer, 0, wx.EXPAND | wx.ALL, 8)
        
        # Save settings button
        save_btn = wx.Button(panel, label="💾 Save Settings", size=(-1, 32))
        save_btn.Bind(wx.EVT_BUTTON, self._on_save_settings)
        inner_sizer.Add(save_btn, 0, wx.ALL | wx.ALIGN_CENTER, 12)
        
        sizer.Add(inner_sizer, 1, wx.EXPAND)
        panel.SetSizer(sizer)
        return panel
    
    def _create_footer(self):
        """Create footer with status and branding."""
        footer = wx.Panel(self)
        footer.SetBackgroundColour(wx.Colour(248, 249, 250))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Status
        self.status_label = wx.StaticText(footer, label="Ready")
        self.status_label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.status_label.SetForegroundColour(wx.Colour(108, 117, 125))
        sizer.Add(self.status_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)
        
        sizer.AddStretchSpacer()
        
        # Branding
        brand = wx.StaticText(footer, label="PCBtools.xyz")
        brand.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        brand.SetForegroundColour(wx.Colour(108, 117, 125))
        sizer.Add(brand, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        footer.SetSizer(sizer)
        footer.SetMinSize((-1, 28))
        return footer
    
    # ========== Todo List Methods ==========
    
    def _add_todo_item(self, text="", done=False):
        """Add a todo item with checkbox."""
        item_id = self._todo_id_counter
        self._todo_id_counter += 1
        
        item_panel = wx.Panel(self.todo_scroll)
        item_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        item_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Checkbox
        cb = wx.CheckBox(item_panel)
        cb.SetValue(done)
        cb.Bind(wx.EVT_CHECKBOX, lambda e, iid=item_id: self._on_todo_check(iid, e))
        item_sizer.Add(cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 8)
        
        # Text input
        txt = wx.TextCtrl(item_panel, value=text, style=wx.BORDER_NONE | wx.TE_PROCESS_ENTER)
        txt.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        if done:
            txt.SetForegroundColour(wx.Colour(173, 181, 189))
        txt.Bind(wx.EVT_TEXT, lambda e, iid=item_id: self._on_todo_text_change(iid, e))
        txt.Bind(wx.EVT_TEXT_ENTER, lambda e: self._on_add_todo(None))
        item_sizer.Add(txt, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 6)
        
        # Delete button
        del_btn = wx.Button(item_panel, label="✕", size=(26, 26))
        del_btn.SetForegroundColour(wx.Colour(220, 53, 69))
        del_btn.Bind(wx.EVT_BUTTON, lambda e, iid=item_id: self._on_delete_todo(iid))
        item_sizer.Add(del_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 4)
        
        item_panel.SetSizer(item_sizer)
        
        # Store reference
        self._todo_items.append({
            'id': item_id,
            'panel': item_panel,
            'checkbox': cb,
            'text': txt,
            'done': done
        })
        
        self.todo_list_sizer.Add(item_panel, 0, wx.EXPAND | wx.BOTTOM, 2)
        self.todo_scroll.FitInside()
        self.todo_scroll.Layout()
        self._update_todo_progress()
        
        return txt
    
    def _on_add_todo(self, event):
        """Add new todo."""
        txt = self._add_todo_item()
        txt.SetFocus()
        self._save_todos()
    
    def _on_todo_check(self, item_id, event):
        """Handle checkbox toggle."""
        for item in self._todo_items:
            if item['id'] == item_id:
                item['done'] = event.IsChecked()
                if event.IsChecked():
                    item['text'].SetForegroundColour(wx.Colour(173, 181, 189))
                else:
                    item['text'].SetForegroundColour(wx.Colour(33, 37, 41))
                item['text'].Refresh()
                break
        self._update_todo_progress()
        self._save_todos()
    
    def _on_todo_text_change(self, item_id, event):
        """Handle todo text change."""
        self._modified = True
        wx.CallLater(1000, self._save_todos)
    
    def _on_delete_todo(self, item_id):
        """Delete a todo item."""
        for i, item in enumerate(self._todo_items):
            if item['id'] == item_id:
                item['panel'].Destroy()
                self._todo_items.pop(i)
                break
        self.todo_scroll.FitInside()
        self.todo_scroll.Layout()
        self._update_todo_progress()
        self._save_todos()
    
    def _on_clear_done_todos(self, event):
        """Clear completed todos."""
        to_remove = [item for item in self._todo_items if item['done']]
        for item in to_remove:
            item['panel'].Destroy()
            self._todo_items.remove(item)
        self.todo_scroll.FitInside()
        self.todo_scroll.Layout()
        self._update_todo_progress()
        self._save_todos()
    
    def _update_todo_progress(self):
        """Update progress label."""
        total = len(self._todo_items)
        done = sum(1 for item in self._todo_items if item['done'])
        self.todo_progress.SetLabel(f"{done}/{total} done")
    
    # ========== Settings Methods ==========
    
    def _on_fontsize_change(self, event):
        """Change editor font size."""
        size = self.fontsize_spin.GetValue()
        self.text_editor.SetFont(wx.Font(size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
    
    def _on_sort_up(self, event):
        """Move sort item up."""
        idx = self.sort_list.GetSelection()
        if idx > 0:
            items = list(self.sort_list.GetItems())
            items[idx], items[idx-1] = items[idx-1], items[idx]
            self.sort_list.Set(items)
            self.sort_list.SetSelection(idx-1)
    
    def _on_sort_down(self, event):
        """Move sort item down."""
        idx = self.sort_list.GetSelection()
        if idx >= 0 and idx < self.sort_list.GetCount() - 1:
            items = list(self.sort_list.GetItems())
            items[idx], items[idx+1] = items[idx+1], items[idx]
            self.sort_list.Set(items)
            self.sort_list.SetSelection(idx+1)
    
    def _on_save_settings(self, event):
        """Save settings."""
        settings = {
            'autosave_interval': self.autosave_spin.GetValue(),
            'font_size': self.fontsize_spin.GetValue(),
            'bom_exclude_dnp': self.bom_exclude_dnp.GetValue(),
            'bom_exclude_fid': self.bom_exclude_fid.GetValue(),
            'bom_exclude_tp': self.bom_exclude_tp.GetValue(),
            'bom_group': self.bom_group.GetSelection(),
            'sort_order': list(self.sort_list.GetItems()),
            'blacklist': self.blacklist_text.GetValue(),
            'blacklist_virtual': self.blacklist_virtual.GetValue(),
        }
        self.notes_manager.save_settings(settings)
        self._update_status("Settings saved ✓")
        wx.MessageBox("Settings saved!", "KiNotes", wx.OK | wx.ICON_INFORMATION)
    
    # ========== Import/Export ==========
    
    def _on_import_click(self, event):
        """Show import menu."""
        menu = wx.Menu()
        
        items = [
            ("📋 BOM (Interactive...)", "bom_config"),
            ("📋 BOM (Quick)", "bom"),
            None,
            ("📚 Stackup", "stackup"),
            ("📐 Board Size", "board_size"),
            ("⚡ Diff Pairs", "diff_pairs"),
            ("🔌 Netlist", "netlist"),
            ("🗂️ Layers", "layers"),
            ("🔩 Drill Table", "drill_table"),
            ("📏 Design Rules", "design_rules"),
            None,
            ("📝 All Metadata", "all"),
        ]
        
        for item in items:
            if item is None:
                menu.AppendSeparator()
            else:
                label, meta_type = item
                mi = menu.Append(wx.ID_ANY, label)
                self.Bind(wx.EVT_MENU, lambda e, t=meta_type: self._do_import(t), mi)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def _do_import(self, meta_type):
        """Import metadata."""
        if meta_type == 'bom_config':
            self._on_bom_config()
        else:
            self._on_import_metadata(meta_type)
    
    def _on_import_metadata(self, meta_type):
        """Import metadata from PCB."""
        try:
            text = self.metadata_extractor.extract(meta_type)
            if text:
                pos = self.text_editor.GetInsertionPoint()
                current = self.text_editor.GetValue()
                new_text = current[:pos] + "\n" + text + "\n" + current[pos:]
                self.text_editor.SetValue(new_text)
                self.text_editor.SetInsertionPoint(pos + len(text) + 2)
                self._update_status(f"Imported {meta_type}")
        except Exception as e:
            wx.MessageBox(f"Import failed: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_bom_config(self):
        """Show BOM config dialog."""
        try:
            from .bom_dialog import show_bom_dialog
            text = show_bom_dialog(self)
            if text:
                pos = self.text_editor.GetInsertionPoint()
                current = self.text_editor.GetValue()
                new_text = current[:pos] + "\n" + text + "\n" + current[pos:]
                self.text_editor.SetValue(new_text)
                self._update_status("BOM inserted")
        except Exception as e:
            wx.MessageBox(f"BOM failed: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_export_pdf(self):
        """Export to PDF."""
        try:
            content = self.text_editor.GetValue()
            filepath = self.pdf_exporter.export(content)
            if filepath:
                self._update_status(f"Exported: {os.path.basename(filepath)}")
                wx.MessageBox(f"Exported to:\n{filepath}", "Export", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Export failed: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_manual_save(self):
        """Manual save."""
        self._save_notes()
        self._save_todos()
        wx.MessageBox("Saved!", "KiNotes", wx.OK | wx.ICON_INFORMATION)
    
    # ========== Text Editor ==========
    
    def _on_text_changed(self, event):
        """Handle text changes."""
        self._modified = True
        self._save_notes()
        event.Skip()
    
    def _on_text_click(self, event):
        """Handle @designator clicks."""
        pos = self.text_editor.HitTestPos(event.GetPosition())[1]
        if pos >= 0:
            text = self.text_editor.GetValue()
            word = self._get_word_at_pos(text, pos)
            if word.startswith('@'):
                self._highlight_component(word[1:])
                return
        event.Skip()
    
    def _get_word_at_pos(self, text, pos):
        """Get word at position."""
        if pos < 0 or pos >= len(text):
            return ""
        start = end = pos
        while start > 0 and (text[start-1].isalnum() or text[start-1] in '@_'):
            start -= 1
        while end < len(text) and (text[end].isalnum() or text[end] in '@_'):
            end += 1
        return text[start:end]
    
    def _highlight_component(self, ref):
        """Highlight component."""
        try:
            if self.designator_linker.highlight(ref):
                self._update_status(f"Highlighted {ref}")
            else:
                self._update_status(f"{ref} not found")
        except Exception as e:
            self._update_status(f"Error: {str(e)}")
    
    # ========== Data Management ==========
    
    def _start_auto_save_timer(self):
        """Start auto-save timer."""
        self._auto_save_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_auto_save, self._auto_save_timer)
        self._auto_save_timer.Start(5000)
    
    def _on_auto_save(self, event):
        """Auto-save."""
        if self._modified:
            self._save_notes()
            self._save_todos()
    
    def _load_all_data(self):
        """Load all data."""
        # Notes
        try:
            content = self.notes_manager.load()
            if content:
                self.text_editor.SetValue(content)
        except:
            pass
        
        # Todos
        try:
            todos = self.notes_manager.load_todos()
            for todo in todos:
                self._add_todo_item(todo.get('text', ''), todo.get('done', False))
        except:
            pass
        
        # Settings
        try:
            settings = self.notes_manager.load_settings()
            if settings:
                self.autosave_spin.SetValue(settings.get('autosave_interval', 5))
                self.fontsize_spin.SetValue(settings.get('font_size', 11))
                self._on_fontsize_change(None)
                self.bom_exclude_dnp.SetValue(settings.get('bom_exclude_dnp', True))
                self.bom_exclude_fid.SetValue(settings.get('bom_exclude_fid', True))
                self.bom_exclude_tp.SetValue(settings.get('bom_exclude_tp', True))
                self.bom_group.SetSelection(settings.get('bom_group', 0))
                if 'sort_order' in settings:
                    self.sort_list.Set(settings['sort_order'])
                if 'blacklist' in settings:
                    self.blacklist_text.SetValue(settings['blacklist'])
                self.blacklist_virtual.SetValue(settings.get('blacklist_virtual', True))
        except:
            pass
        
        self._modified = False
        self._update_status("Loaded")
    
    def _save_notes(self):
        """Save notes."""
        try:
            self.notes_manager.save(self.text_editor.GetValue())
            self._modified = False
            self._update_status("Saved ✓")
        except Exception as e:
            self._update_status(f"Error: {str(e)}")
    
    def _save_todos(self):
        """Save todos."""
        try:
            todos = []
            for item in self._todo_items:
                todos.append({
                    'text': item['text'].GetValue(),
                    'done': item['checkbox'].GetValue()
                })
            self.notes_manager.save_todos(todos)
        except:
            pass
    
    def _update_status(self, msg):
        """Update status."""
        self.status_label.SetLabel(msg)
        wx.CallLater(3000, lambda: self.status_label.SetLabel("Ready") if self.status_label else None)
    
    def force_save(self):
        """Force save."""
        self._save_notes()
        self._save_todos()
    
    def cleanup(self):
        """Cleanup."""
        if self._auto_save_timer:
            self._auto_save_timer.Stop()
