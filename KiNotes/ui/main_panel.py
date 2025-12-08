"""
KiNotes Main Panel - Modern UI with Dark Theme Toggle
Tab 1: Notes | Tab 2: Todo List | Tab 3: BOM Tool
User-selectable background and text colors with dark mode
"""
import wx
import wx.lib.scrolledpanel as scrolled
import os
import datetime
import json


# ============================================================
# COLOR PRESETS - Light Mode
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

# Dark Mode Colors
DARK_THEME = {
    "bg_panel": "#1E1E1E",
    "bg_toolbar": "#2D2D2D",
    "bg_button": "#3C3C3C",
    "bg_button_hover": "#4A4A4A",
    "bg_editor": "#252526",
    "text_primary": "#E0E0E0",
    "text_secondary": "#A0A0A0",
    "border": "#404040",
    "accent_blue": "#0078D4",
    "accent_green": "#4CAF50",
    "accent_red": "#F44336",
}

LIGHT_THEME = {
    "bg_panel": "#F5F5F5",
    "bg_toolbar": "#EBEBEB",
    "bg_button": "#E1E1E1",
    "bg_button_hover": "#D2D2D2",
    "bg_editor": "#FFFDF5",
    "text_primary": "#202124",
    "text_secondary": "#5F6368",
    "border": "#DADCE0",
    "accent_blue": "#4285F4",
    "accent_green": "#34A853",
    "accent_red": "#EA4335",
}


def hex_to_colour(hex_str):
    """Convert hex color to wx.Colour."""
    hex_str = hex_str.lstrip("#")
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return wx.Colour(r, g, b)


# ============================================================
# ROUNDED BUTTON CLASS - Modern Unified Buttons
# ============================================================
class RoundedButton(wx.Panel):
    """Custom rounded button with hover effects."""
    
    def __init__(self, parent, label="", size=(120, 44), bg_color="#4285F4", 
                 fg_color="#FFFFFF", icon="", corner_radius=8, font_size=11,
                 font_weight=wx.FONTWEIGHT_BOLD):
        super().__init__(parent, size=size)
        
        self.label = label
        self.icon = icon
        self.bg_color = hex_to_colour(bg_color) if isinstance(bg_color, str) else bg_color
        self.fg_color = hex_to_colour(fg_color) if isinstance(fg_color, str) else fg_color
        self.hover_color = self._darken_color(self.bg_color, 20)
        self.corner_radius = corner_radius
        self.is_hovered = False
        self.callback = None
        
        self.SetMinSize(size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        
        self.font = wx.Font(font_size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, font_weight)
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_ENTER_WINDOW, self._on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_leave)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_click)
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
    
    def _darken_color(self, color, amount):
        """Darken a color by amount."""
        r = max(0, color.Red() - amount)
        g = max(0, color.Green() - amount)
        b = max(0, color.Blue() - amount)
        return wx.Colour(r, g, b)
    
    def _on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        w, h = self.GetSize()
        
        # Draw rounded rectangle background
        bg = self.hover_color if self.is_hovered else self.bg_color
        gc.SetBrush(wx.Brush(bg))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, w, h, self.corner_radius)
        
        # Draw text
        gc.SetFont(self.font, self.fg_color)
        display_text = self.icon + "  " + self.label if self.icon else self.label
        text_w, text_h = gc.GetTextExtent(display_text)[:2]
        x = (w - text_w) / 2
        y = (h - text_h) / 2
        gc.DrawText(display_text, x, y)
    
    def _on_enter(self, event):
        self.is_hovered = True
        self.Refresh()
    
    def _on_leave(self, event):
        self.is_hovered = False
        self.Refresh()
    
    def _on_click(self, event):
        if self.callback:
            self.callback(event)
    
    def Bind_Click(self, callback):
        """Bind click callback."""
        self.callback = callback
    
    def SetColors(self, bg_color, fg_color):
        """Update button colors."""
        self.bg_color = hex_to_colour(bg_color) if isinstance(bg_color, str) else bg_color
        self.fg_color = hex_to_colour(fg_color) if isinstance(fg_color, str) else fg_color
        self.hover_color = self._darken_color(self.bg_color, 20)
        self.Refresh()


