"""
KiNotes Main Panel - Modern UI with Tabs
Tab 1: Notes | Tab 2: Todo List | Tab 3: BOM Tool
"""
import wx
import wx.lib.scrolledpanel as scrolled
import os
import datetime

# Modern color scheme
class Colors:
    # Dark theme (matches KiCad dark mode)
    BG_DARK = wx.Colour(45, 45, 48)
    BG_MEDIUM = wx.Colour(60, 60, 65)
    BG_LIGHT = wx.Colour(75, 75, 80)
    
    # Accent colors
    ACCENT = wx.Colour(0, 122, 204)  # Blue
    ACCENT_HOVER = wx.Colour(30, 144, 220)
    SUCCESS = wx.Colour(76, 175, 80)  # Green
    WARNING = wx.Colour(255, 152, 0)  # Orange
    
    # Text
    TEXT_PRIMARY = wx.Colour(220, 220, 220)
    TEXT_SECONDARY = wx.Colour(160, 160, 160)
    TEXT_MUTED = wx.Colour(120, 120, 120)
    
    # Tab bar
    TAB_BG = wx.Colour(37, 37, 38)
    TAB_ACTIVE = wx.Colour(0, 122, 204)
    TAB_INACTIVE = wx.Colour(60, 60, 65)
    
    # Editor
    EDITOR_BG = wx.Colour(30, 30, 30)
    EDITOR_TEXT = wx.Colour(212, 212, 212)
    
    # Borders
    BORDER = wx.Colour(70, 70, 75)


