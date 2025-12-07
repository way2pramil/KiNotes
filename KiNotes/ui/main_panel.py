"""
KiNotes Main Panel - IBOM-style tabbed UI
Tab 1: Notes | Tab 2: Todo List | Tab 3: BOM Tool
"""
import wx
import wx.lib.scrolledpanel as scrolled
import os
import datetime


class KiNotesMainPanel(wx.Panel):
    """Main panel with IBOM-style tabs."""
    
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
        
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        
        self._init_ui()
        self._load_all_data()
        self._auto_insert_header()
        self._start_auto_save_timer()
    
    def _init_ui(self):
        """Initialize IBOM-style tabbed UI."""
        print("KiNotes: Initializing UI...")
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # === TAB BAR (IBOM style) ===
        print("KiNotes: Creating tab bar...")
        self.tab_bar = self._create_tab_bar()
        main_sizer.Add(self.tab_bar, 0, wx.EXPAND)
        
        # === CONTENT AREA ===
        print("KiNotes: Creating content panel...")
        self.content_panel = wx.Panel(self)
        self.content_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create all tab panels
        print("KiNotes: Creating Notes tab...")
        self.notes_panel = self._create_notes_tab(self.content_panel)
        print("KiNotes: Creating Todo tab...")
        self.todo_panel = self._create_todo_tab(self.content_panel)
        print("KiNotes: Creating BOM tab...")
        self.bom_panel = self._create_bom_tab(self.content_panel)
        
        self.content_sizer.Add(self.notes_panel, 1, wx.EXPAND)
        self.content_sizer.Add(self.todo_panel, 1, wx.EXPAND)
        self.content_sizer.Add(self.bom_panel, 1, wx.EXPAND)
        
        self.content_panel.SetSizer(self.content_sizer)
        main_sizer.Add(self.content_panel, 1, wx.EXPAND)
        
        # === FOOTER ===
        print("KiNotes: Creating footer...")
        footer = self._create_footer()
        main_sizer.Add(footer, 0, wx.EXPAND)
        
        self.SetSizer(main_sizer)
        
        # Show first tab
        print("KiNotes: Showing first tab...")
        self._show_tab(0)
        print("KiNotes: UI initialization complete!")
    
    def _create_tab_bar(self):
        """Create IBOM-style tab bar with reliable buttons."""
        tab_bar = wx.Panel(self)
        tab_bar.SetBackgroundColour(wx.Colour(50, 50, 50))  # Dark background
        tab_bar.SetMinSize((-1, 36))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(4)
        
        self.tab_buttons = []
        tabs = ["Notes", "Todo", "BOM"]
        
        for idx, label in enumerate(tabs):
            # Use regular button
            btn = wx.Button(tab_bar, label=label, size=(70, 28), style=wx.BORDER_NONE)
            btn.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            btn.Bind(wx.EVT_BUTTON, lambda e, i=idx: self._on_tab_click(i))
            self.tab_buttons.append(btn)
            sizer.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 2)
        
        sizer.AddStretchSpacer()
        tab_bar.SetSizer(sizer)
        
        # Force initial styling
        wx.CallAfter(self._update_tab_styles, 0)
        
        return tab_bar
    
    def _update_tab_styles(self, active_idx):
        """Update tab button styles."""
        for i, btn in enumerate(self.tab_buttons):
            try:
                if i == active_idx:
                    btn.SetBackgroundColour(wx.Colour(0, 120, 212))  # Blue active
                    btn.SetForegroundColour(wx.Colour(255, 255, 255))
                else:
                    btn.SetBackgroundColour(wx.Colour(80, 80, 80))  # Gray inactive
                    btn.SetForegroundColour(wx.Colour(180, 180, 180))
                btn.Refresh()
            except:
                pass
    
    def _on_tab_click(self, idx):
        """Handle tab click."""
        self._show_tab(idx)
    
    def _show_tab(self, idx):
        """Show selected tab."""
        self._current_tab = idx
        
        # Update button styles
        self._update_tab_styles(idx)
        
        # Hide all panels
        self.notes_panel.Hide()
        self.todo_panel.Hide()
        self.bom_panel.Hide()
        
        # Show selected panel
        if idx == 0:
            self.notes_panel.Show()
        elif idx == 1:
            self.todo_panel.Show()
            try:
                self.todo_scroll.FitInside()
            except:
                pass
        elif idx == 2:
            self.bom_panel.Show()
            try:
                self.bom_panel.FitInside()
            except:
                pass
        
        # Force layout refresh
        self.content_panel.Layout()
        self.Layout()
        self.Refresh()
        self.Update()
        
        self.content_panel.Layout()
        self.Layout()
        self.Refresh()
    
    # ============================================================
    # TAB 1: NOTES
    # ============================================================
    
    def _create_notes_tab(self, parent):
        """Create Notes tab with editor and toolbar."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar
        toolbar = wx.Panel(panel)
        toolbar.SetBackgroundColour(wx.Colour(240, 240, 240))
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Import button
        import_btn = wx.Button(toolbar, label="Import ▼", size=(75, 26))
        import_btn.Bind(wx.EVT_BUTTON, self._on_import_click)
        tb_sizer.Add(import_btn, 0, wx.ALL, 3)
        
        # PDF button
        pdf_btn = wx.Button(toolbar, label="PDF", size=(50, 26))
        pdf_btn.Bind(wx.EVT_BUTTON, lambda e: self._on_export_pdf())
        tb_sizer.Add(pdf_btn, 0, wx.ALL, 3)
        
        # Save button
        save_btn = wx.Button(toolbar, label="Save", size=(50, 26))
        save_btn.Bind(wx.EVT_BUTTON, lambda e: self._on_manual_save())
        tb_sizer.Add(save_btn, 0, wx.ALL, 3)
        
        toolbar.SetSizer(tb_sizer)
        sizer.Add(toolbar, 0, wx.EXPAND)
        
        # Text editor
        self.text_editor = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_RICH2 | wx.BORDER_SIMPLE
        )
        self.text_editor.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.text_editor.Bind(wx.EVT_TEXT, self._on_text_changed)
        self.text_editor.Bind(wx.EVT_LEFT_DOWN, self._on_text_click)
        sizer.Add(self.text_editor, 1, wx.EXPAND | wx.ALL, 4)
        
        panel.SetSizer(sizer)
        return panel
    
    def _auto_insert_header(self):
        """Auto-insert project header if notes are empty."""
        current = self.text_editor.GetValue().strip()
        if current and not current.startswith("Start typing"):
            return  # Don't overwrite existing notes
        
        try:
            import pcbnew
            board = pcbnew.GetBoard()
            if not board:
                return
            
            # Get project info
            filename = board.GetFileName()
            project_name = os.path.splitext(os.path.basename(filename))[0] if filename else "Untitled"
            
            # Get title block info
            title_block = board.GetTitleBlock()
            title = title_block.GetTitle() or project_name
            author = title_block.GetCompany() or ""
            revision = title_block.GetRevision() or ""
            date = title_block.GetDate() or datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Build header
            header_lines = [f"# {title}"]
            if author:
                header_lines.append(f"**Author:** {author}")
            if revision:
                header_lines.append(f"**Revision:** {revision}")
            header_lines.append(f"**Date:** {date}")
            header_lines.append("")
            header_lines.append("---")
            header_lines.append("")
            header_lines.append("")
            
            self.text_editor.SetValue("\n".join(header_lines))
            self.text_editor.SetInsertionPointEnd()
            
        except Exception as e:
            print(f"KiNotes: Auto-header failed: {e}")
    
    # ============================================================
    # TAB 2: TODO LIST
    # ============================================================
    
    def _create_todo_tab(self, parent):
        """Create Todo tab with checkboxes."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar
        toolbar = wx.Panel(panel)
        toolbar.SetBackgroundColour(wx.Colour(240, 240, 240))
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        add_btn = wx.Button(toolbar, label="+ Add Task", size=(80, 26))
        add_btn.Bind(wx.EVT_BUTTON, self._on_add_todo)
        tb_sizer.Add(add_btn, 0, wx.ALL, 3)
        
        clear_btn = wx.Button(toolbar, label="Clear Done", size=(80, 26))
        clear_btn.Bind(wx.EVT_BUTTON, self._on_clear_done)
        tb_sizer.Add(clear_btn, 0, wx.ALL, 3)
        
        tb_sizer.AddStretchSpacer()
        
        self.todo_count = wx.StaticText(toolbar, label="0/0")
        self.todo_count.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        tb_sizer.Add(self.todo_count, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        toolbar.SetSizer(tb_sizer)
        sizer.Add(toolbar, 0, wx.EXPAND)
        
        # Scrollable todo list
        self.todo_scroll = scrolled.ScrolledPanel(panel)
        self.todo_scroll.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.todo_scroll.SetupScrolling(scroll_x=False)
        
        self.todo_sizer = wx.BoxSizer(wx.VERTICAL)
        self.todo_scroll.SetSizer(self.todo_sizer)
        
        sizer.Add(self.todo_scroll, 1, wx.EXPAND | wx.ALL, 4)
        
        panel.SetSizer(sizer)
        return panel
    
    def _add_todo_item(self, text="", done=False):
        """Add a todo item with checkbox and text."""
        item_id = self._todo_id_counter
        self._todo_id_counter += 1
        
        item_panel = wx.Panel(self.todo_scroll)
        item_panel.SetBackgroundColour(wx.Colour(250, 250, 250))
        item_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Checkbox
        cb = wx.CheckBox(item_panel)
        cb.SetValue(done)
        cb.Bind(wx.EVT_CHECKBOX, lambda e, iid=item_id: self._on_todo_toggle(iid))
        item_sizer.Add(cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
        
        # Text field
        txt = wx.TextCtrl(item_panel, value=text, style=wx.BORDER_NONE | wx.TE_PROCESS_ENTER)
        txt.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        if done:
            txt.SetForegroundColour(wx.Colour(160, 160, 160))
        txt.Bind(wx.EVT_TEXT, lambda e: self._save_todos())
        txt.Bind(wx.EVT_TEXT_ENTER, lambda e: self._on_add_todo(None))
        item_sizer.Add(txt, 1, wx.EXPAND | wx.ALL, 4)
        
        # Delete button
        del_btn = wx.Button(item_panel, label="×", size=(24, 24))
        del_btn.SetForegroundColour(wx.Colour(200, 60, 60))
        del_btn.Bind(wx.EVT_BUTTON, lambda e, iid=item_id: self._on_delete_todo(iid))
        item_sizer.Add(del_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        
        item_panel.SetSizer(item_sizer)
        
        self._todo_items.append({
            'id': item_id,
            'panel': item_panel,
            'checkbox': cb,
            'text': txt,
            'done': done
        })
        
        self.todo_sizer.Add(item_panel, 0, wx.EXPAND | wx.BOTTOM, 2)
        self.todo_scroll.FitInside()
        self.todo_scroll.Layout()
        self._update_todo_count()
        
        return txt
    
    def _on_add_todo(self, event):
        """Add new todo."""
        txt = self._add_todo_item()
        txt.SetFocus()
        self._save_todos()
    
    def _on_todo_toggle(self, item_id):
        """Toggle todo completion."""
        for item in self._todo_items:
            if item['id'] == item_id:
                item['done'] = item['checkbox'].GetValue()
                if item['done']:
                    item['text'].SetForegroundColour(wx.Colour(160, 160, 160))
                else:
                    item['text'].SetForegroundColour(wx.Colour(0, 0, 0))
                item['text'].Refresh()
                break
        self._update_todo_count()
        self._save_todos()
    
    def _on_delete_todo(self, item_id):
        """Delete todo item."""
        for i, item in enumerate(self._todo_items):
            if item['id'] == item_id:
                item['panel'].Destroy()
                self._todo_items.pop(i)
                break
        self.todo_scroll.FitInside()
        self._update_todo_count()
        self._save_todos()
    
    def _on_clear_done(self, event):
        """Clear completed todos."""
        to_remove = [item for item in self._todo_items if item['done']]
        for item in to_remove:
            item['panel'].Destroy()
            self._todo_items.remove(item)
        self.todo_scroll.FitInside()
        self._update_todo_count()
        self._save_todos()
    
    def _update_todo_count(self):
        """Update todo count display."""
        total = len(self._todo_items)
        done = sum(1 for item in self._todo_items if item['done'])
        self.todo_count.SetLabel(f"{done}/{total}")
    
    # ============================================================
    # TAB 3: BOM TOOL (IBOM-style)
    # ============================================================
    
    def _create_bom_tab(self, parent):
        """Create BOM Tool tab with IBOM-style options."""
        panel = scrolled.ScrolledPanel(parent)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        panel.SetupScrolling(scroll_x=False)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # === GENERAL OPTIONS ===
        gen_box = wx.StaticBox(panel, label="General")
        gen_sizer = wx.StaticBoxSizer(gen_box, wx.VERTICAL)
        
        self.bom_show_qty = wx.CheckBox(panel, label="Show quantity column")
        self.bom_show_qty.SetValue(True)
        gen_sizer.Add(self.bom_show_qty, 0, wx.ALL, 4)
        
        self.bom_show_value = wx.CheckBox(panel, label="Show value column")
        self.bom_show_value.SetValue(True)
        gen_sizer.Add(self.bom_show_value, 0, wx.ALL, 4)
        
        self.bom_show_fp = wx.CheckBox(panel, label="Show footprint column")
        self.bom_show_fp.SetValue(True)
        gen_sizer.Add(self.bom_show_fp, 0, wx.ALL, 4)
        
        self.bom_show_refs = wx.CheckBox(panel, label="Show references column")
        self.bom_show_refs.SetValue(True)
        gen_sizer.Add(self.bom_show_refs, 0, wx.ALL, 4)
        
        sizer.Add(gen_sizer, 0, wx.EXPAND | wx.ALL, 6)
        
        # === GROUPING ===
        grp_box = wx.StaticBox(panel, label="Grouping")
        grp_sizer = wx.StaticBoxSizer(grp_box, wx.VERTICAL)
        
        group_row = wx.BoxSizer(wx.HORIZONTAL)
        group_row.Add(wx.StaticText(panel, label="Group by:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.bom_group_by = wx.Choice(panel, choices=[
            "Value + Footprint",
            "Value only",
            "Footprint only",
            "No grouping"
        ])
        self.bom_group_by.SetSelection(0)
        group_row.Add(self.bom_group_by, 1, wx.EXPAND)
        grp_sizer.Add(group_row, 0, wx.EXPAND | wx.ALL, 4)
        
        sizer.Add(grp_sizer, 0, wx.EXPAND | wx.ALL, 6)
        
        # === FILTERS ===
        flt_box = wx.StaticBox(panel, label="Filters")
        flt_sizer = wx.StaticBoxSizer(flt_box, wx.VERTICAL)
        
        self.bom_exclude_dnp = wx.CheckBox(panel, label="Exclude DNP (Do Not Populate)")
        self.bom_exclude_dnp.SetValue(True)
        flt_sizer.Add(self.bom_exclude_dnp, 0, wx.ALL, 4)
        
        self.bom_exclude_virtual = wx.CheckBox(panel, label="Exclude virtual components")
        self.bom_exclude_virtual.SetValue(True)
        flt_sizer.Add(self.bom_exclude_virtual, 0, wx.ALL, 4)
        
        self.bom_exclude_fid = wx.CheckBox(panel, label="Exclude fiducials (FID*)")
        self.bom_exclude_fid.SetValue(True)
        flt_sizer.Add(self.bom_exclude_fid, 0, wx.ALL, 4)
        
        self.bom_exclude_tp = wx.CheckBox(panel, label="Exclude test points (TP*)")
        self.bom_exclude_tp.SetValue(True)
        flt_sizer.Add(self.bom_exclude_tp, 0, wx.ALL, 4)
        
        self.bom_exclude_mh = wx.CheckBox(panel, label="Exclude mounting holes (MH*)")
        self.bom_exclude_mh.SetValue(True)
        flt_sizer.Add(self.bom_exclude_mh, 0, wx.ALL, 4)
        
        sizer.Add(flt_sizer, 0, wx.EXPAND | wx.ALL, 6)
        
        # === SORT ORDER ===
        sort_box = wx.StaticBox(panel, label="Sort Order")
        sort_sizer = wx.StaticBoxSizer(sort_box, wx.VERTICAL)
        
        sort_row = wx.BoxSizer(wx.HORIZONTAL)
        sort_row.Add(wx.StaticText(panel, label="Sort by:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.bom_sort_by = wx.Choice(panel, choices=[
            "Reference (natural)",
            "Value",
            "Footprint",
            "Quantity"
        ])
        self.bom_sort_by.SetSelection(0)
        sort_row.Add(self.bom_sort_by, 1, wx.EXPAND)
        sort_sizer.Add(sort_row, 0, wx.EXPAND | wx.ALL, 4)
        
        sizer.Add(sort_sizer, 0, wx.EXPAND | wx.ALL, 6)
        
        # === CUSTOM BLACKLIST ===
        bl_box = wx.StaticBox(panel, label="Custom Blacklist")
        bl_sizer = wx.StaticBoxSizer(bl_box, wx.VERTICAL)
        
        bl_sizer.Add(wx.StaticText(panel, label="Reference patterns to exclude (one per line):"), 0, wx.ALL, 4)
        self.bom_blacklist = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 50))
        self.bom_blacklist.SetHint("e.g.\nLOGO*\nH*")
        bl_sizer.Add(self.bom_blacklist, 0, wx.EXPAND | wx.ALL, 4)
        
        sizer.Add(bl_sizer, 0, wx.EXPAND | wx.ALL, 6)
        
        # === GENERATE BUTTON ===
        gen_btn = wx.Button(panel, label="Generate BOM to Notes", size=(-1, 32))
        gen_btn.SetBackgroundColour(wx.Colour(0, 120, 212))
        gen_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        gen_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        gen_btn.Bind(wx.EVT_BUTTON, self._on_generate_bom)
        sizer.Add(gen_btn, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        return panel
    
    def _on_generate_bom(self, event):
        """Generate BOM and insert into Notes."""
        try:
            bom_text = self._generate_bom_text()
            if bom_text:
                # Insert at end of notes
                current = self.text_editor.GetValue()
                if current and not current.endswith("\n"):
                    current += "\n"
                current += "\n" + bom_text
                self.text_editor.SetValue(current)
                self.text_editor.SetInsertionPointEnd()
                
                # Switch to Notes tab
                self._show_tab(0)
                self._update_status("BOM inserted into notes")
        except Exception as e:
            wx.MessageBox(f"BOM generation failed: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _generate_bom_text(self):
        """Generate BOM text based on settings."""
        import pcbnew
        import fnmatch
        
        board = pcbnew.GetBoard()
        if not board:
            return None
        
        # Get blacklist patterns
        blacklist = []
        if self.bom_exclude_fid.GetValue():
            blacklist.append("FID*")
        if self.bom_exclude_tp.GetValue():
            blacklist.append("TP*")
        if self.bom_exclude_mh.GetValue():
            blacklist.append("MH*")
        
        custom_bl = self.bom_blacklist.GetValue().strip()
        if custom_bl:
            blacklist.extend([p.strip() for p in custom_bl.split("\n") if p.strip()])
        
        # Collect components
        components = []
        for fp in board.GetFootprints():
            ref = fp.GetReference()
            value = fp.GetValue()
            footprint = fp.GetFPIDAsString().split(":")[-1] if fp.GetFPIDAsString() else ""
            
            # Apply filters
            if self.bom_exclude_dnp.GetValue():
                try:
                    if hasattr(fp, 'GetAttributes'):
                        attrs = fp.GetAttributes()
                        if hasattr(pcbnew, 'FP_EXCLUDE_FROM_BOM') and (attrs & pcbnew.FP_EXCLUDE_FROM_BOM):
                            continue
                except:
                    pass
            
            if self.bom_exclude_virtual.GetValue():
                try:
                    if hasattr(fp, 'GetAttributes'):
                        attrs = fp.GetAttributes()
                        if hasattr(pcbnew, 'FP_BOARD_ONLY') and (attrs & pcbnew.FP_BOARD_ONLY):
                            continue
                except:
                    pass
            
            # Check blacklist
            skip = False
            for pattern in blacklist:
                if fnmatch.fnmatch(ref.upper(), pattern.upper()):
                    skip = True
                    break
            if skip:
                continue
            
            components.append({
                'ref': ref,
                'value': value,
                'footprint': footprint
            })
        
        if not components:
            return "## BOM\n\n*No components found*\n"
        
        # Group components
        group_mode = self.bom_group_by.GetSelection()
        grouped = {}
        
        for comp in components:
            if group_mode == 0:  # Value + Footprint
                key = (comp['value'], comp['footprint'])
            elif group_mode == 1:  # Value only
                key = (comp['value'], "")
            elif group_mode == 2:  # Footprint only
                key = ("", comp['footprint'])
            else:  # No grouping
                key = (comp['ref'], comp['value'], comp['footprint'])
            
            if key not in grouped:
                grouped[key] = {
                    'value': comp['value'],
                    'footprint': comp['footprint'],
                    'refs': []
                }
            grouped[key]['refs'].append(comp['ref'])
        
        # Sort
        def natural_sort_key(ref):
            import re
            parts = re.split(r'(\d+)', ref)
            return [int(p) if p.isdigit() else p.lower() for p in parts]
        
        # Sort refs within groups
        for group in grouped.values():
            group['refs'].sort(key=natural_sort_key)
        
        # Sort groups
        sort_mode = self.bom_sort_by.GetSelection()
        if sort_mode == 0:  # Reference
            items = sorted(grouped.values(), key=lambda x: natural_sort_key(x['refs'][0]))
        elif sort_mode == 1:  # Value
            items = sorted(grouped.values(), key=lambda x: x['value'].lower())
        elif sort_mode == 2:  # Footprint
            items = sorted(grouped.values(), key=lambda x: x['footprint'].lower())
        else:  # Quantity
            items = sorted(grouped.values(), key=lambda x: -len(x['refs']))
        
        # Build output
        lines = ["## Bill of Materials", ""]
        
        # Build header
        header_parts = []
        if self.bom_show_qty.GetValue():
            header_parts.append("Qty")
        if self.bom_show_value.GetValue():
            header_parts.append("Value")
        if self.bom_show_fp.GetValue():
            header_parts.append("Footprint")
        if self.bom_show_refs.GetValue():
            header_parts.append("References")
        
        lines.append("| " + " | ".join(header_parts) + " |")
        lines.append("| " + " | ".join(["---"] * len(header_parts)) + " |")
        
        # Build rows
        total_count = 0
        for item in items:
            row_parts = []
            qty = len(item['refs'])
            total_count += qty
            
            if self.bom_show_qty.GetValue():
                row_parts.append(str(qty))
            if self.bom_show_value.GetValue():
                row_parts.append(item['value'])
            if self.bom_show_fp.GetValue():
                row_parts.append(item['footprint'])
            if self.bom_show_refs.GetValue():
                row_parts.append(", ".join(item['refs']))
            
            lines.append("| " + " | ".join(row_parts) + " |")
        
        lines.append("")
        lines.append(f"**Total:** {total_count} components, {len(items)} unique")
        lines.append("")
        
        return "\n".join(lines)
    
    # ============================================================
    # IMPORT / EXPORT
    # ============================================================
    
    def _on_import_click(self, event):
        """Show import menu."""
        menu = wx.Menu()
        
        items = [
            ("Board Info", "board_size"),
            ("Stackup", "stackup"),
            ("Netlist", "netlist"),
            ("Layers", "layers"),
            ("Drill Table", "drill_table"),
            ("Design Rules", "design_rules"),
            ("Diff Pairs", "diff_pairs"),
        ]
        
        for label, meta_type in items:
            mi = menu.Append(wx.ID_ANY, label)
            self.Bind(wx.EVT_MENU, lambda e, t=meta_type: self._import_metadata(t), mi)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def _import_metadata(self, meta_type):
        """Import metadata into notes."""
        try:
            text = self.metadata_extractor.extract(meta_type)
            if text:
                current = self.text_editor.GetValue()
                if current and not current.endswith("\n"):
                    current += "\n"
                current += "\n" + text + "\n"
                self.text_editor.SetValue(current)
                self.text_editor.SetInsertionPointEnd()
                self._update_status(f"Imported {meta_type}")
        except Exception as e:
            wx.MessageBox(f"Import failed: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_export_pdf(self):
        """Export notes to PDF."""
        try:
            content = self.text_editor.GetValue()
            filepath = self.pdf_exporter.export(content)
            if filepath:
                self._update_status(f"Exported PDF")
                wx.MessageBox(f"Exported to:\n{filepath}", "Export", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Export failed: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_manual_save(self):
        """Manual save."""
        self._save_notes()
        self._save_todos()
        self._update_status("Saved")
    
    # ============================================================
    # TEXT EDITOR
    # ============================================================
    
    def _on_text_changed(self, event):
        """Handle text changes."""
        self._modified = True
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
        """Highlight component on board."""
        try:
            if self.designator_linker.highlight(ref):
                self._update_status(f"→ {ref}")
        except:
            pass
    
    # ============================================================
    # DATA MANAGEMENT
    # ============================================================
    
    def _create_footer(self):
        """Create footer."""
        footer = wx.Panel(self)
        footer.SetBackgroundColour(wx.Colour(240, 240, 240))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.status_label = wx.StaticText(footer, label="Ready")
        self.status_label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.status_label.SetForegroundColour(wx.Colour(100, 100, 100))
        sizer.Add(self.status_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
        
        brand = wx.StaticText(footer, label="Built with ❤ by PCBtools.xyz")
        brand.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        brand.SetForegroundColour(wx.Colour(100, 100, 100))
        sizer.Add(brand, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        footer.SetSizer(sizer)
        footer.SetMinSize((-1, 22))
        return footer
    
    def _update_status(self, msg):
        """Update status."""
        self.status_label.SetLabel(msg)
        wx.CallLater(3000, lambda: self.status_label.SetLabel("Ready") if self.status_label else None)
    
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
            self._modified = False
    
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
        
        self._modified = False
    
    def _save_notes(self):
        """Save notes."""
        try:
            self.notes_manager.save(self.text_editor.GetValue())
            self._update_status("Saved ✓")
        except:
            pass
    
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
    
    def force_save(self):
        """Force save all."""
        self._save_notes()
        self._save_todos()
    
    def cleanup(self):
        """Cleanup."""
        if self._auto_save_timer:
            self._auto_save_timer.Stop()
