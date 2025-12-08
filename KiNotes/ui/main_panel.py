"""
KiNotes Main Panel - Blender-Style Modern UI
Tab 1: Notes | Tab 2: Todo List | Tab 3: BOM Tool
Inspired by Blender's 2024+ interface design
"""
import wx
import wx.lib.scrolledpanel as scrolled
import os
import datetime


# ============================================================
# BLENDER-STYLE COLOR SCHEME
# ============================================================
class Colors:
    """Blender-inspired dark theme colors."""
    # Main backgrounds - Blender's signature dark grays
    BG_DARKEST = wx.Colour(30, 30, 30)       # Deepest background
    BG_DARK = wx.Colour(42, 42, 42)          # Primary background
    BG_MEDIUM = wx.Colour(53, 53, 53)        # Secondary/panels
    BG_LIGHT = wx.Colour(66, 66, 66)         # Elevated elements
    BG_HOVER = wx.Colour(76, 76, 76)         # Hover state
    
    # Accent - Blender's signature blue-orange
    ACCENT_BLUE = wx.Colour(76, 165, 224)    # Primary accent (Blender blue)
    ACCENT_ORANGE = wx.Colour(237, 139, 38)  # Secondary accent
    ACCENT_GREEN = wx.Colour(96, 186, 96)    # Success green
    ACCENT_RED = wx.Colour(224, 96, 96)      # Error/delete red
    
    # Text colors
    TEXT_WHITE = wx.Colour(255, 255, 255)    # Primary text
    TEXT_BRIGHT = wx.Colour(230, 230, 230)   # Standard text
    TEXT_NORMAL = wx.Colour(200, 200, 200)   # Normal text
    TEXT_DIM = wx.Colour(140, 140, 140)      # Muted text
    TEXT_DARK = wx.Colour(100, 100, 100)     # Disabled text
    
    # Special
    BORDER = wx.Colour(28, 28, 28)           # Dark borders
    BORDER_LIGHT = wx.Colour(60, 60, 60)     # Light borders
    SELECTION = wx.Colour(66, 133, 188)      # Selection blue
    
    # Editor - high contrast
    EDITOR_BG = wx.Colour(20, 20, 20)        # Nearly black
    EDITOR_TEXT = wx.Colour(255, 255, 255)   # Pure white


# ============================================================
# ICONS - Unicode symbols that work across platforms
# ============================================================
class Icons:
    """Unicode icons for Blender-style interface."""
    # Tabs
    NOTES = "▤"       # Document/lines
    TODO = "☑"        # Checkbox
    BOM = "▦"         # Grid/table
    
    # Actions  
    IMPORT = "↓"      # Download arrow
    EXPORT = "↑"      # Upload arrow
    SAVE = "●"        # Disk/dot
    PDF = "◫"         # Document
    ADD = "+"         # Plus
    DELETE = "×"      # X mark
    CLEAR = "○"       # Circle/clear
    TITLE = "T"       # Title text
    DATE = "◷"        # Clock/calendar
    BOARD = "▢"       # Board outline
    LAYERS = "≡"      # Stacked layers
    DRILL = "◉"       # Drill hole
    RULES = "⚙"       # Gear
    GENERATE = "▶"    # Play/generate
    CHECK = "✓"       # Checkmark
    UNCHECK = "○"     # Empty circle