class KiNotesMainPanel(wx.Panel):
    """Main panel with modern tabbed UI."""
    
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
        
        self.SetBackgroundColour(Colors.BG_DARK)
        
        self._init_ui()
        self._load_all_data()
        self._auto_insert_header()
        self._start_auto_save_timer()
    
    def _init_ui(self):
        """Initialize modern tabbed UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # === TAB BAR ===
        self.tab_bar = self._create_tab_bar()
        main_sizer.Add(self.tab_bar, 0, wx.EXPAND)
        
        # === CONTENT AREA ===
        self.content_panel = wx.Panel(self)
        self.content_panel.SetBackgroundColour(Colors.BG_DARK)
        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create all tab panels
        self.notes_panel = self._create_notes_tab(self.content_panel)
        self.todo_panel = self._create_todo_tab(self.content_panel)
        self.bom_panel = self._create_bom_tab(self.content_panel)
        
        self.content_sizer.Add(self.notes_panel, 1, wx.EXPAND)
        self.content_sizer.Add(self.todo_panel, 1, wx.EXPAND)
        self.content_sizer.Add(self.bom_panel, 1, wx.EXPAND)
        
        self.content_panel.SetSizer(self.content_sizer)
        main_sizer.Add(self.content_panel, 1, wx.EXPAND)
        
        # === FOOTER ===
        footer = self._create_footer()
        main_sizer.Add(footer, 0, wx.EXPAND)
        
        self.SetSizer(main_sizer)
        self._show_tab(0)
    
    def _create_tab_bar(self):
        """Create modern tab bar."""
        tab_bar = wx.Panel(self)
        tab_bar.SetBackgroundColour(Colors.TAB_BG)
        tab_bar.SetMinSize((-1, 40))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(8)
        
        self.tab_buttons = []
        tabs = [("📝 Notes", 0), ("☑ Todo", 1), ("📋 BOM", 2)]
        
        for label, idx in tabs:
            btn = wx.Button(tab_bar, label=label, size=(80, 32), style=wx.BORDER_NONE)
            btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            btn.Bind(wx.EVT_BUTTON, lambda e, i=idx: self._on_tab_click(i))
            btn.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            self.tab_buttons.append(btn)
            sizer.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        
        sizer.AddStretchSpacer()
        tab_bar.SetSizer(sizer)
        wx.CallAfter(self._update_tab_styles, 0)
        return tab_bar
    
    def _update_tab_styles(self, active_idx):
        """Update tab button styles."""
        for i, btn in enumerate(self.tab_buttons):
            try:
                if i == active_idx:
                    btn.SetBackgroundColour(Colors.TAB_ACTIVE)
                    btn.SetForegroundColour(wx.Colour(255, 255, 255))
                else:
                    btn.SetBackgroundColour(Colors.TAB_INACTIVE)
                    btn.SetForegroundColour(Colors.TEXT_SECONDARY)
                btn.Refresh()
            except:
                pass
    
    def _on_tab_click(self, idx):
        self._show_tab(idx)
    
    def _show_tab(self, idx):
        """Show selected tab."""
        self._current_tab = idx
        self._update_tab_styles(idx)
        
        self.notes_panel.Hide()
        self.todo_panel.Hide()
        self.bom_panel.Hide()
        
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
        
        self.content_panel.Layout()
        self.Layout()
        self.Refresh()
    
    # ============================================================
    # TAB 1: NOTES
    # ============================================================
    
    def _create_notes_tab(self, parent):
        """Create Notes tab with modern editor."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(Colors.BG_DARK)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar
        toolbar = wx.Panel(panel)
        toolbar.SetBackgroundColour(Colors.BG_MEDIUM)
        toolbar.SetMinSize((-1, 36))
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tb_sizer.AddSpacer(8)
        
        # Modern styled buttons
        btn_style = wx.BORDER_NONE
        btn_size = (70, 28)
        
        import_btn = wx.Button(toolbar, label="⬇ Import", size=btn_size, style=btn_style)
        import_btn.SetBackgroundColour(Colors.BG_LIGHT)
        import_btn.SetForegroundColour(Colors.TEXT_PRIMARY)
        import_btn.Bind(wx.EVT_BUTTON, self._on_import_click)
        tb_sizer.Add(import_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        
        pdf_btn = wx.Button(toolbar, label="📄 PDF", size=(60, 28), style=btn_style)
        pdf_btn.SetBackgroundColour(Colors.BG_LIGHT)
        pdf_btn.SetForegroundColour(Colors.TEXT_PRIMARY)
        pdf_btn.Bind(wx.EVT_BUTTON, lambda e: self._on_export_pdf())
        tb_sizer.Add(pdf_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        
        save_btn = wx.Button(toolbar, label="💾 Save", size=(60, 28), style=btn_style)
        save_btn.SetBackgroundColour(Colors.SUCCESS)
        save_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        save_btn.Bind(wx.EVT_BUTTON, lambda e: self._on_manual_save())
        tb_sizer.Add(save_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        tb_sizer.AddStretchSpacer()
        toolbar.SetSizer(tb_sizer)
        sizer.Add(toolbar, 0, wx.EXPAND)
        
        # Text editor with dark theme
        self.text_editor = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_RICH2 | wx.BORDER_NONE
        )
        self.text_editor.SetBackgroundColour(Colors.EDITOR_BG)
        self.text_editor.SetForegroundColour(Colors.EDITOR_TEXT)
        self.text_editor.SetFont(wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.text_editor.Bind(wx.EVT_TEXT, self._on_text_changed)
        self.text_editor.Bind(wx.EVT_LEFT_DOWN, self._on_text_click)
        sizer.Add(self.text_editor, 1, wx.EXPAND | wx.ALL, 4)
        
        panel.SetSizer(sizer)
        return panel
    
    def _auto_insert_header(self):
        """Auto-insert project header if notes are empty."""
        current = self.text_editor.GetValue().strip()
        if current:
            return
        
        try:
            import pcbnew
            board = pcbnew.GetBoard()
            if not board:
                return
            
            filename = board.GetFileName()
            project_name = os.path.splitext(os.path.basename(filename))[0] if filename else "Untitled"
            
            title_block = board.GetTitleBlock()
            title = title_block.GetTitle() or project_name
            author = title_block.GetCompany() or ""
            revision = title_block.GetRevision() or ""
            date = title_block.GetDate() or datetime.datetime.now().strftime("%Y-%m-%d")
            
            header_lines = [f"# {title}"]
            if author:
                header_lines.append(f"Author: {author}")
            if revision:
                header_lines.append(f"Revision: {revision}")
            header_lines.append(f"Date: {date}")
            header_lines.append("")
            header_lines.append("─" * 40)
            header_lines.append("")
            
            self.text_editor.SetValue("\n".join(header_lines))
            self.text_editor.SetInsertionPointEnd()
        except:
            pass
    
    # ============================================================
    # TAB 2: TODO LIST
    # ============================================================
    
    def _create_todo_tab(self, parent):
        """Create Todo tab with checkboxes."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(Colors.BG_DARK)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar
        toolbar = wx.Panel(panel)
        toolbar.SetBackgroundColour(Colors.BG_MEDIUM)
        toolbar.SetMinSize((-1, 36))
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tb_sizer.AddSpacer(8)
        
        add_btn = wx.Button(toolbar, label="+ Add Task", size=(85, 28), style=wx.BORDER_NONE)
        add_btn.SetBackgroundColour(Colors.ACCENT)
        add_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        add_btn.Bind(wx.EVT_BUTTON, self._on_add_todo)
        tb_sizer.Add(add_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        
        clear_btn = wx.Button(toolbar, label="Clear Done", size=(80, 28), style=wx.BORDER_NONE)
        clear_btn.SetBackgroundColour(Colors.BG_LIGHT)
        clear_btn.SetForegroundColour(Colors.TEXT_PRIMARY)
        clear_btn.Bind(wx.EVT_BUTTON, self._on_clear_done)
        tb_sizer.Add(clear_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        tb_sizer.AddStretchSpacer()
        
        self.todo_count = wx.StaticText(toolbar, label="0/0")
        self.todo_count.SetForegroundColour(Colors.TEXT_SECONDARY)
        self.todo_count.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        tb_sizer.Add(self.todo_count, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        toolbar.SetSizer(tb_sizer)
        sizer.Add(toolbar, 0, wx.EXPAND)
        
        # Todo list
        self.todo_scroll = scrolled.ScrolledPanel(panel)
        self.todo_scroll.SetBackgroundColour(Colors.BG_DARK)
        self.todo_scroll.SetupScrolling(scroll_x=False)
        
        self.todo_sizer = wx.BoxSizer(wx.VERTICAL)
        self.todo_scroll.SetSizer(self.todo_sizer)
        sizer.Add(self.todo_scroll, 1, wx.EXPAND | wx.ALL, 4)
        
        panel.SetSizer(sizer)
        return panel
    
    def _add_todo_item(self, text="", done=False):
        """Add a todo item."""
        item_id = self._todo_id_counter
        self._todo_id_counter += 1
        
        item_panel = wx.Panel(self.todo_scroll)
        item_panel.SetBackgroundColour(Colors.BG_MEDIUM)
        item_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        cb = wx.CheckBox(item_panel)
        cb.SetValue(done)
        cb.SetBackgroundColour(Colors.BG_MEDIUM)
        cb.Bind(wx.EVT_CHECKBOX, lambda e, iid=item_id: self._on_todo_toggle(iid))
        item_sizer.Add(cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        
        txt = wx.TextCtrl(item_panel, value=text, style=wx.BORDER_NONE | wx.TE_PROCESS_ENTER)
        txt.SetBackgroundColour(Colors.BG_MEDIUM)
        txt.SetForegroundColour(Colors.TEXT_MUTED if done else Colors.TEXT_PRIMARY)
        txt.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        txt.Bind(wx.EVT_TEXT, lambda e: self._save_todos())
        txt.Bind(wx.EVT_TEXT_ENTER, lambda e: self._on_add_todo(None))
        item_sizer.Add(txt, 1, wx.EXPAND | wx.ALL, 6)
        
        del_btn = wx.Button(item_panel, label="✕", size=(26, 26), style=wx.BORDER_NONE)
        del_btn.SetBackgroundColour(Colors.BG_MEDIUM)
        del_btn.SetForegroundColour(wx.Colour(200, 80, 80))
        del_btn.Bind(wx.EVT_BUTTON, lambda e, iid=item_id: self._on_delete_todo(iid))
        item_sizer.Add(del_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        
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
        txt = self._add_todo_item()
        txt.SetFocus()
        self._save_todos()
    
    def _on_todo_toggle(self, item_id):
        for item in self._todo_items:
            if item['id'] == item_id:
                item['done'] = item['checkbox'].GetValue()
                item['text'].SetForegroundColour(
                    Colors.TEXT_MUTED if item['done'] else Colors.TEXT_PRIMARY
                )
                item['text'].Refresh()
                break
        self._update_todo_count()
        self._save_todos()
    
    def _on_delete_todo(self, item_id):
        for i, item in enumerate(self._todo_items):
            if item['id'] == item_id:
                item['panel'].Destroy()
                self._todo_items.pop(i)
                break
        self.todo_scroll.FitInside()
        self._update_todo_count()
        self._save_todos()
    
    def _on_clear_done(self, event):
        to_remove = [item for item in self._todo_items if item['done']]
        for item in to_remove:
            item['panel'].Destroy()
            self._todo_items.remove(item)
        self.todo_scroll.FitInside()
        self._update_todo_count()
        self._save_todos()
    
    def _update_todo_count(self):
        total = len(self._todo_items)
        done = sum(1 for item in self._todo_items if item['done'])
        self.todo_count.SetLabel(f"{done}/{total}")
    
    # ============================================================
    # TAB 3: BOM TOOL
    # ============================================================
    
    def _create_bom_tab(self, parent):
        """Create BOM Tool tab."""
        panel = scrolled.ScrolledPanel(parent)
        panel.SetBackgroundColour(Colors.BG_DARK)
        panel.SetupScrolling(scroll_x=False)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(8)
        
        # Helper to create section
        def add_section(title, checkboxes):
            box = wx.StaticBox(panel, label=title)
            box.SetForegroundColour(Colors.TEXT_PRIMARY)
            box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
            
            widgets = []
            for label, default in checkboxes:
                cb = wx.CheckBox(panel, label=label)
                cb.SetValue(default)
                cb.SetForegroundColour(Colors.TEXT_PRIMARY)
                box_sizer.Add(cb, 0, wx.ALL, 4)
                widgets.append(cb)
            
            sizer.Add(box_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
            return widgets
        
        # Columns section
        cols = add_section("Columns", [
            ("Show quantity", True),
            ("Show value", True),
            ("Show footprint", True),
            ("Show references", True),
        ])
        self.bom_show_qty, self.bom_show_value, self.bom_show_fp, self.bom_show_refs = cols
        
        # Filters section
        filters = add_section("Filters", [
            ("Exclude DNP", True),
            ("Exclude virtual", True),
            ("Exclude fiducials (FID*)", True),
            ("Exclude test points (TP*)", True),
            ("Exclude mounting holes (MH*)", True),
        ])
        self.bom_exclude_dnp, self.bom_exclude_virtual, self.bom_exclude_fid, self.bom_exclude_tp, self.bom_exclude_mh = filters
        
        # Grouping
        grp_box = wx.StaticBox(panel, label="Grouping")
        grp_box.SetForegroundColour(Colors.TEXT_PRIMARY)
        grp_sizer = wx.StaticBoxSizer(grp_box, wx.VERTICAL)
        
        self.bom_group_by = wx.Choice(panel, choices=[
            "Value + Footprint",
            "Value only",
            "Footprint only",
            "No grouping"
        ])
        self.bom_group_by.SetSelection(0)
        grp_sizer.Add(self.bom_group_by, 0, wx.EXPAND | wx.ALL, 4)
        sizer.Add(grp_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        
        # Sort
        sort_box = wx.StaticBox(panel, label="Sort by")
        sort_box.SetForegroundColour(Colors.TEXT_PRIMARY)
        sort_sizer = wx.StaticBoxSizer(sort_box, wx.VERTICAL)
        
        self.bom_sort_by = wx.Choice(panel, choices=[
            "Reference (natural)",
            "Value",
            "Footprint",
            "Quantity"
        ])
        self.bom_sort_by.SetSelection(0)
        sort_sizer.Add(self.bom_sort_by, 0, wx.EXPAND | wx.ALL, 4)
        sizer.Add(sort_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        
        # Custom blacklist
        bl_box = wx.StaticBox(panel, label="Custom Blacklist (one per line)")
        bl_box.SetForegroundColour(Colors.TEXT_PRIMARY)
        bl_sizer = wx.StaticBoxSizer(bl_box, wx.VERTICAL)
        
        self.bom_blacklist = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 60))
        self.bom_blacklist.SetBackgroundColour(Colors.EDITOR_BG)
        self.bom_blacklist.SetForegroundColour(Colors.EDITOR_TEXT)
        self.bom_blacklist.SetHint("e.g. LOGO*, H*")
        bl_sizer.Add(self.bom_blacklist, 0, wx.EXPAND | wx.ALL, 4)
        sizer.Add(bl_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        
        # Generate button
        gen_btn = wx.Button(panel, label="Generate BOM → Notes", size=(-1, 40), style=wx.BORDER_NONE)
        gen_btn.SetBackgroundColour(Colors.ACCENT)
        gen_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        gen_btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        gen_btn.Bind(wx.EVT_BUTTON, self._on_generate_bom)
        sizer.Add(gen_btn, 0, wx.EXPAND | wx.ALL, 12)
        
        panel.SetSizer(sizer)
        return panel
    
    def _on_generate_bom(self, event):
        """Generate BOM and insert into Notes."""
        try:
            bom_text = self._generate_bom_text()
            if bom_text:
                current = self.text_editor.GetValue()
                if current and not current.endswith("\n"):
                    current += "\n"
                current += "\n" + bom_text
                self.text_editor.SetValue(current)
                self.text_editor.SetInsertionPointEnd()
                self._show_tab(0)
                self._update_status("BOM added to notes")
        except Exception as e:
            wx.MessageBox(f"BOM generation failed: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _generate_bom_text(self):
        """Generate BOM text."""
        import pcbnew
        import fnmatch
        
        board = pcbnew.GetBoard()
        if not board:
            return None
        
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
        
        components = []
        for fp in board.GetFootprints():
            ref = fp.GetReference()
            value = fp.GetValue()
            footprint = fp.GetFPIDAsString().split(":")[-1] if fp.GetFPIDAsString() else ""
            
            if self.bom_exclude_dnp.GetValue():
                try:
                    attrs = fp.GetAttributes()
                    if hasattr(pcbnew, 'FP_EXCLUDE_FROM_BOM') and (attrs & pcbnew.FP_EXCLUDE_FROM_BOM):
                        continue
                except:
                    pass
            
            if self.bom_exclude_virtual.GetValue():
                try:
                    attrs = fp.GetAttributes()
                    if hasattr(pcbnew, 'FP_BOARD_ONLY') and (attrs & pcbnew.FP_BOARD_ONLY):
                        continue
                except:
                    pass
            
            skip = False
            for pattern in blacklist:
                if fnmatch.fnmatch(ref.upper(), pattern.upper()):
                    skip = True
                    break
            if skip:
                continue
            
            components.append({'ref': ref, 'value': value, 'footprint': footprint})
        
        if not components:
            return "## BOM\n\n*No components found*\n"
        
        # Group
        group_mode = self.bom_group_by.GetSelection()
        grouped = {}
        
        for comp in components:
            if group_mode == 0:
                key = (comp['value'], comp['footprint'])
            elif group_mode == 1:
                key = (comp['value'], "")
            elif group_mode == 2:
                key = ("", comp['footprint'])
            else:
                key = (comp['ref'], comp['value'], comp['footprint'])
            
            if key not in grouped:
                grouped[key] = {'value': comp['value'], 'footprint': comp['footprint'], 'refs': []}
            grouped[key]['refs'].append(comp['ref'])
        
        # Sort
        def natural_sort_key(ref):
            import re
            parts = re.split(r'(\d+)', ref)
            return [int(p) if p.isdigit() else p.lower() for p in parts]
        
        for group in grouped.values():
            group['refs'].sort(key=natural_sort_key)
        
        sort_mode = self.bom_sort_by.GetSelection()
        if sort_mode == 0:
            items = sorted(grouped.values(), key=lambda x: natural_sort_key(x['refs'][0]))
        elif sort_mode == 1:
            items = sorted(grouped.values(), key=lambda x: x['value'].lower())
        elif sort_mode == 2:
            items = sorted(grouped.values(), key=lambda x: x['footprint'].lower())
        else:
            items = sorted(grouped.values(), key=lambda x: -len(x['refs']))
        
        # Build output
        lines = ["## Bill of Materials", ""]
        
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
        try:
            content = self.text_editor.GetValue()
            filepath = self.pdf_exporter.export(content)
            if filepath:
                self._update_status("PDF exported")
                wx.MessageBox(f"Exported to:\n{filepath}", "Export", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Export failed: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_manual_save(self):
        self._save_notes()
        self._save_todos()
        self._update_status("Saved ✓")
    
    def _on_text_changed(self, event):
        self._modified = True
        event.Skip()
    
    def _on_text_click(self, event):
        pos = self.text_editor.HitTestPos(event.GetPosition())[1]
        if pos >= 0:
            text = self.text_editor.GetValue()
            word = self._get_word_at_pos(text, pos)
            if word.startswith('@'):
                self._highlight_component(word[1:])
                return
        event.Skip()
    
    def _get_word_at_pos(self, text, pos):
        if pos < 0 or pos >= len(text):
            return ""
        start = end = pos
        while start > 0 and (text[start-1].isalnum() or text[start-1] in '@_'):
            start -= 1
        while end < len(text) and (text[end].isalnum() or text[end] in '@_'):
            end += 1
        return text[start:end]
    
    def _highlight_component(self, ref):
        try:
            if self.designator_linker.highlight(ref):
                self._update_status(f"→ {ref}")
        except:
            pass
    
    # ============================================================
    # DATA / FOOTER
    # ============================================================
    
    def _create_footer(self):
        footer = wx.Panel(self)
        footer.SetBackgroundColour(Colors.TAB_BG)
        footer.SetMinSize((-1, 24))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.status_label = wx.StaticText(footer, label="Ready")
        self.status_label.SetForegroundColour(Colors.TEXT_MUTED)
        self.status_label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.status_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        
        brand = wx.StaticText(footer, label="PCBtools.xyz")
        brand.SetForegroundColour(Colors.TEXT_MUTED)
        brand.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(brand, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        footer.SetSizer(sizer)
        return footer
    
    def _update_status(self, msg):
        self.status_label.SetLabel(msg)
        wx.CallLater(3000, lambda: self.status_label.SetLabel("Ready") if self.status_label else None)
    
    def _start_auto_save_timer(self):
        self._auto_save_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_auto_save, self._auto_save_timer)
        self._auto_save_timer.Start(5000)
    
    def _on_auto_save(self, event):
        if self._modified:
            self._save_notes()
            self._save_todos()
            self._modified = False
    
    def _load_all_data(self):
        try:
            content = self.notes_manager.load()
            if content:
                self.text_editor.SetValue(content)
        except:
            pass
        
        try:
            todos = self.notes_manager.load_todos()
            for todo in todos:
                self._add_todo_item(todo.get('text', ''), todo.get('done', False))
        except:
            pass
        
        self._modified = False
    
    def _save_notes(self):
        try:
            self.notes_manager.save(self.text_editor.GetValue())
        except:
            pass
    
    def _save_todos(self):
        try:
            todos = [{'text': item['text'].GetValue(), 'done': item['checkbox'].GetValue()} 
                     for item in self._todo_items]
            self.notes_manager.save_todos(todos)
        except:
            pass
    
    def force_save(self):
        self._save_notes()
        self._save_todos()
    
    def cleanup(self):
        if self._auto_save_timer:
            self._auto_save_timer.Stop()
