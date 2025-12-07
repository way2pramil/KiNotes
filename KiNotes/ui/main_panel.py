"""
KiNotes Main Panel - Multi-tab UI like Interactive BOM
"""
import wx
import wx.lib.scrolledpanel as scrolled
import wx.lib.agw.flatnotebook as fnb
import re
import os
import json


class KiNotesMainPanel(wx.Panel):
    """
    Main KiNotes panel with multi-tab interface like IBOM.
    Tabs: Notes | Todo List | Settings
    """
    
    def __init__(self, parent, notes_manager, designator_linker, metadata_extractor, pdf_exporter):
        super().__init__(parent)
        
        self.notes_manager = notes_manager
        self.designator_linker = designator_linker
        self.metadata_extractor = metadata_extractor
        self.pdf_exporter = pdf_exporter
        
        self._auto_save_timer = None
        self._modified = False
        self._todo_items = []
        
        self._init_ui()
        self._load_all_data()
        self._start_auto_save_timer()
    
    def _init_ui(self):
        """Initialize the multi-tab UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create notebook with flat tabs (like IBOM)
        agw_style = (fnb.FNB_NO_X_BUTTON | fnb.FNB_NO_NAV_BUTTONS | 
                     fnb.FNB_NODRAG | fnb.FNB_FF2)
        self.notebook = fnb.FlatNotebook(self, agwStyle=agw_style)
        
        # Style the notebook tabs
        self.notebook.SetActiveTabColour(wx.Colour(240, 240, 240))
        self.notebook.SetTabAreaColour(wx.Colour(250, 250, 250))
        self.notebook.SetActiveTabTextColour(wx.Colour(0, 120, 212))
        self.notebook.SetNonActiveTabTextColour(wx.Colour(80, 80, 80))
        
        # Create tabs
        self.notes_tab = self._create_notes_tab()
        self.todo_tab = self._create_todo_tab()
        self.settings_tab = self._create_settings_tab()
        
        self.notebook.AddPage(self.notes_tab, "Notes")
        self.notebook.AddPage(self.todo_tab, "Todo List")
        self.notebook.AddPage(self.settings_tab, "Settings")
        
        main_sizer.Add(self.notebook, 1, wx.EXPAND)
        
        # Bottom toolbar
        bottom_bar = self._create_bottom_bar()
        main_sizer.Add(bottom_bar, 0, wx.EXPAND)
        
        self.SetSizer(main_sizer)
    
    def _create_notes_tab(self):
        """Create the Notes editor tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar for notes
        toolbar = self._create_notes_toolbar(panel)
        sizer.Add(toolbar, 0, wx.EXPAND | wx.ALL, 2)
        
        # Separator
        sep = wx.StaticLine(panel)
        sizer.Add(sep, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        
        # Text editor
        self.text_editor = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_RICH2 | wx.TE_PROCESS_TAB | wx.BORDER_SIMPLE
        )
        self.text_editor.SetFont(wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.text_editor.SetBackgroundColour(wx.Colour(255, 255, 255))
        
        sizer.Add(self.text_editor, 1, wx.EXPAND | wx.ALL, 5)
        
        # Bind events
        self.text_editor.Bind(wx.EVT_TEXT, self._on_text_changed)
        self.text_editor.Bind(wx.EVT_LEFT_DOWN, self._on_text_click)
        
        panel.SetSizer(sizer)
        return panel
    
    def _create_notes_toolbar(self, parent):
        """Create toolbar for notes tab."""
        toolbar = wx.Panel(parent)
        toolbar.SetBackgroundColour(wx.Colour(250, 250, 250))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Import dropdown button
        self.import_btn = wx.Button(toolbar, label="📥 Import", size=(80, 28))
        self.import_btn.SetToolTip("Import board metadata")
        self.import_btn.Bind(wx.EVT_BUTTON, self._on_import_click)
        sizer.Add(self.import_btn, 0, wx.ALL, 3)
        
        # Export PDF button
        pdf_btn = wx.Button(toolbar, label="📄 PDF", size=(65, 28))
        pdf_btn.SetToolTip("Export to PDF")
        pdf_btn.Bind(wx.EVT_BUTTON, lambda e: self._on_export_pdf())
        sizer.Add(pdf_btn, 0, wx.ALL, 3)
        
        sizer.AddStretchSpacer()
        
        # Save button
        save_btn = wx.Button(toolbar, label="💾 Save", size=(65, 28))
        save_btn.SetToolTip("Save notes")
        save_btn.Bind(wx.EVT_BUTTON, lambda e: self._on_save())
        sizer.Add(save_btn, 0, wx.ALL, 3)
        
        toolbar.SetSizer(sizer)
        return toolbar
    
    def _create_todo_tab(self):
        """Create the Todo List tab with interactive checkboxes."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar
        toolbar = wx.Panel(panel)
        toolbar.SetBackgroundColour(wx.Colour(250, 250, 250))
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        add_btn = wx.Button(toolbar, label="➕ Add Task", size=(90, 28))
        add_btn.Bind(wx.EVT_BUTTON, self._on_add_todo)
        tb_sizer.Add(add_btn, 0, wx.ALL, 3)
        
        clear_done_btn = wx.Button(toolbar, label="🗑️ Clear Done", size=(100, 28))
        clear_done_btn.Bind(wx.EVT_BUTTON, self._on_clear_done_todos)
        tb_sizer.Add(clear_done_btn, 0, wx.ALL, 3)
        
        tb_sizer.AddStretchSpacer()
        
        # Progress label
        self.todo_progress = wx.StaticText(toolbar, label="0/0 completed")
        self.todo_progress.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        tb_sizer.Add(self.todo_progress, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        toolbar.SetSizer(tb_sizer)
        sizer.Add(toolbar, 0, wx.EXPAND | wx.ALL, 2)
        
        # Separator
        sep = wx.StaticLine(panel)
        sizer.Add(sep, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        
        # Scrollable todo list
        self.todo_scroll = scrolled.ScrolledPanel(panel)
        self.todo_scroll.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.todo_scroll.SetupScrolling(scroll_x=False)
        
        self.todo_sizer = wx.BoxSizer(wx.VERTICAL)
        self.todo_scroll.SetSizer(self.todo_sizer)
        
        sizer.Add(self.todo_scroll, 1, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        return panel
    
    def _create_settings_tab(self):
        """Create the Settings tab."""
        panel = scrolled.ScrolledPanel(self.notebook)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        panel.SetupScrolling(scroll_x=False)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # === General Settings ===
        general_box = wx.StaticBox(panel, label="General")
        general_sizer = wx.StaticBoxSizer(general_box, wx.VERTICAL)
        
        # Auto-save interval
        autosave_sizer = wx.BoxSizer(wx.HORIZONTAL)
        autosave_sizer.Add(wx.StaticText(panel, label="Auto-save interval (seconds):"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.autosave_spin = wx.SpinCtrl(panel, min=1, max=60, initial=5, size=(70, -1))
        autosave_sizer.Add(self.autosave_spin, 0)
        general_sizer.Add(autosave_sizer, 0, wx.ALL, 5)
        
        # Font size
        font_sizer = wx.BoxSizer(wx.HORIZONTAL)
        font_sizer.Add(wx.StaticText(panel, label="Editor font size:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.fontsize_spin = wx.SpinCtrl(panel, min=8, max=24, initial=11, size=(70, -1))
        self.fontsize_spin.Bind(wx.EVT_SPINCTRL, self._on_fontsize_change)
        font_sizer.Add(self.fontsize_spin, 0)
        general_sizer.Add(font_sizer, 0, wx.ALL, 5)
        
        sizer.Add(general_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # === BOM Settings ===
        bom_box = wx.StaticBox(panel, label="BOM Defaults")
        bom_sizer = wx.StaticBoxSizer(bom_box, wx.VERTICAL)
        
        self.bom_exclude_dnp = wx.CheckBox(panel, label="Exclude DNP components")
        self.bom_exclude_dnp.SetValue(True)
        bom_sizer.Add(self.bom_exclude_dnp, 0, wx.ALL, 5)
        
        self.bom_exclude_fid = wx.CheckBox(panel, label="Exclude fiducials (FID*)")
        self.bom_exclude_fid.SetValue(True)
        bom_sizer.Add(self.bom_exclude_fid, 0, wx.ALL, 5)
        
        self.bom_exclude_tp = wx.CheckBox(panel, label="Exclude test points (TP*)")
        self.bom_exclude_tp.SetValue(True)
        bom_sizer.Add(self.bom_exclude_tp, 0, wx.ALL, 5)
        
        # Group by
        group_sizer = wx.BoxSizer(wx.HORIZONTAL)
        group_sizer.Add(wx.StaticText(panel, label="Group by:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.bom_group = wx.Choice(panel, choices=["Value + Footprint", "Value only", "Footprint only", "No grouping"])
        self.bom_group.SetSelection(0)
        group_sizer.Add(self.bom_group, 1)
        bom_sizer.Add(group_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(bom_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # === Component Sort Order (like IBOM) ===
        sort_box = wx.StaticBox(panel, label="Component Sort Order")
        sort_sizer = wx.StaticBoxSizer(sort_box, wx.VERTICAL)
        
        self.sort_list = wx.ListBox(panel, choices=['C', 'R', 'L', 'D', 'U', 'Y', 'X', 'F', 'SW', 'A', 'J', 'TP'], 
                                    style=wx.LB_SINGLE, size=(-1, 120))
        sort_sizer.Add(self.sort_list, 1, wx.EXPAND | wx.ALL, 5)
        
        sort_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        up_btn = wx.Button(panel, label="⬆️ Up", size=(60, 26))
        up_btn.Bind(wx.EVT_BUTTON, self._on_sort_up)
        down_btn = wx.Button(panel, label="⬇️ Down", size=(60, 26))
        down_btn.Bind(wx.EVT_BUTTON, self._on_sort_down)
        sort_btn_sizer.Add(up_btn, 0, wx.RIGHT, 5)
        sort_btn_sizer.Add(down_btn, 0)
        sort_sizer.Add(sort_btn_sizer, 0, wx.ALL, 5)
        
        sizer.Add(sort_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # === Component Blacklist (like IBOM) ===
        blacklist_box = wx.StaticBox(panel, label="Component Blacklist")
        blacklist_sizer = wx.StaticBoxSizer(blacklist_box, wx.VERTICAL)
        
        blacklist_sizer.Add(wx.StaticText(panel, label="Globs supported, e.g. MH*"), 0, wx.ALL, 5)
        
        self.blacklist_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 60))
        self.blacklist_text.SetHint("MH*\nTP*")
        blacklist_sizer.Add(self.blacklist_text, 0, wx.EXPAND | wx.ALL, 5)
        
        self.blacklist_virtual = wx.CheckBox(panel, label="Blacklist virtual components")
        self.blacklist_virtual.SetValue(True)
        blacklist_sizer.Add(self.blacklist_virtual, 0, wx.ALL, 5)
        
        self.blacklist_empty = wx.CheckBox(panel, label="Blacklist components with empty value")
        blacklist_sizer.Add(self.blacklist_empty, 0, wx.ALL, 5)
        
        sizer.Add(blacklist_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Save settings button
        save_settings_btn = wx.Button(panel, label="Save Current Settings...")
        save_settings_btn.Bind(wx.EVT_BUTTON, self._on_save_settings)
        sizer.Add(save_settings_btn, 0, wx.ALL, 10)
        
        panel.SetSizer(sizer)
        return panel
    
    def _create_bottom_bar(self):
        """Create bottom status/branding bar."""
        bar = wx.Panel(self, size=(-1, 26))
        bar.SetBackgroundColour(wx.Colour(245, 245, 245))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Status
        self.status_label = wx.StaticText(bar, label="Ready")
        self.status_label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.status_label.SetForegroundColour(wx.Colour(100, 100, 100))
        sizer.Add(self.status_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        
        sizer.AddStretchSpacer()
        
        # Branding
        brand = wx.StaticText(bar, label="Built with ❤️ by PCBtools.xyz")
        brand.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        brand.SetForegroundColour(wx.Colour(120, 120, 120))
        sizer.Add(brand, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        bar.SetSizer(sizer)
        return bar
    
    # ========== Todo List Methods ==========
    
    def _add_todo_item(self, text="", done=False, item_id=None):
        """Add a todo item with checkbox to the list."""
        if item_id is None:
            item_id = len(self._todo_items)
        
        item_panel = wx.Panel(self.todo_scroll)
        item_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        item_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Checkbox
        cb = wx.CheckBox(item_panel)
        cb.SetValue(done)
        cb.Bind(wx.EVT_CHECKBOX, lambda e, idx=item_id: self._on_todo_check(idx, e))
        item_sizer.Add(cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        
        # Text input
        txt = wx.TextCtrl(item_panel, value=text, style=wx.BORDER_NONE)
        txt.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        if done:
            txt.SetForegroundColour(wx.Colour(150, 150, 150))
        txt.Bind(wx.EVT_TEXT, lambda e, idx=item_id: self._on_todo_text_change(idx, e))
        txt.Bind(wx.EVT_KEY_DOWN, lambda e, idx=item_id: self._on_todo_key(idx, e))
        item_sizer.Add(txt, 1, wx.EXPAND | wx.ALL, 3)
        
        # Delete button
        del_btn = wx.Button(item_panel, label="✕", size=(24, 24))
        del_btn.SetToolTip("Delete task")
        del_btn.Bind(wx.EVT_BUTTON, lambda e, idx=item_id: self._on_delete_todo(idx))
        item_sizer.Add(del_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        
        item_panel.SetSizer(item_sizer)
        
        # Store reference
        self._todo_items.append({
            'id': item_id,
            'panel': item_panel,
            'checkbox': cb,
            'text': txt,
            'done': done
        })
        
        self.todo_sizer.Add(item_panel, 0, wx.EXPAND | wx.ALL, 2)
        self.todo_scroll.FitInside()
        self._update_todo_progress()
        
        return txt
    
    def _on_add_todo(self, event):
        """Add new todo item."""
        txt = self._add_todo_item()
        txt.SetFocus()
        self._save_todos()
    
    def _on_todo_check(self, idx, event):
        """Handle todo checkbox change."""
        for item in self._todo_items:
            if item['id'] == idx:
                item['done'] = event.IsChecked()
                if event.IsChecked():
                    item['text'].SetForegroundColour(wx.Colour(150, 150, 150))
                else:
                    item['text'].SetForegroundColour(wx.Colour(0, 0, 0))
                item['text'].Refresh()
                break
        self._update_todo_progress()
        self._save_todos()
    
    def _on_todo_text_change(self, idx, event):
        """Handle todo text change."""
        self._modified = True
        self._save_todos()
    
    def _on_todo_key(self, idx, event):
        """Handle Enter key to add new todo."""
        if event.GetKeyCode() == wx.WXK_RETURN:
            txt = self._add_todo_item()
            txt.SetFocus()
            self._save_todos()
        else:
            event.Skip()
    
    def _on_delete_todo(self, idx):
        """Delete a todo item."""
        for i, item in enumerate(self._todo_items):
            if item['id'] == idx:
                item['panel'].Destroy()
                self._todo_items.pop(i)
                break
        self.todo_scroll.FitInside()
        self._update_todo_progress()
        self._save_todos()
    
    def _on_clear_done_todos(self, event):
        """Clear all completed todos."""
        to_remove = [item for item in self._todo_items if item['done']]
        for item in to_remove:
            item['panel'].Destroy()
            self._todo_items.remove(item)
        self.todo_scroll.FitInside()
        self._update_todo_progress()
        self._save_todos()
    
    def _update_todo_progress(self):
        """Update todo progress label."""
        total = len(self._todo_items)
        done = sum(1 for item in self._todo_items if item['done'])
        self.todo_progress.SetLabel(f"{done}/{total} completed")
    
    # ========== Settings Methods ==========
    
    def _on_fontsize_change(self, event):
        """Change editor font size."""
        size = self.fontsize_spin.GetValue()
        self.text_editor.SetFont(wx.Font(size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
    
    def _on_sort_up(self, event):
        """Move selected sort item up."""
        idx = self.sort_list.GetSelection()
        if idx > 0:
            items = list(self.sort_list.GetItems())
            items[idx], items[idx-1] = items[idx-1], items[idx]
            self.sort_list.Set(items)
            self.sort_list.SetSelection(idx-1)
    
    def _on_sort_down(self, event):
        """Move selected sort item down."""
        idx = self.sort_list.GetSelection()
        if idx < self.sort_list.GetCount() - 1 and idx >= 0:
            items = list(self.sort_list.GetItems())
            items[idx], items[idx+1] = items[idx+1], items[idx]
            self.sort_list.Set(items)
            self.sort_list.SetSelection(idx+1)
    
    def _on_save_settings(self, event):
        """Save current settings."""
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
            'blacklist_empty': self.blacklist_empty.GetValue(),
        }
        self.notes_manager.save_settings(settings)
        self._update_status("Settings saved")
        wx.MessageBox("Settings saved!", "KiNotes", wx.OK | wx.ICON_INFORMATION)
    
    # ========== Import/Export Methods ==========
    
    def _on_import_click(self, event):
        """Show import metadata menu."""
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
        
        for item_data in items:
            if item_data is None:
                menu.AppendSeparator()
            else:
                label, meta_type = item_data
                item = menu.Append(wx.ID_ANY, label)
                self.Bind(wx.EVT_MENU, lambda e, t=meta_type: self._do_import(t), item)
        
        btn_rect = self.import_btn.GetRect()
        self.PopupMenu(menu, (btn_rect.x, btn_rect.y + btn_rect.height))
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
            metadata_text = self.metadata_extractor.extract(meta_type)
            if metadata_text:
                pos = self.text_editor.GetInsertionPoint()
                current = self.text_editor.GetValue()
                new_text = current[:pos] + "\n" + metadata_text + "\n" + current[pos:]
                self.text_editor.SetValue(new_text)
                self.text_editor.SetInsertionPoint(pos + len(metadata_text) + 2)
                self._update_status(f"Imported {meta_type}")
        except Exception as e:
            wx.MessageBox(f"Import failed: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_bom_config(self):
        """Show IBOM-style BOM dialog."""
        try:
            from .bom_dialog import show_bom_dialog
            bom_text = show_bom_dialog(self)
            if bom_text:
                pos = self.text_editor.GetInsertionPoint()
                current = self.text_editor.GetValue()
                new_text = current[:pos] + "\n" + bom_text + "\n" + current[pos:]
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
                wx.MessageBox(f"Exported to:\n{filepath}", "Export Complete", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Export failed: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_save(self):
        """Manual save."""
        self._save_notes()
        self._save_todos()
        wx.MessageBox("Saved!", "KiNotes", wx.OK | wx.ICON_INFORMATION)
    
    # ========== Text Editor Events ==========
    
    def _on_text_changed(self, event):
        """Handle text changes."""
        self._modified = True
        self._save_notes()
        event.Skip()
    
    def _on_text_click(self, event):
        """Handle click on @designator links."""
        pos = self.text_editor.HitTestPos(event.GetPosition())[1]
        if pos >= 0:
            text = self.text_editor.GetValue()
            word = self._get_word_at_position(text, pos)
            if word.startswith('@'):
                self._highlight_component(word[1:])
                return
        event.Skip()
    
    def _get_word_at_position(self, text, pos):
        """Get word at position."""
        if pos < 0 or pos >= len(text):
            return ""
        start = end = pos
        while start > 0 and (text[start-1].isalnum() or text[start-1] in '@_'):
            start -= 1
        while end < len(text) and (text[end].isalnum() or text[end] in '@_'):
            end += 1
        return text[start:end]
    
    def _highlight_component(self, designator):
        """Highlight component on PCB."""
        try:
            if self.designator_linker.highlight(designator):
                self._update_status(f"Highlighted {designator}")
            else:
                self._update_status(f"{designator} not found")
        except Exception as e:
            self._update_status(f"Error: {str(e)}")
    
    # ========== Data Management ==========
    
    def _start_auto_save_timer(self):
        """Start auto-save timer."""
        self._auto_save_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_auto_save, self._auto_save_timer)
        self._auto_save_timer.Start(5000)
    
    def _on_auto_save(self, event):
        """Auto-save callback."""
        if self._modified:
            self._save_notes()
            self._save_todos()
    
    def _load_all_data(self):
        """Load notes and todos."""
        # Load notes
        try:
            content = self.notes_manager.load()
            if content:
                self.text_editor.SetValue(content)
        except:
            pass
        
        # Load todos
        try:
            todos = self.notes_manager.load_todos()
            for todo in todos:
                self._add_todo_item(todo.get('text', ''), todo.get('done', False))
        except:
            pass
        
        # Load settings
        try:
            settings = self.notes_manager.load_settings()
            if settings:
                self.autosave_spin.SetValue(settings.get('autosave_interval', 5))
                self.fontsize_spin.SetValue(settings.get('font_size', 11))
                self._on_fontsize_change(None)
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
    
    def _update_status(self, message):
        """Update status label."""
        self.status_label.SetLabel(message)
        wx.CallLater(3000, lambda: self.status_label.SetLabel("Ready") if self.status_label else None)
    
    def force_save(self):
        """Force save all data."""
        self._save_notes()
        self._save_todos()
    
    def cleanup(self):
        """Cleanup resources."""
        if self._auto_save_timer:
            self._auto_save_timer.Stop()