# ============================================================
# MAIN PANEL
# ============================================================
class KiNotesMainPanel(wx.Panel):
    """Main panel with Blender-style modern tabbed UI."""
    
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
        
        # Safe initialization
        try:
            self._init_ui()
            self._load_all_data()
            # No auto-insert header - start with empty notes
            self._start_auto_save_timer()
        except Exception as e:
            print(f"KiNotes UI init error: {e}")
    
    def _init_ui(self):
        """Initialize Blender-style tabbed UI."""
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
        """Create Blender-style tab bar."""
        tab_bar = wx.Panel(self)
        tab_bar.SetBackgroundColour(Colors.BG_DARKEST)
        tab_bar.SetMinSize((-1, 48))  # Taller tab bar
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(12)
        
        self.tab_buttons = []
        tabs = [
            (f"{Icons.NOTES}  Notes", 0),
            (f"{Icons.TODO}  Todo", 1),
            (f"{Icons.BOM}  BOM", 2)
        ]
        
        for label, idx in tabs:
            btn = wx.Button(tab_bar, label=label, size=(100, 38), style=wx.BORDER_NONE)
            btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            btn.Bind(wx.EVT_BUTTON, lambda e, i=idx: self._on_tab_click(i))
            btn.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            self.tab_buttons.append(btn)
            sizer.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        sizer.AddStretchSpacer()
        tab_bar.SetSizer(sizer)
        wx.CallAfter(self._update_tab_styles, 0)
        return tab_bar
    
    def _update_tab_styles(self, active_idx):
        """Update tab button styles - Blender style."""
        for i, btn in enumerate(self.tab_buttons):
            try:
                if i == active_idx:
                    btn.SetBackgroundColour(Colors.ACCENT_BLUE)
                    btn.SetForegroundColour(Colors.TEXT_WHITE)
                else:
                    btn.SetBackgroundColour(Colors.BG_MEDIUM)
                    btn.SetForegroundColour(Colors.TEXT_DIM)
                btn.Refresh()
            except Exception:
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
            except Exception:
                pass
        elif idx == 2:
            self.bom_panel.Show()
            try:
                self.bom_panel.FitInside()
            except Exception:
                pass
        
        self.content_panel.Layout()
        self.Layout()
        self.Refresh()
    
    # ============================================================
    # TAB 1: NOTES
    # ============================================================
    
    def _create_notes_tab(self, parent):
        """Create Notes tab with Blender-style editor."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(Colors.BG_DARK)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar - Blender style
        toolbar = wx.Panel(panel)
        toolbar.SetBackgroundColour(Colors.BG_MEDIUM)
        toolbar.SetMinSize((-1, 44))
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tb_sizer.AddSpacer(10)
        
        # Import dropdown button
        import_btn = wx.Button(toolbar, label=f"{Icons.IMPORT}  Import", size=(100, 34), style=wx.BORDER_NONE)
        import_btn.SetBackgroundColour(Colors.BG_LIGHT)
        import_btn.SetForegroundColour(Colors.TEXT_BRIGHT)
        import_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        import_btn.Bind(wx.EVT_BUTTON, self._on_import_click)
        tb_sizer.Add(import_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        # PDF button
        pdf_btn = wx.Button(toolbar, label=f"{Icons.PDF}  PDF", size=(80, 34), style=wx.BORDER_NONE)
        pdf_btn.SetBackgroundColour(Colors.BG_LIGHT)
        pdf_btn.SetForegroundColour(Colors.TEXT_BRIGHT)
        pdf_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        pdf_btn.Bind(wx.EVT_BUTTON, lambda e: self._on_export_pdf())
        tb_sizer.Add(pdf_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        # Save button - accent color
        save_btn = wx.Button(toolbar, label=f"{Icons.SAVE}  Save", size=(90, 34), style=wx.BORDER_NONE)
        save_btn.SetBackgroundColour(Colors.ACCENT_GREEN)
        save_btn.SetForegroundColour(Colors.TEXT_WHITE)
        save_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        save_btn.Bind(wx.EVT_BUTTON, lambda e: self._on_manual_save())
        tb_sizer.Add(save_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        tb_sizer.AddStretchSpacer()
        toolbar.SetSizer(tb_sizer)
        sizer.Add(toolbar, 0, wx.EXPAND)
        
        # Separator line
        sep = wx.Panel(panel, size=(-1, 1))
        sep.SetBackgroundColour(Colors.BORDER)
        sizer.Add(sep, 0, wx.EXPAND)
        
        # Text editor - high contrast black/white
        self.text_editor = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_RICH2 | wx.BORDER_NONE
        )
        self.text_editor.SetBackgroundColour(Colors.EDITOR_BG)
        self.text_editor.SetForegroundColour(Colors.EDITOR_TEXT)
        self.text_editor.SetFont(wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.text_editor.Bind(wx.EVT_TEXT, self._on_text_changed)
        self.text_editor.Bind(wx.EVT_LEFT_DOWN, self._on_text_click)
        sizer.Add(self.text_editor, 1, wx.EXPAND | wx.ALL, 6)
        
        panel.SetSizer(sizer)
        return panel
    
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
        toolbar.SetMinSize((-1, 44))
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tb_sizer.AddSpacer(10)
        
        # Add task button - accent
        add_btn = wx.Button(toolbar, label=f"{Icons.ADD}  Add Task", size=(110, 34), style=wx.BORDER_NONE)
        add_btn.SetBackgroundColour(Colors.ACCENT_BLUE)
        add_btn.SetForegroundColour(Colors.TEXT_WHITE)
        add_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        add_btn.Bind(wx.EVT_BUTTON, self._on_add_todo)
        tb_sizer.Add(add_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        # Clear done button
        clear_btn = wx.Button(toolbar, label=f"{Icons.CLEAR}  Clear Done", size=(120, 34), style=wx.BORDER_NONE)
        clear_btn.SetBackgroundColour(Colors.BG_LIGHT)
        clear_btn.SetForegroundColour(Colors.TEXT_BRIGHT)
        clear_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        clear_btn.Bind(wx.EVT_BUTTON, self._on_clear_done)
        tb_sizer.Add(clear_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        tb_sizer.AddStretchSpacer()
        
        # Counter
        self.todo_count = wx.StaticText(toolbar, label="0 / 0")
        self.todo_count.SetForegroundColour(Colors.TEXT_DIM)
        self.todo_count.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        tb_sizer.Add(self.todo_count, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 14)
        
        toolbar.SetSizer(tb_sizer)
        sizer.Add(toolbar, 0, wx.EXPAND)
        
        # Separator
        sep = wx.Panel(panel, size=(-1, 1))
        sep.SetBackgroundColour(Colors.BORDER)
        sizer.Add(sep, 0, wx.EXPAND)
        
        # Todo list scroll area
        self.todo_scroll = scrolled.ScrolledPanel(panel)
        self.todo_scroll.SetBackgroundColour(Colors.BG_DARK)
        self.todo_scroll.SetupScrolling(scroll_x=False)
        
        self.todo_sizer = wx.BoxSizer(wx.VERTICAL)
        self.todo_sizer.AddSpacer(6)
        self.todo_scroll.SetSizer(self.todo_sizer)
        sizer.Add(self.todo_scroll, 1, wx.EXPAND | wx.ALL, 6)
        
        panel.SetSizer(sizer)
        return panel
    
    def _add_todo_item(self, text="", done=False):
        """Add a todo item with Blender styling."""
        item_id = self._todo_id_counter
        self._todo_id_counter += 1
        
        item_panel = wx.Panel(self.todo_scroll)
        item_panel.SetBackgroundColour(Colors.BG_MEDIUM)
        item_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Checkbox
        cb = wx.CheckBox(item_panel)
        cb.SetValue(done)
        cb.SetBackgroundColour(Colors.BG_MEDIUM)
        cb.Bind(wx.EVT_CHECKBOX, lambda e, iid=item_id: self._on_todo_toggle(iid))
        item_sizer.Add(cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)
        
        # Text input
        txt = wx.TextCtrl(item_panel, value=text, style=wx.BORDER_NONE | wx.TE_PROCESS_ENTER)
        txt.SetBackgroundColour(Colors.BG_MEDIUM)
        txt.SetForegroundColour(Colors.TEXT_DARK if done else Colors.TEXT_BRIGHT)
        txt.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        txt.Bind(wx.EVT_TEXT, lambda e: self._save_todos())
        txt.Bind(wx.EVT_TEXT_ENTER, lambda e: self._on_add_todo(None))
        item_sizer.Add(txt, 1, wx.EXPAND | wx.ALL, 8)
        
        # Delete button
        del_btn = wx.Button(item_panel, label=Icons.DELETE, size=(32, 32), style=wx.BORDER_NONE)
        del_btn.SetBackgroundColour(Colors.BG_MEDIUM)
        del_btn.SetForegroundColour(Colors.ACCENT_RED)
        del_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        del_btn.Bind(wx.EVT_BUTTON, lambda e, iid=item_id: self._on_delete_todo(iid))
        item_sizer.Add(del_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        item_panel.SetSizer(item_sizer)
        
        self._todo_items.append({
            'id': item_id,
            'panel': item_panel,
            'checkbox': cb,
            'text': txt,
            'done': done
        })
        
        self.todo_sizer.Add(item_panel, 0, wx.EXPAND | wx.BOTTOM, 4)
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
                    Colors.TEXT_DARK if item['done'] else Colors.TEXT_BRIGHT
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
        self.todo_count.SetLabel(f"{done} / {total}")
    
    # ============================================================
    # TAB 3: BOM TOOL
    # ============================================================
    
    def _create_bom_tab(self, parent):
        """Create BOM Tool tab with Blender styling."""
        panel = scrolled.ScrolledPanel(parent)
        panel.SetBackgroundColour(Colors.BG_DARK)
        panel.SetupScrolling(scroll_x=False)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(12)
        
        # Section helper
        def add_section(title, checkboxes):
            # Section header
            header = wx.StaticText(panel, label=f"  {title}")
            header.SetForegroundColour(Colors.TEXT_DIM)
            header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            sizer.Add(header, 0, wx.LEFT | wx.BOTTOM, 8)
            
            # Options panel
            opt_panel = wx.Panel(panel)
            opt_panel.SetBackgroundColour(Colors.BG_MEDIUM)
            opt_sizer = wx.BoxSizer(wx.VERTICAL)
            
            widgets = []
            for label, default in checkboxes:
                cb = wx.CheckBox(opt_panel, label=f"  {label}")
                cb.SetValue(default)
                cb.SetForegroundColour(Colors.TEXT_NORMAL)
                cb.SetBackgroundColour(Colors.BG_MEDIUM)
                cb.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
                opt_sizer.Add(cb, 0, wx.ALL, 8)
                widgets.append(cb)
            
            opt_panel.SetSizer(opt_sizer)
            sizer.Add(opt_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
            return widgets
        
        # Columns section
        cols = add_section("COLUMNS", [
            ("Show quantity", True),
            ("Show value", True),
            ("Show footprint", True),
            ("Show references", True),
        ])
        self.bom_show_qty, self.bom_show_value, self.bom_show_fp, self.bom_show_refs = cols
        
        # Filters section
        filters = add_section("FILTERS", [
            ("Exclude DNP", True),
            ("Exclude virtual", True),
            ("Exclude fiducials (FID*)", True),
            ("Exclude test points (TP*)", True),
            ("Exclude mounting holes (MH*)", True),
        ])
        self.bom_exclude_dnp, self.bom_exclude_virtual, self.bom_exclude_fid, self.bom_exclude_tp, self.bom_exclude_mh = filters
        
        # Grouping header
        grp_header = wx.StaticText(panel, label="  GROUPING")
        grp_header.SetForegroundColour(Colors.TEXT_DIM)
        grp_header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(grp_header, 0, wx.LEFT | wx.BOTTOM, 8)
        
        self.bom_group_by = wx.Choice(panel, choices=[
            "  Value + Footprint",
            "  Value only",
            "  Footprint only",
            "  No grouping"
        ])
        self.bom_group_by.SetSelection(0)
        self.bom_group_by.SetBackgroundColour(Colors.BG_MEDIUM)
        self.bom_group_by.SetForegroundColour(Colors.TEXT_NORMAL)
        sizer.Add(self.bom_group_by, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Sort header
        sort_header = wx.StaticText(panel, label="  SORT BY")
        sort_header.SetForegroundColour(Colors.TEXT_DIM)
        sort_header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(sort_header, 0, wx.LEFT | wx.BOTTOM, 8)
        
        self.bom_sort_by = wx.Choice(panel, choices=[
            "  Reference (natural)",
            "  Value",
            "  Footprint",
            "  Quantity"
        ])
        self.bom_sort_by.SetSelection(0)
        self.bom_sort_by.SetBackgroundColour(Colors.BG_MEDIUM)
        self.bom_sort_by.SetForegroundColour(Colors.TEXT_NORMAL)
        sizer.Add(self.bom_sort_by, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Blacklist header
        bl_header = wx.StaticText(panel, label="  CUSTOM BLACKLIST")
        bl_header.SetForegroundColour(Colors.TEXT_DIM)
        bl_header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(bl_header, 0, wx.LEFT | wx.BOTTOM, 8)
        
        self.bom_blacklist = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 60))
        self.bom_blacklist.SetBackgroundColour(Colors.EDITOR_BG)
        self.bom_blacklist.SetForegroundColour(Colors.EDITOR_TEXT)
        self.bom_blacklist.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.bom_blacklist.SetHint("e.g. LOGO*, H* (one per line)")
        sizer.Add(self.bom_blacklist, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Generate button - large accent
        gen_btn = wx.Button(panel, label=f"{Icons.GENERATE}  Generate BOM to Notes", size=(-1, 48), style=wx.BORDER_NONE)
        gen_btn.SetBackgroundColour(Colors.ACCENT_BLUE)
        gen_btn.SetForegroundColour(Colors.TEXT_WHITE)
        gen_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
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
            self._update_status(f"BOM error: {str(e)[:30]}")
    
    def _generate_bom_text(self):
        """Generate BOM text - safe pcbnew access."""
        try:
            import pcbnew
            import fnmatch
        except ImportError:
            return "## BOM\n\n*pcbnew not available*\n"
        
        try:
            board = pcbnew.GetBoard()
            if not board:
                return "## BOM\n\n*No board loaded*\n"
        except Exception:
            return "## BOM\n\n*Could not access board*\n"
        
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
        try:
            for fp in board.GetFootprints():
                ref = fp.GetReference()
                value = fp.GetValue()
                footprint = fp.GetFPIDAsString().split(":")[-1] if fp.GetFPIDAsString() else ""
                
                if self.bom_exclude_dnp.GetValue():
                    try:
                        attrs = fp.GetAttributes()
                        if hasattr(pcbnew, 'FP_EXCLUDE_FROM_BOM') and (attrs & pcbnew.FP_EXCLUDE_FROM_BOM):
                            continue
                    except Exception:
                        pass
                
                if self.bom_exclude_virtual.GetValue():
                    try:
                        attrs = fp.GetAttributes()
                        if hasattr(pcbnew, 'FP_BOARD_ONLY') and (attrs & pcbnew.FP_BOARD_ONLY):
                            continue
                    except Exception:
                        pass
                
                skip = False
                for pattern in blacklist:
                    if fnmatch.fnmatch(ref.upper(), pattern.upper()):
                        skip = True
                        break
                if skip:
                    continue
                
                components.append({'ref': ref, 'value': value, 'footprint': footprint})
        except Exception as e:
            return f"## BOM\n\n*Error reading components: {e}*\n"
        
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
        """Show import menu with Title/Date options."""
        menu = wx.Menu()
        
        # Header section
        menu.Append(wx.ID_ANY, "── Extract from Board ──").Enable(False)
        
        items = [
            (f"{Icons.TITLE}  Project Title", "title"),
            (f"{Icons.DATE}  Project Date", "date"),
            (f"{Icons.BOARD}  Board Info", "board_size"),
            (f"{Icons.LAYERS}  Stackup", "stackup"),
            ("    Netlist", "netlist"),
            (f"{Icons.LAYERS}  Layers", "layers"),
            (f"{Icons.DRILL}  Drill Table", "drill_table"),
            (f"{Icons.RULES}  Design Rules", "design_rules"),
            ("    Diff Pairs", "diff_pairs"),
        ]
        
        for label, meta_type in items:
            mi = menu.Append(wx.ID_ANY, label)
            self.Bind(wx.EVT_MENU, lambda e, t=meta_type: self._import_metadata(t), mi)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def _import_metadata(self, meta_type):
        """Import metadata with safe pcbnew access."""
        try:
            # Handle special title/date cases
            if meta_type == "title":
                text = self._extract_title()
            elif meta_type == "date":
                text = self._extract_date()
            else:
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
            self._update_status(f"Import error")
    
    def _extract_title(self):
        """Extract project title from board."""
        try:
            import pcbnew
            board = pcbnew.GetBoard()
            if not board:
                return "# Untitled Project"
            
            filename = board.GetFileName()
            project_name = os.path.splitext(os.path.basename(filename))[0] if filename else "Untitled"
            
            title_block = board.GetTitleBlock()
            title = title_block.GetTitle() if title_block else ""
            company = title_block.GetCompany() if title_block else ""
            revision = title_block.GetRevision() if title_block else ""
            
            lines = [f"# {title or project_name}"]
            if company:
                lines.append(f"**Author:** {company}")
            if revision:
                lines.append(f"**Revision:** {revision}")
            lines.append("")
            
            return "\n".join(lines)
        except Exception:
            return "# Project Title\n"
    
    def _extract_date(self):
        """Extract project date from board."""
        try:
            import pcbnew
            board = pcbnew.GetBoard()
            if board:
                title_block = board.GetTitleBlock()
                date = title_block.GetDate() if title_block else ""
                if date:
                    return f"**Date:** {date}"
        except Exception:
            pass
        
        return f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d')}"
    
    def _on_export_pdf(self):
        """Export notes to PDF."""
        try:
            content = self.text_editor.GetValue()
            filepath = self.pdf_exporter.export(content)
            if filepath:
                self._update_status("PDF exported")
        except Exception as e:
            self._update_status("PDF export failed")
    
    def _on_manual_save(self):
        """Manual save with feedback."""
        try:
            self._save_notes()
            self._save_todos()
            self._update_status(f"{Icons.CHECK} Saved")
        except Exception:
            self._update_status("Save failed")
    
    def _on_text_changed(self, event):
        self._modified = True
        event.Skip()
    
    def _on_text_click(self, event):
        """Handle @REF clicks for component highlighting."""
        try:
            pos = self.text_editor.HitTestPos(event.GetPosition())[1]
            if pos >= 0:
                text = self.text_editor.GetValue()
                word = self._get_word_at_pos(text, pos)
                if word.startswith('@'):
                    self._highlight_component(word[1:])
                    return
        except Exception:
            pass
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
        """Highlight component in PCB - safe."""
        try:
            if self.designator_linker.highlight(ref):
                self._update_status(f"→ {ref}")
        except Exception:
            pass
    
    # ============================================================
    # DATA / FOOTER
    # ============================================================
    
    def _create_footer(self):
        """Create Blender-style footer."""
        footer = wx.Panel(self)
        footer.SetBackgroundColour(Colors.BG_DARKEST)
        footer.SetMinSize((-1, 28))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.status_label = wx.StaticText(footer, label="Ready")
        self.status_label.SetForegroundColour(Colors.TEXT_DIM)
        self.status_label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.status_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)
        
        brand = wx.StaticText(footer, label="PCBtools.xyz")
        brand.SetForegroundColour(Colors.TEXT_DARK)
        brand.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(brand, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        footer.SetSizer(sizer)
        return footer
    
    def _update_status(self, msg):
        """Update status with auto-clear."""
        try:
            self.status_label.SetLabel(msg)
            wx.CallLater(3000, lambda: self.status_label.SetLabel("Ready") if self.status_label else None)
        except Exception:
            pass
    
    def _start_auto_save_timer(self):
        """Start auto-save timer - safe."""
        try:
            self._auto_save_timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self._on_auto_save, self._auto_save_timer)
            self._auto_save_timer.Start(5000)
        except Exception:
            pass
    
    def _on_auto_save(self, event):
        """Auto-save if modified."""
        if self._modified:
            try:
                self._save_notes()
                self._save_todos()
                self._modified = False
            except Exception:
                pass
    
    def _load_all_data(self):
        """Load saved data - safe."""
        try:
            content = self.notes_manager.load()
            if content:
                self.text_editor.SetValue(content)
        except Exception:
            pass
        
        try:
            todos = self.notes_manager.load_todos()
            for todo in todos:
                self._add_todo_item(todo.get('text', ''), todo.get('done', False))
        except Exception:
            pass
        
        self._modified = False
    
    def _save_notes(self):
        """Save notes - safe."""
        try:
            self.notes_manager.save(self.text_editor.GetValue())
        except Exception:
            pass
    
    def _save_todos(self):
        """Save todos - safe."""
        try:
            todos = [{'text': item['text'].GetValue(), 'done': item['checkbox'].GetValue()} 
                     for item in self._todo_items]
            self.notes_manager.save_todos(todos)
        except Exception:
            pass
    
    def force_save(self):
        """Force save all data."""
        self._save_notes()
        self._save_todos()
    
    def cleanup(self):
        """Cleanup timer resources."""
        try:
            if self._auto_save_timer:
                self._auto_save_timer.Stop()
        except Exception:
            pass
