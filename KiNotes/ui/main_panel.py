"""
KiNotes Main Panel - Clean Modern UI
Tab 1: Notes | Tab 2: Todo List | Tab 3: BOM Tool
User-selectable background and text colors
"""
import wx
import wx.lib.scrolledpanel as scrolled
import os
import datetime
import json


# ============================================================
# COLOR PRESETS - User Selectable
# ============================================================
BACKGROUND_COLORS = {
    "Snow Gray": "#F8F9FA",
    "Ivory Paper": "#FFFDF5",
    "Mint Mist": "#EAF7F1",
    "Sakura Mist": "#FAF1F4",
    "Storm Fog": "#E4E7EB",
}

TEXT_COLORS = {
    "Carbon Black": "#2B2B2B",
    "Deep Ink": "#1A1A1A",
    "Slate Night": "#36454F",
    "Cocoa Brown": "#4E342E",
    "Evergreen Ink": "#004D40",
}

def hex_to_colour(hex_str):
    """Convert hex color to wx.Colour."""
    hex_str = hex_str.lstrip('#')
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return wx.Colour(r, g, b)


# ============================================================
# UI COLORS (for buttons, panels, etc.)
# ============================================================
class Colors:
    """UI colors for panels and buttons."""
    # Panel backgrounds
    BG_PANEL = wx.Colour(245, 245, 245)      # Light gray panels
    BG_TOOLBAR = wx.Colour(235, 235, 235)    # Toolbar background
    BG_BUTTON = wx.Colour(225, 225, 225)     # Button background
    BG_BUTTON_HOVER = wx.Colour(210, 210, 210)
    
    # Accent colors
    ACCENT_BLUE = wx.Colour(66, 133, 244)    # Google blue
    ACCENT_GREEN = wx.Colour(52, 168, 83)    # Google green
    ACCENT_RED = wx.Colour(234, 67, 53)      # Google red
    
    # Text
    TEXT_PRIMARY = wx.Colour(32, 33, 36)     # Dark gray text
    TEXT_SECONDARY = wx.Colour(95, 99, 104)  # Medium gray
    TEXT_WHITE = wx.Colour(255, 255, 255)    # White text
    
    # Borders
    BORDER = wx.Colour(218, 220, 224)        # Light border
    BORDER_DARK = wx.Colour(180, 180, 180)   # Darker border


# ============================================================
# ICONS - Simple Unicode
# ============================================================
class Icons:
    NOTES = "📝"
    TODO = "✅"
    BOM = "📋"
    IMPORT = "📥"
    SAVE = "💾"
    PDF = "📄"
    ADD = "➕"
    DELETE = "✖"
    CLEAR = "🗑"
    SETTINGS = "⚙"
    GENERATE = "▶"