# ============================================================
# TOGGLE SWITCH - Dark Mode Toggle
# ============================================================
class ToggleSwitch(wx.Panel):
    """iOS-style toggle switch."""
    
    def __init__(self, parent, size=(50, 26), is_on=False, label_on="", label_off=""):
        super().__init__(parent, size=size)
        
        self.is_on = is_on
        self.label_on = label_on
        self.label_off = label_off
        self.callback = None
        
        self.track_color_on = hex_to_colour("#4285F4")
        self.track_color_off = hex_to_colour("#CCCCCC")
        self.knob_color = wx.WHITE
        
        self.SetMinSize(size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_click)
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
    
    def _on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        w, h = self.GetSize()
        track_h = h - 4
        track_y = 2
        knob_size = track_h - 4
        
        # Draw track
        track_color = self.track_color_on if self.is_on else self.track_color_off
        gc.SetBrush(wx.Brush(track_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, track_y, w, track_h, track_h / 2)
        
        # Draw knob
        knob_x = w - knob_size - 4 if self.is_on else 4
        knob_y = track_y + 2
        gc.SetBrush(wx.Brush(self.knob_color))
        gc.DrawEllipse(knob_x, knob_y, knob_size, knob_size)
    
    def _on_click(self, event):
        self.is_on = not self.is_on
        self.Refresh()
        if self.callback:
            self.callback(self.is_on)
    
    def SetValue(self, value):
        self.is_on = value
        self.Refresh()
    
    def GetValue(self):
        return self.is_on
    
    def Bind_Change(self, callback):
        self.callback = callback


# ============================================================
# ICONS - Beautiful Unicode icons
# ============================================================
class Icons:
    # Tab icons
    NOTES = "\U0001F4DD"      # Memo/Note
    TODO = "\u2611"           # Checkbox with check
    BOM = "\U0001F4CB"        # Clipboard
    
    # Action icons  
    IMPORT = "\u21E9"         # Downwards arrow
    SAVE = "\U0001F4BE"       # Floppy disk
    PDF = "\U0001F4C4"        # Document
    ADD = "\u2795"            # Plus
    DELETE = "\u2716"         # X mark
    CLEAR = "\U0001F5D1"      # Wastebasket
    SETTINGS = "\u2699"       # Gear
    GENERATE = "\u27A4"       # Arrow
    
    # Theme icons
    DARK = "\U0001F319"       # Crescent moon
    LIGHT = "\u2600"          # Sun
    
    # Import menu icons
    BOARD = "\U0001F4D0"      # Board/Triangular ruler
    LAYERS = "\U0001F5C2"     # Layers/Card index
    NETLIST = "\U0001F517"    # Link
    RULES = "\U0001F4CF"      # Ruler
    DRILL = "\U0001F529"      # Nut and bolt
    ALL = "\U0001F4E6"        # Package


# ============================================================
# MAIN PANEL
# ============================================================
class KiNotesMainPanel(wx.Panel):
    """Main panel with tabs, color picker, dark mode toggle, and bottom action buttons."""
    
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
        
        # Theme settings
        self._dark_mode = False
        self._bg_color_name = "Ivory Paper"
        self._text_color_name = "Carbon Black"
        self._load_color_settings()
        
        self._theme = DARK_THEME if self._dark_mode else LIGHT_THEME
        self.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        
        try:
            self._init_ui()
            self._load_all_data()
            self._start_auto_save_timer()
        except Exception as e:
            print("KiNotes UI init error: " + str(e))
    
    def _load_color_settings(self):
        """Load saved color settings."""
        try:
            settings = self.notes_manager.load_settings()
            if settings:
                self._bg_color_name = settings.get("bg_color", "Ivory Paper")
                self._text_color_name = settings.get("text_color", "Carbon Black")
                self._dark_mode = settings.get("dark_mode", False)
        except:
            pass
    
    def _save_color_settings(self):
        """Save color settings."""
        try:
            settings = self.notes_manager.load_settings() or {}
            settings.update({
                "bg_color": self._bg_color_name,
                "text_color": self._text_color_name,
                "dark_mode": self._dark_mode
            })
            self.notes_manager.save_settings(settings)
        except:
            pass
    
    def _get_editor_bg(self):
        if self._dark_mode:
            return hex_to_colour(DARK_THEME["bg_editor"])
        return hex_to_colour(BACKGROUND_COLORS.get(self._bg_color_name, "#FFFDF5"))
    
    def _get_editor_text(self):
        if self._dark_mode:
            return hex_to_colour(DARK_THEME["text_primary"])
        return hex_to_colour(TEXT_COLORS.get(self._text_color_name, "#2B2B2B"))
    
    def _init_ui(self):
        """Initialize UI with new layout."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # === TOP BAR: Tabs + Import + Settings ===
        self.top_bar = self._create_top_bar()
        main_sizer.Add(self.top_bar, 0, wx.EXPAND)
        
        # === CONTENT AREA ===
        self.content_panel = wx.Panel(self)
        self.content_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
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
        
        # === BOTTOM BAR: pcbtools.xyz + Save + Export PDF ===
        self.bottom_bar = self._create_bottom_bar()
        main_sizer.Add(self.bottom_bar, 0, wx.EXPAND)
        
        self.SetSizer(main_sizer)
        self._show_tab(0)
    
    def _create_top_bar(self):
        """Create top bar with tabs + Import button on same line."""
        top_bar = wx.Panel(self)
        top_bar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        top_bar.SetMinSize((-1, 60))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(16)
        
        # Tab buttons - unified rounded style
        self.tab_buttons = []
        tabs = [
            (Icons.NOTES, "Notes", 0),
            (Icons.TODO, "Todo", 1),
            (Icons.BOM, "BOM", 2)
        ]
        
        for icon, label, idx in tabs:
            btn = RoundedButton(
                top_bar, 
                label=label,
                icon=icon,
                size=(110, 42),
                bg_color=self._theme["bg_button"],
                fg_color=self._theme["text_primary"],
                corner_radius=10,
                font_size=11,
                font_weight=wx.FONTWEIGHT_BOLD
            )
            btn.Bind_Click(lambda e, i=idx: self._on_tab_click(i))
            btn.tab_index = idx
            self.tab_buttons.append(btn)
            sizer.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        
        sizer.AddSpacer(16)
        
        # Import button - unified style
        self.import_btn = RoundedButton(
            top_bar,
            label="Import",
            icon=Icons.IMPORT,
            size=(130, 42),
            bg_color=self._theme["bg_button"],
            fg_color=self._theme["text_primary"],
            corner_radius=10,
            font_size=11,
            font_weight=wx.FONTWEIGHT_NORMAL
        )
        self.import_btn.Bind_Click(self._on_import_click)
        sizer.Add(self.import_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        sizer.AddStretchSpacer()
        
        # Settings button - with gear icon
        self.settings_btn = RoundedButton(
            top_bar,
            label="",
            icon=Icons.SETTINGS,
            size=(50, 42),
            bg_color=self._theme["bg_button"],
            fg_color=self._theme["text_primary"],
            corner_radius=10,
            font_size=14,
            font_weight=wx.FONTWEIGHT_NORMAL
        )
        self.settings_btn.Bind_Click(self._on_settings_click)
        sizer.Add(self.settings_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
        
        top_bar.SetSizer(sizer)
        wx.CallAfter(self._update_tab_styles, 0)
        return top_bar
    
    def _create_bottom_bar(self):
        """Create bottom bar with pcbtools.xyz link, Save and Export PDF buttons."""
        bottom_bar = wx.Panel(self)
        bottom_bar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        bottom_bar.SetMinSize((-1, 70))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(16)
        
        # pcbtools.xyz link on the left
        link_text = wx.StaticText(bottom_bar, label="pcbtools.xyz")
        link_text.SetForegroundColour(hex_to_colour(self._theme["accent_blue"]))
        link_text.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, underline=True))
        link_text.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        link_text.Bind(wx.EVT_LEFT_DOWN, self._on_website_click)
        link_text.SetToolTip("Visit pcbtools.xyz")
        sizer.Add(link_text, 0, wx.ALIGN_CENTER_VERTICAL)
        
        sizer.AddStretchSpacer()
        
        # Save button - unified rounded style
        self.save_btn = RoundedButton(
            bottom_bar,
            label="Save",
            icon=Icons.SAVE,
            size=(130, 48),
            bg_color=self._theme["accent_green"],
            fg_color="#FFFFFF",
            corner_radius=10,
            font_size=12,
            font_weight=wx.FONTWEIGHT_BOLD
        )
        self.save_btn.Bind_Click(lambda e: self._on_manual_save())
        sizer.Add(self.save_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        # Export PDF button - unified rounded style with more space
        self.pdf_btn = RoundedButton(
            bottom_bar,
            label="Export PDF",
            icon=Icons.PDF,
            size=(160, 48),
            bg_color=self._theme["accent_blue"],
            fg_color="#FFFFFF",
            corner_radius=10,
            font_size=12,
            font_weight=wx.FONTWEIGHT_BOLD
        )
        self.pdf_btn.Bind_Click(lambda e: self._on_export_pdf())
        sizer.Add(self.pdf_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
        
        bottom_bar.SetSizer(sizer)
        return bottom_bar
    
    def _on_website_click(self, event):
        """Open pcbtools.xyz in browser."""
        try:
            import webbrowser
            webbrowser.open("https://pcbtools.xyz")
        except:
            pass
    
    def _update_tab_styles(self, active_idx):
        """Update tab button styles."""
        for btn in self.tab_buttons:
            try:
                if btn.tab_index == active_idx:
                    btn.SetColors(self._theme["accent_blue"], "#FFFFFF")
                else:
                    btn.SetColors(self._theme["bg_button"], self._theme["text_primary"])
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
        
        # Show/hide Import button - only visible on Notes tab
        if idx == 0:
            self.notes_panel.Show()
            self.import_btn.Show()
        elif idx == 1:
            self.todo_panel.Show()
            self.import_btn.Hide()
            try:
                self.todo_scroll.FitInside()
            except:
                pass
        elif idx == 2:
            self.bom_panel.Show()
            self.import_btn.Hide()
            try:
                self.bom_panel.FitInside()
            except:
                pass
        
        self.top_bar.Layout()
        self.content_panel.Layout()
        self.Layout()
        self.Refresh()
    
    # ============================================================
    # SETTINGS DIALOG - With Dark Mode Toggle
    # ============================================================
    
    def _on_settings_click(self, event):
        """Show color settings dialog with dark mode toggle."""
        dlg = wx.Dialog(self, title="Editor Colors", size=(420, 480),
                       style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        dlg.SetMinSize((380, 450))
        dlg.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(24)
        
        # Dark Mode Toggle Section
        mode_panel = wx.Panel(dlg)
        mode_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        mode_label = wx.StaticText(mode_panel, label=Icons.DARK + "  Dark Theme")
        mode_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        mode_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        mode_sizer.Add(mode_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        mode_sizer.AddStretchSpacer()
        
        self._dark_toggle = ToggleSwitch(mode_panel, size=(54, 28), is_on=self._dark_mode)
        mode_sizer.Add(self._dark_toggle, 0, wx.ALIGN_CENTER_VERTICAL)
        
        mode_panel.SetSizer(mode_sizer)
        sizer.Add(mode_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)
        
        sizer.AddSpacer(24)
        
        # Separator
        sep = wx.StaticLine(dlg)
        sizer.Add(sep, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)
        
        sizer.AddSpacer(20)
        
        # Light Mode Colors Section Header
        light_header = wx.StaticText(dlg, label="Light Theme Colors")
        light_header.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        light_header.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        sizer.Add(light_header, 0, wx.LEFT, 24)
        sizer.AddSpacer(12)
        
        # Background color
        bg_label = wx.StaticText(dlg, label="Background:")
        bg_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        bg_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        sizer.Add(bg_label, 0, wx.LEFT, 24)
        sizer.AddSpacer(6)
        
        bg_choices = list(BACKGROUND_COLORS.keys())
        self._bg_choice = wx.Choice(dlg, choices=bg_choices)
        self._bg_choice.SetSelection(bg_choices.index(self._bg_color_name) if self._bg_color_name in bg_choices else 0)
        sizer.Add(self._bg_choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)
        
        sizer.AddSpacer(16)
        
        # Text color
        txt_label = wx.StaticText(dlg, label="Text:")
        txt_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        txt_label.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        sizer.Add(txt_label, 0, wx.LEFT, 24)
        sizer.AddSpacer(6)
        
        txt_choices = list(TEXT_COLORS.keys())
        self._txt_choice = wx.Choice(dlg, choices=txt_choices)
        self._txt_choice.SetSelection(txt_choices.index(self._text_color_name) if self._text_color_name in txt_choices else 0)
        sizer.Add(self._txt_choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 24)
        
        sizer.AddStretchSpacer()
        
        # Buttons - unified rounded style with clear Save action
        btn_panel = wx.Panel(dlg)
        btn_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddStretchSpacer()
        
        cancel_btn = wx.Button(dlg, wx.ID_CANCEL, "Cancel", size=(100, 40))
        btn_sizer.Add(cancel_btn, 0, wx.RIGHT, 12)
        
        apply_btn = wx.Button(dlg, wx.ID_OK, "Save & Apply", size=(120, 40))
        apply_btn.SetBackgroundColour(hex_to_colour(self._theme["accent_blue"]))
        apply_btn.SetForegroundColour(wx.WHITE)
        apply_btn.SetToolTip("Save settings and apply theme")
        btn_sizer.Add(apply_btn, 0)
        
        btn_panel.SetSizer(btn_sizer)
        sizer.Add(btn_panel, 0, wx.EXPAND | wx.ALL, 24)
        
        dlg.SetSizer(sizer)
        
        if dlg.ShowModal() == wx.ID_OK:
            self._bg_color_name = bg_choices[self._bg_choice.GetSelection()]
            self._text_color_name = txt_choices[self._txt_choice.GetSelection()]
            self._dark_mode = self._dark_toggle.GetValue()
            self._theme = DARK_THEME if self._dark_mode else LIGHT_THEME
            self._apply_theme()
            self._apply_editor_colors()
            self._save_color_settings()
        
        dlg.Destroy()
    
    def _apply_theme(self):
        """Apply current theme to all UI elements."""
        self.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        self.top_bar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        self.bottom_bar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        self.content_panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        
        # Update tab buttons
        for btn in self.tab_buttons:
            if btn.tab_index == self._current_tab:
                btn.SetColors(self._theme["accent_blue"], "#FFFFFF")
            else:
                btn.SetColors(self._theme["bg_button"], self._theme["text_primary"])
        
        # Update other buttons
        self.import_btn.SetColors(self._theme["bg_button"], self._theme["text_primary"])
        self.settings_btn.SetColors(self._theme["bg_button"], self._theme["text_primary"])
        self.save_btn.SetColors(self._theme["accent_green"], "#FFFFFF")
        self.pdf_btn.SetColors(self._theme["accent_blue"], "#FFFFFF")
        
        self.Refresh()
        self.Update()
    
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
        panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
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
        sizer.Add(self.text_editor, 1, wx.EXPAND | wx.ALL, 12)
        
        panel.SetSizer(sizer)
        return panel
    
    # ============================================================
    # TAB 2: TODO LIST
    # ============================================================
    
    def _create_todo_tab(self, parent):
        """Create Todo tab with checkboxes."""
        panel = wx.Panel(parent)
        panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar
        toolbar = wx.Panel(panel)
        toolbar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        toolbar.SetMinSize((-1, 60))
        tb_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tb_sizer.AddSpacer(16)
        
        # Add task button - unified rounded style
        self.add_todo_btn = RoundedButton(
            toolbar,
            label="Add Task",
            icon=Icons.ADD,
            size=(130, 42),
            bg_color=self._theme["accent_blue"],
            fg_color="#FFFFFF",
            corner_radius=10,
            font_size=11,
            font_weight=wx.FONTWEIGHT_BOLD
        )
        self.add_todo_btn.Bind_Click(self._on_add_todo)
        tb_sizer.Add(self.add_todo_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        
        # Clear done button - unified rounded style
        self.clear_done_btn = RoundedButton(
            toolbar,
            label="Clear Done",
            icon=Icons.CLEAR,
            size=(140, 42),
            bg_color=self._theme["bg_button"],
            fg_color=self._theme["text_primary"],
            corner_radius=10,
            font_size=11,
            font_weight=wx.FONTWEIGHT_NORMAL
        )
        self.clear_done_btn.Bind_Click(self._on_clear_done)
        tb_sizer.Add(self.clear_done_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        
        tb_sizer.AddStretchSpacer()
        
        # Counter
        self.todo_count = wx.StaticText(toolbar, label="0 / 0")
        self.todo_count.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        self.todo_count.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        tb_sizer.Add(self.todo_count, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 20)
        
        toolbar.SetSizer(tb_sizer)
        sizer.Add(toolbar, 0, wx.EXPAND)
        
        # Todo list scroll area
        self.todo_scroll = scrolled.ScrolledPanel(panel)
        self.todo_scroll.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        self.todo_scroll.SetupScrolling(scroll_x=False)
        
        self.todo_sizer = wx.BoxSizer(wx.VERTICAL)
        self.todo_sizer.AddSpacer(12)
        self.todo_scroll.SetSizer(self.todo_sizer)
        sizer.Add(self.todo_scroll, 1, wx.EXPAND | wx.ALL, 12)
        
        panel.SetSizer(sizer)
        return panel
    
    def _add_todo_item(self, text="", done=False):
        """Add a todo item."""
        item_id = self._todo_id_counter
        self._todo_id_counter += 1
        
        item_panel = wx.Panel(self.todo_scroll)
        item_panel.SetBackgroundColour(wx.WHITE if not self._dark_mode else hex_to_colour("#2D2D2D"))
        item_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Checkbox
        cb = wx.CheckBox(item_panel)
        cb.SetValue(done)
        cb.Bind(wx.EVT_CHECKBOX, lambda e, iid=item_id: self._on_todo_toggle(iid))
        item_sizer.Add(cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 14)
        
        # Text input
        txt = wx.TextCtrl(item_panel, value=text, style=wx.BORDER_NONE | wx.TE_PROCESS_ENTER)
        txt.SetBackgroundColour(wx.WHITE if not self._dark_mode else hex_to_colour("#2D2D2D"))
        txt.SetForegroundColour(hex_to_colour(self._theme["text_secondary"] if done else self._theme["text_primary"]))
        txt.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        txt.Bind(wx.EVT_TEXT, lambda e: self._save_todos())
        txt.Bind(wx.EVT_TEXT_ENTER, lambda e: self._on_add_todo(None))
        item_sizer.Add(txt, 1, wx.EXPAND | wx.ALL, 12)
        
        # Delete button with icon
        del_btn = wx.Button(item_panel, label=Icons.DELETE, size=(40, 40), style=wx.BORDER_NONE)
        del_btn.SetBackgroundColour(wx.WHITE if not self._dark_mode else hex_to_colour("#2D2D2D"))
        del_btn.SetForegroundColour(hex_to_colour(self._theme["accent_red"]))
        del_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        del_btn.Bind(wx.EVT_BUTTON, lambda e, iid=item_id: self._on_delete_todo(iid))
        item_sizer.Add(del_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        item_panel.SetSizer(item_sizer)
        
        self._todo_items.append({
            "id": item_id,
            "panel": item_panel,
            "checkbox": cb,
            "text": txt,
            "done": done
        })
        
        self.todo_sizer.Add(item_panel, 0, wx.EXPAND | wx.BOTTOM, 8)
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
            if item["id"] == item_id:
                item["done"] = item["checkbox"].GetValue()
                item["text"].SetForegroundColour(
                    hex_to_colour(self._theme["text_secondary"] if item["done"] else self._theme["text_primary"])
                )
                item["text"].Refresh()
                break
        self._update_todo_count()
        self._save_todos()
    
    def _on_delete_todo(self, item_id):
        for i, item in enumerate(self._todo_items):
            if item["id"] == item_id:
                item["panel"].Destroy()
                self._todo_items.pop(i)
                break
        self.todo_scroll.FitInside()
        self._update_todo_count()
        self._save_todos()
    
    def _on_clear_done(self, event):
        to_remove = [item for item in self._todo_items if item["done"]]
        for item in to_remove:
            item["panel"].Destroy()
            self._todo_items.remove(item)
        self.todo_scroll.FitInside()
        self._update_todo_count()
        self._save_todos()
    
    def _update_todo_count(self):
        total = len(self._todo_items)
        done = sum(1 for item in self._todo_items if item["done"])
        self.todo_count.SetLabel(str(done) + " / " + str(total))
    
    # ============================================================
    # TAB 3: BOM TOOL
    # ============================================================
    
    def _create_bom_tab(self, parent):
        """Create BOM Tool tab."""
        panel = scrolled.ScrolledPanel(parent)
        panel.SetBackgroundColour(hex_to_colour(self._theme["bg_panel"]))
        panel.SetupScrolling(scroll_x=False)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(20)
        
        # Section helper
        def add_section(title, checkboxes):
            header = wx.StaticText(panel, label=title)
            header.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
            header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            sizer.Add(header, 0, wx.LEFT | wx.BOTTOM, 16)
            
            opt_panel = wx.Panel(panel)
            opt_panel.SetBackgroundColour(wx.WHITE if not self._dark_mode else hex_to_colour("#2D2D2D"))
            opt_sizer = wx.BoxSizer(wx.VERTICAL)
            
            widgets = []
            for label, default in checkboxes:
                cb = wx.CheckBox(opt_panel, label="  " + label)
                cb.SetValue(default)
                cb.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
                cb.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
                opt_sizer.Add(cb, 0, wx.ALL, 12)
                widgets.append(cb)
            
            opt_panel.SetSizer(opt_sizer)
            sizer.Add(opt_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)
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
        grp_header.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        grp_header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(grp_header, 0, wx.LEFT | wx.BOTTOM, 16)
        
        self.bom_group_by = wx.Choice(panel, choices=[
            "Value + Footprint",
            "Value only",
            "Footprint only",
            "No grouping"
        ])
        self.bom_group_by.SetSelection(0)
        sizer.Add(self.bom_group_by, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)
        
        # Sort
        sort_header = wx.StaticText(panel, label="SORT BY")
        sort_header.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        sort_header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(sort_header, 0, wx.LEFT | wx.BOTTOM, 16)
        
        self.bom_sort_by = wx.Choice(panel, choices=[
            "Reference (natural)",
            "Value",
            "Footprint",
            "Quantity"
        ])
        self.bom_sort_by.SetSelection(0)
        sizer.Add(self.bom_sort_by, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)
        
        # Blacklist
        bl_header = wx.StaticText(panel, label="CUSTOM BLACKLIST (one per line)")
        bl_header.SetForegroundColour(hex_to_colour(self._theme["text_secondary"]))
        bl_header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(bl_header, 0, wx.LEFT | wx.BOTTOM, 16)
        
        self.bom_blacklist = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 80))
        self.bom_blacklist.SetHint("e.g. LOGO*, H*")
        sizer.Add(self.bom_blacklist, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)
        
        # Generate button - unified rounded style
        self.gen_bom_btn = RoundedButton(
            panel,
            label="Generate BOM -> Notes",
            icon=Icons.GENERATE,
            size=(-1, 52),
            bg_color=self._theme["accent_blue"],
            fg_color="#FFFFFF",
            corner_radius=10,
            font_size=12,
            font_weight=wx.FONTWEIGHT_BOLD
        )
        self.gen_bom_btn.Bind_Click(self._on_generate_bom)
        sizer.Add(self.gen_bom_btn, 0, wx.EXPAND | wx.ALL, 20)
        
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
                        if hasattr(pcbnew, "FP_EXCLUDE_FROM_BOM") and (attrs & pcbnew.FP_EXCLUDE_FROM_BOM):
                            continue
                    except:
                        pass
                
                if self.bom_exclude_virtual.GetValue():
                    try:
                        attrs = fp.GetAttributes()
                        if hasattr(pcbnew, "FP_BOARD_ONLY") and (attrs & pcbnew.FP_BOARD_ONLY):
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
                
                components.append({"ref": ref, "value": value, "footprint": footprint})
        except:
            return "## BOM\n\n*Error reading components*\n"
        
        if not components:
            return "## BOM\n\n*No components found*\n"
        
        # Group
        group_mode = self.bom_group_by.GetSelection()
        grouped = {}
        
        for comp in components:
            if group_mode == 0:
                key = (comp["value"], comp["footprint"])
            elif group_mode == 1:
                key = (comp["value"], "")
            elif group_mode == 2:
                key = ("", comp["footprint"])
            else:
                key = (comp["ref"], comp["value"], comp["footprint"])
            
            if key not in grouped:
                grouped[key] = {"refs": [], "value": comp["value"], "footprint": comp["footprint"]}
            grouped[key]["refs"].append(comp["ref"])
        
        # Sort refs naturally
        import re
        def natural_key(s):
            return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", s)]
        
        for data in grouped.values():
            data["refs"].sort(key=natural_key)
        
        # Sort groups
        sort_mode = self.bom_sort_by.GetSelection()
        items = list(grouped.values())
        
        if sort_mode == 0:
            items.sort(key=lambda x: natural_key(x["refs"][0]))
        elif sort_mode == 1:
            items.sort(key=lambda x: x["value"].lower())
        elif sort_mode == 2:
            items.sort(key=lambda x: x["footprint"].lower())
        elif sort_mode == 3:
            items.sort(key=lambda x: -len(x["refs"]))
        
        # Build output
        lines = ["## BOM - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), ""]
        
        # Header
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
        lines.append("|" + "|".join(["---"] * len(header_parts)) + "|")
        
        for item in items:
            row = []
            if self.bom_show_qty.GetValue():
                row.append(str(len(item["refs"])))
            if self.bom_show_value.GetValue():
                row.append(item["value"])
            if self.bom_show_fp.GetValue():
                row.append(item["footprint"])
            if self.bom_show_refs.GetValue():
                refs_str = ", ".join(["@" + r for r in item["refs"][:5]])
                if len(item["refs"]) > 5:
                    refs_str += " +" + str(len(item["refs"])-5) + " more"
                row.append(refs_str)
            lines.append("| " + " | ".join(row) + " |")
        
        lines.append("")
        lines.append("**Total unique groups:** " + str(len(items)))
        lines.append("**Total components:** " + str(sum(len(i["refs"]) for i in items)))
        
        return "\n".join(lines)
    
    # ============================================================
    # IMPORT HANDLER
    # ============================================================
    
    def _on_import_click(self, event):
        """Handle import button click."""
        menu = wx.Menu()
        
        items = [
            (Icons.BOARD + "  Board Info", self._import_board_info),
            (Icons.BOM + "  Bill of Materials (BOM)", self._import_bom),
            (Icons.LAYERS + "  Layer Stackup", self._import_stackup),
            (Icons.LAYERS + "  Layer Info", self._import_layers),
            (None, None),
            (Icons.NETLIST + "  Netlist", self._import_netlist),
            (Icons.NETLIST + "  Differential Pairs", self._import_diff_pairs),
            (Icons.RULES + "  Design Rules", self._import_design_rules),
            (Icons.DRILL + "  Drill Table", self._import_drill_table),
            (None, None),
            (Icons.ALL + "  Import All", self._import_all),
        ]
        
        for label, handler in items:
            if label is None:
                menu.AppendSeparator()
            else:
                item = menu.Append(wx.ID_ANY, label)
                if handler:
                    menu.Bind(wx.EVT_MENU, handler, item)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def _get_import_header(self, title):
        """Generate header with title and date for imported content."""
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"## {title}\n**Imported:** {date_str}\n\n"
    
    def _import_board_info(self, event):
        """Import board size/info."""
        try:
            header = self._get_import_header("Board Information")
            info = self.metadata_extractor.extract('board_size')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing board info: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_bom(self, event):
        """Import Bill of Materials."""
        try:
            header = self._get_import_header("Bill of Materials")
            info = self.metadata_extractor.extract('bom')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing BOM: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_stackup(self, event):
        """Import layer stackup."""
        try:
            header = self._get_import_header("Layer Stackup")
            info = self.metadata_extractor.extract('stackup')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing stackup: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_layers(self, event):
        """Import layer information."""
        try:
            header = self._get_import_header("Layer Information")
            info = self.metadata_extractor.extract('layers')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing layers: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_netlist(self, event):
        """Import netlist summary."""
        try:
            header = self._get_import_header("Netlist Summary")
            info = self.metadata_extractor.extract('netlist')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing netlist: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_diff_pairs(self, event):
        """Import differential pairs."""
        try:
            header = self._get_import_header("Differential Pairs")
            info = self.metadata_extractor.extract('diff_pairs')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing differential pairs: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_design_rules(self, event):
        """Import design rules."""
        try:
            header = self._get_import_header("Design Rules")
            info = self.metadata_extractor.extract('design_rules')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing design rules: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_drill_table(self, event):
        """Import drill table."""
        try:
            header = self._get_import_header("Drill Table")
            info = self.metadata_extractor.extract('drill_table')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing drill table: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _import_all(self, event):
        """Import all metadata."""
        try:
            header = self._get_import_header("Complete Board Metadata")
            info = self.metadata_extractor.extract('all')
            self._insert_text(header + info)
        except Exception as e:
            wx.MessageBox(f"Error importing all metadata: {e}", "Import Error", wx.OK | wx.ICON_ERROR)
    
    def _insert_text(self, text):
        """Insert text at cursor or end."""
        try:
            current = self.text_editor.GetValue()
            if current and not current.endswith("\n"):
                current += "\n"
            current += "\n" + text
            self.text_editor.SetValue(current)
            self.text_editor.SetInsertionPointEnd()
            self._apply_editor_colors()
            self._show_tab(0)
        except:
            pass
    
    def _on_export_pdf(self):
        """Export notes to PDF."""
        try:
            content = self.text_editor.GetValue()
            filepath = self.pdf_exporter.export(content)
            if filepath:
                wx.MessageBox("Exported to:\n" + filepath, "PDF Export", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox("Export failed: " + str(e), "Error", wx.OK | wx.ICON_ERROR)
    
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
                if word.startswith("@"):
                    self._highlight_component(word[1:])
                    return
        except:
            pass
        event.Skip()
    
    def _get_word_at_pos(self, text, pos):
        if pos < 0 or pos >= len(text):
            return ""
        start = end = pos
        while start > 0 and (text[start-1].isalnum() or text[start-1] in "@_"):
            start -= 1
        while end < len(text) and (text[end].isalnum() or text[end] in "@_"):
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
                self._add_todo_item(todo.get("text", ""), todo.get("done", False))
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
            todos = [{"text": item["text"].GetValue(), "done": item["checkbox"].GetValue()} 
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