# ============================================================
# MAIN PANEL
# ============================================================
class KiNotesMainPanel(wx.Panel):
    """Main panel with tabs, color picker, and bottom action buttons."""
    
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
        
        # Default colors
        self._bg_color_name = "Ivory Paper"
        self._text_color_name = "Carbon Black"
        self._load_color_settings()
        
        self.SetBackgroundColour(Colors.BG_PANEL)
        
        try:
            self._init_ui()
            self._load_all_data()
            self._start_auto_save_timer()
        except Exception as e:
            print(f"KiNotes UI init error: {e}")
    
    def _load_color_settings(self):
        """Load saved color settings."""
        try:
            settings = self.notes_manager.load_settings()
            if settings:
                self._bg_color_name = settings.get('bg_color', 'Ivory Paper')
                self._text_color_name = settings.get('text_color', 'Carbon Black')
        except:
            pass
    
    def _save_color_settings(self):
        """Save color settings."""
        try:
            self.notes_manager.save_settings({
                'bg_color': self._bg_color_name,
                'text_color': self._text_color_name
            })
        except:
            pass
    
    def _get_editor_bg(self):
        return hex_to_colour(BACKGROUND_COLORS.get(self._bg_color_name, "#FFFDF5"))
    
    def _get_editor_text(self):
        return hex_to_colour(TEXT_COLORS.get(self._text_color_name, "#2B2B2B"))
    
    def _init_ui(self):
        """Initialize UI with new layout."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # === TOP BAR: Tabs + Import on same line ===
        self.top_bar = self._create_top_bar()
        main_sizer.Add(self.top_bar, 0, wx.EXPAND)
        
        # === CONTENT AREA ===
        self.content_panel = wx.Panel(self)
        self.content_panel.SetBackgroundColour(Colors.BG_PANEL)
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
        
        # === BOTTOM BAR: Save + Export PDF ===
        self.bottom_bar = self._create_bottom_bar()
        main_sizer.Add(self.bottom_bar, 0, wx.EXPAND)
        
        self.SetSizer(main_sizer)
        self._show_tab(0)
    
    def _create_top_bar(self):
        """Create top bar with tabs + Import button on same line."""
        top_bar = wx.Panel(self)
        top_bar.SetBackgroundColour(Colors.BG_TOOLBAR)
        top_bar.SetMinSize((-1, 50))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(10)
        
        # Tab buttons
        self.tab_buttons = []
        tabs = [
            (f"{Icons.NOTES} Notes", 0),
            (f"{Icons.TODO} Todo", 1),
            (f"{Icons.BOM} BOM", 2)
        ]
        
        for label, idx in tabs:
            btn = wx.Button(top_bar, label=label, size=(100, 40), style=wx.BORDER_NONE)
            btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            btn.Bind(wx.EVT_BUTTON, lambda e, i=idx: self._on_tab_click(i))
            btn.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            self.tab_buttons.append(btn)
            sizer.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        
        sizer.AddSpacer(20)
        
        # Import button
        import_btn = wx.Button(top_bar, label=f"{Icons.IMPORT} Import", size=(100, 40), style=wx.BORDER_NONE)
        import_btn.SetBackgroundColour(Colors.BG_BUTTON)
        import_btn.SetForegroundColour(Colors.TEXT_PRIMARY)
        import_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        import_btn.Bind(wx.EVT_BUTTON, self._on_import_click)
        sizer.Add(import_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        sizer.AddStretchSpacer()
        
        # Color settings button
        settings_btn = wx.Button(top_bar, label=f"{Icons.SETTINGS}", size=(40, 40), style=wx.BORDER_NONE)
        settings_btn.SetBackgroundColour(Colors.BG_BUTTON)
        settings_btn.SetForegroundColour(Colors.TEXT_PRIMARY)
        settings_btn.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        settings_btn.Bind(wx.EVT_BUTTON, self._on_settings_click)
        settings_btn.SetToolTip("Color Settings")
        sizer.Add(settings_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        top_bar.SetSizer(sizer)
        wx.CallAfter(self._update_tab_styles, 0)
        return top_bar
    
    def _create_bottom_bar(self):
        """Create bottom bar with Save and Export PDF buttons."""
        bottom_bar = wx.Panel(self)
        bottom_bar.SetBackgroundColour(Colors.BG_TOOLBAR)
        bottom_bar.SetMinSize((-1, 60))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddStretchSpacer()
        
        # Save button
        save_btn = wx.Button(bottom_bar, label=f"{Icons.SAVE}  Save", size=(120, 44), style=wx.BORDER_NONE)
        save_btn.SetBackgroundColour(Colors.ACCENT_GREEN)
        save_btn.SetForegroundColour(Colors.TEXT_WHITE)
        save_btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        save_btn.Bind(wx.EVT_BUTTON, lambda e: self._on_manual_save())
        sizer.Add(save_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        # Export PDF button
        pdf_btn = wx.Button(bottom_bar, label=f"{Icons.PDF}  Export PDF", size=(140, 44), style=wx.BORDER_NONE)
        pdf_btn.SetBackgroundColour(Colors.ACCENT_BLUE)
        pdf_btn.SetForegroundColour(Colors.TEXT_WHITE)
        pdf_btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        pdf_btn.Bind(wx.EVT_BUTTON, lambda e: self._on_export_pdf())
        sizer.Add(pdf_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
        
        bottom_bar.SetSizer(sizer)
        return bottom_bar
    
    def _update_tab_styles(self, active_idx):
        """Update tab button styles."""
        for i, btn in enumerate(self.tab_buttons):
            try:
                if i == active_idx:
                    btn.SetBackgroundColour(Colors.ACCENT_BLUE)
                    btn.SetForegroundColour(Colors.TEXT_WHITE)
                else:
                    btn.SetBackgroundColour(Colors.BG_BUTTON)
                    btn.SetForegroundColour(Colors.TEXT_PRIMARY)
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
    # SETTINGS DIALOG
    # ============================================================
    
    def _on_settings_click(self, event):
        """Show color settings dialog."""
        dlg = wx.Dialog(self, title="Editor Colors", size=(350, 280))
        dlg.SetBackgroundColour(Colors.BG_PANEL)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(20)
        
        # Background color
        bg_label = wx.StaticText(dlg, label="Background Color:")
        bg_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(bg_label, 0, wx.LEFT, 20)
        sizer.AddSpacer(8)
        
        bg_choices = list(BACKGROUND_COLORS.keys())
        self._bg_choice = wx.Choice(dlg, choices=bg_choices)
        self._bg_choice.SetSelection(bg_choices.index(self._bg_color_name) if self._bg_color_name in bg_choices else 0)
        sizer.Add(self._bg_choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)
        
        sizer.AddSpacer(20)
        
        # Text color
        txt_label = wx.StaticText(dlg, label="Text Color:")
        txt_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(txt_label, 0, wx.LEFT, 20)
        sizer.AddSpacer(8)
        
        txt_choices = list(TEXT_COLORS.keys())
        self._txt_choice = wx.Choice(dlg, choices=txt_choices)
        self._txt_choice.SetSelection(txt_choices.index(self._text_color_name) if self._text_color_name in txt_choices else 0)
        sizer.Add(self._txt_choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)
        
        sizer.AddStretchSpacer()
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddStretchSpacer()
        
        cancel_btn = wx.Button(dlg, wx.ID_CANCEL, "Cancel", size=(80, 36))
        btn_sizer.Add(cancel_btn, 0, wx.RIGHT, 10)
        
        apply_btn = wx.Button(dlg, wx.ID_OK, "Apply", size=(80, 36))
        apply_btn.SetBackgroundColour(Colors.ACCENT_BLUE)
        apply_btn.SetForegroundColour(Colors.TEXT_WHITE)
        btn_sizer.Add(apply_btn, 0, wx.RIGHT, 20)
        
        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.BOTTOM, 20)
        dlg.SetSizer(sizer)
        
        if dlg.ShowModal() == wx.ID_OK:
            self._bg_color_name = bg_choices[self._bg_choice.GetSelection()]
            self._text_color_name = txt_choices[self._txt_choice.GetSelection()]
            self._apply_editor_colors()
            self._save_color_settings()
        
        dlg.Destroy()
    
    def _apply_editor_colors(self):
        """Apply selected colors to editor."""
        bg = self._get_editor_bg()
        fg = self._get_editor_text()
        
        self.text_editor.SetBackgroundColour(bg)
        self.text_editor.SetForegroundColour(fg)
        
        # Apply to all text
        font = self.text_editor.GetFont()
        text_attr = wx.TextAttr(fg, bg, font)
        self.text_editor.SetDefaultStyle(text_attr)
        self.text_editor.SetStyle(0, self.text_editor.GetLastPosition(), text_attr)
        self.text_editor.Refresh()
    
    # ============================================================
    # TAB 1: NOTES
    # ============================================================
    
    def _create_notes_tab(self, parent):
        """Create Notes tab with editor."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(Colors.BG_PANEL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Text editor
        self.text_editor = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_RICH2 | wx.BORDER_SIMPLE
        )
        self.text_editor.SetBackgroundColour(self._get_editor_bg())
        self.text_editor.SetForegroundColour(self._get_editor_text())
        self.text_editor.SetFont(wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        # Set default text style
        font = self.text_editor.GetFont()
        text_attr = wx.TextAttr(self._get_editor_text(), self._get_editor_bg(), font)
        self.text_editor.SetDefaultStyle(text_attr)
        
        self.text_editor.Bind(wx.EVT_TEXT, self._on_text_changed)
        self.text_editor.Bind(wx.EVT_LEFT_DOWN, self._on_text_click)
        sizer.Add(self.text_editor, 1, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        return panel
    
    # ============================================================
    # TAB 2: TODO LIST
    # ============================================================
    
    def _create_todo_tab(self, parent):
        """Create Todo tab with checkboxes."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(Colors.BG_PANEL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar
        toolbar = wx.Panel(panel)
        toolbar.SetBackgroundColour(Colors.BG_TOOLBAR)
        toolbar.SetMinSize((-1, 50))
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tb_sizer.AddSpacer(10)
        
        # Add task button
        add_btn = wx.Button(toolbar, label=f"{Icons.ADD}  Add Task", size=(120, 40), style=wx.BORDER_NONE)
        add_btn.SetBackgroundColour(Colors.ACCENT_BLUE)
        add_btn.SetForegroundColour(Colors.TEXT_WHITE)
        add_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        add_btn.Bind(wx.EVT_BUTTON, self._on_add_todo)
        tb_sizer.Add(add_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        # Clear done button
        clear_btn = wx.Button(toolbar, label=f"{Icons.CLEAR}  Clear Done", size=(130, 40), style=wx.BORDER_NONE)
        clear_btn.SetBackgroundColour(Colors.BG_BUTTON)
        clear_btn.SetForegroundColour(Colors.TEXT_PRIMARY)
        clear_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        clear_btn.Bind(wx.EVT_BUTTON, self._on_clear_done)
        tb_sizer.Add(clear_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        tb_sizer.AddStretchSpacer()
        
        # Counter
        self.todo_count = wx.StaticText(toolbar, label="0 / 0")
        self.todo_count.SetForegroundColour(Colors.TEXT_SECONDARY)
        self.todo_count.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        tb_sizer.Add(self.todo_count, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
        
        toolbar.SetSizer(tb_sizer)
        sizer.Add(toolbar, 0, wx.EXPAND)
        
        # Todo list scroll area
        self.todo_scroll = scrolled.ScrolledPanel(panel)
        self.todo_scroll.SetBackgroundColour(Colors.BG_PANEL)
        self.todo_scroll.SetupScrolling(scroll_x=False)
        
        self.todo_sizer = wx.BoxSizer(wx.VERTICAL)
        self.todo_sizer.AddSpacer(10)
        self.todo_scroll.SetSizer(self.todo_sizer)
        sizer.Add(self.todo_scroll, 1, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        return panel
    
    def _add_todo_item(self, text="", done=False):
        """Add a todo item."""
        item_id = self._todo_id_counter
        self._todo_id_counter += 1
        
        item_panel = wx.Panel(self.todo_scroll)
        item_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        item_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Checkbox
        cb = wx.CheckBox(item_panel)
        cb.SetValue(done)
        cb.Bind(wx.EVT_CHECKBOX, lambda e, iid=item_id: self._on_todo_toggle(iid))
        item_sizer.Add(cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)
        
        # Text input
        txt = wx.TextCtrl(item_panel, value=text, style=wx.BORDER_NONE | wx.TE_PROCESS_ENTER)
        txt.SetBackgroundColour(wx.Colour(255, 255, 255))
        txt.SetForegroundColour(Colors.TEXT_SECONDARY if done else Colors.TEXT_PRIMARY)
        txt.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        txt.Bind(wx.EVT_TEXT, lambda e: self._save_todos())
        txt.Bind(wx.EVT_TEXT_ENTER, lambda e: self._on_add_todo(None))
        item_sizer.Add(txt, 1, wx.EXPAND | wx.ALL, 10)
        
        # Delete button
        del_btn = wx.Button(item_panel, label=Icons.DELETE, size=(36, 36), style=wx.BORDER_NONE)
        del_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
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
        
        self.todo_sizer.Add(item_panel, 0, wx.EXPAND | wx.BOTTOM, 6)
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
                    Colors.TEXT_SECONDARY if item['done'] else Colors.TEXT_PRIMARY
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
        """Create BOM Tool tab."""
        panel = scrolled.ScrolledPanel(parent)
        panel.SetBackgroundColour(Colors.BG_PANEL)
        panel.SetupScrolling(scroll_x=False)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(16)
        
        # Section helper
        def add_section(title, checkboxes):
            header = wx.StaticText(panel, label=title)
            header.SetForegroundColour(Colors.TEXT_SECONDARY)
            header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            sizer.Add(header, 0, wx.LEFT | wx.BOTTOM, 12)
            
            opt_panel = wx.Panel(panel)
            opt_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
            opt_sizer = wx.BoxSizer(wx.VERTICAL)
            
            widgets = []
            for label, default in checkboxes:
                cb = wx.CheckBox(opt_panel, label=f"  {label}")
                cb.SetValue(default)
                cb.SetForegroundColour(Colors.TEXT_PRIMARY)
                cb.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
                opt_sizer.Add(cb, 0, wx.ALL, 10)
                widgets.append(cb)
            
            opt_panel.SetSizer(opt_sizer)
            sizer.Add(opt_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
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
        
        # Grouping
        grp_header = wx.StaticText(panel, label="GROUPING")
        grp_header.SetForegroundColour(Colors.TEXT_SECONDARY)
        grp_header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(grp_header, 0, wx.LEFT | wx.BOTTOM, 12)
        
        self.bom_group_by = wx.Choice(panel, choices=[
            "Value + Footprint",
            "Value only",
            "Footprint only",
            "No grouping"
        ])
        self.bom_group_by.SetSelection(0)
        sizer.Add(self.bom_group_by, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        
        # Sort
        sort_header = wx.StaticText(panel, label="SORT BY")
        sort_header.SetForegroundColour(Colors.TEXT_SECONDARY)
        sort_header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(sort_header, 0, wx.LEFT | wx.BOTTOM, 12)
        
        self.bom_sort_by = wx.Choice(panel, choices=[
            "Reference (natural)",
            "Value",
            "Footprint",
            "Quantity"
        ])
        self.bom_sort_by.SetSelection(0)
        sizer.Add(self.bom_sort_by, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        
        # Blacklist
        bl_header = wx.StaticText(panel, label="CUSTOM BLACKLIST (one per line)")
        bl_header.SetForegroundColour(Colors.TEXT_SECONDARY)
        bl_header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(bl_header, 0, wx.LEFT | wx.BOTTOM, 12)
        
        self.bom_blacklist = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 70))
        self.bom_blacklist.SetHint("e.g. LOGO*, H*")
        sizer.Add(self.bom_blacklist, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        
        # Generate button
        gen_btn = wx.Button(panel, label=f"{Icons.GENERATE}  Generate BOM → Notes", size=(-1, 50), style=wx.BORDER_NONE)
        gen_btn.SetBackgroundColour(Colors.ACCENT_BLUE)
        gen_btn.SetForegroundColour(Colors.TEXT_WHITE)
        gen_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        gen_btn.Bind(wx.EVT_BUTTON, self._on_generate_bom)
        sizer.Add(gen_btn, 0, wx.EXPAND | wx.ALL, 16)
        
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
                self._apply_editor_colors()
                self._show_tab(0)
        except Exception as e:
            pass
    
    def _generate_bom_text(self):
        """Generate BOM text."""
        try:
            import pcbnew
            import fnmatch
        except ImportError:
            return "## BOM\n\n*pcbnew not available*\n"
        
        try:
            board = pcbnew.GetBoard()
            if not board:
                return "## BOM\n\n*No board loaded*\n"
        except:
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
        except:
            return "## BOM\n\n*Error reading components*\n"
        
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
        """Show import menu."""
        menu = wx.Menu()
        
        items = [
            ("📋 Project Title", "title"),
            ("📅 Project Date", "date"),
            ("📐 Board Info", "board_size"),
            ("📚 Stackup", "stackup"),
            ("🔗 Netlist", "netlist"),
            ("📑 Layers", "layers"),
            ("🔘 Drill Table", "drill_table"),
            ("⚙ Design Rules", "design_rules"),
            ("↔ Diff Pairs", "diff_pairs"),
        ]
        
        for label, meta_type in items:
            mi = menu.Append(wx.ID_ANY, label)
            self.Bind(wx.EVT_MENU, lambda e, t=meta_type: self._import_metadata(t), mi)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def _import_metadata(self, meta_type):
        """Import metadata."""
        try:
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
                self._apply_editor_colors()
        except:
            pass
    
    def _extract_title(self):
        """Extract project title."""
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
        except:
            return "# Project Title\n"
    
    def _extract_date(self):
        """Extract project date."""
        try:
            import pcbnew
            board = pcbnew.GetBoard()
            if board:
                title_block = board.GetTitleBlock()
                date = title_block.GetDate() if title_block else ""
                if date:
                    return f"**Date:** {date}"
        except:
            pass
        
        return f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d')}"
    
    def _on_export_pdf(self):
        """Export notes to PDF."""
        try:
            content = self.text_editor.GetValue()
            filepath = self.pdf_exporter.export(content)
            if filepath:
                wx.MessageBox(f"Exported to:\n{filepath}", "PDF Export", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Export failed: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_manual_save(self):
        """Manual save."""
        try:
            self._save_notes()
            self._save_todos()
            wx.MessageBox("Notes saved successfully!", "Saved", wx.OK | wx.ICON_INFORMATION)
        except:
            pass
    
    def _on_text_changed(self, event):
        self._modified = True
        event.Skip()
    
    def _on_text_click(self, event):
        """Handle @REF clicks."""
        try:
            pos = self.text_editor.HitTestPos(event.GetPosition())[1]
            if pos >= 0:
                text = self.text_editor.GetValue()
                word = self._get_word_at_pos(text, pos)
                if word.startswith('@'):
                    self._highlight_component(word[1:])
                    return
        except:
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
        """Highlight component in PCB."""
        try:
            if self.designator_linker.highlight(ref):
                pass
        except:
            pass
    
    # ============================================================
    # DATA MANAGEMENT
    # ============================================================
    
    def _start_auto_save_timer(self):
        """Start auto-save timer."""
        try:
            self._auto_save_timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self._on_auto_save, self._auto_save_timer)
            self._auto_save_timer.Start(5000)
        except:
            pass
    
    def _on_auto_save(self, event):
        """Auto-save if modified."""
        if self._modified:
            try:
                self._save_notes()
                self._save_todos()
                self._modified = False
            except:
                pass
    
    def _load_all_data(self):
        """Load saved data."""
        try:
            content = self.notes_manager.load()
            if content:
                self.text_editor.SetValue(content)
                self._apply_editor_colors()
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
        """Save notes."""
        try:
            self.notes_manager.save(self.text_editor.GetValue())
        except:
            pass
    
    def _save_todos(self):
        """Save todos."""
        try:
            todos = [{'text': item['text'].GetValue(), 'done': item['checkbox'].GetValue()} 
                     for item in self._todo_items]
            self.notes_manager.save_todos(todos)
        except:
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
        except:
            pass
