"""
KiNotes Visual Editor - WYSIWYG Rich Text Editor for KiCad 9+
========================================================================
A visual note editor using wx.richtext.RichTextCtrl that provides a 
Notion-like WYSIWYG experience. Supports:
- Bold, Italic, Underline, Strikethrough
- Headings (H1, H2, H3)
- Bullet Lists, Numbered Lists, Checkboxes
- Horizontal Dividers
- Timestamps
- Images (inline)
- Tables
- Links

All content is stored as Markdown (.md) files for compatibility.
Requires: wxPython 4.1+ (included in KiCad 9+)

Author: KiNotes Team (pcbtools.xyz)
License: MIT
"""
import wx
import wx.richtext as rt
import os
import re
import datetime
from typing import Optional, Tuple, List


# ============================================================
# DPI SCALING UTILITIES
# ============================================================
_dpi_scale_factor = None

def get_dpi_scale_factor(window=None):
    """Get the DPI scale factor for high-DPI displays."""
    global _dpi_scale_factor
    if _dpi_scale_factor is not None:
        return _dpi_scale_factor
    
    try:
        if window:
            if hasattr(window, 'GetDPIScaleFactor'):
                _dpi_scale_factor = window.GetDPIScaleFactor()
                return _dpi_scale_factor
            elif hasattr(window, 'GetContentScaleFactor'):
                _dpi_scale_factor = window.GetContentScaleFactor()
                return _dpi_scale_factor
        
        dc = wx.ScreenDC()
        dpi = dc.GetPPI()
        _dpi_scale_factor = dpi[0] / 96.0
    except:
        _dpi_scale_factor = 1.0
    
    return _dpi_scale_factor

def scale_size(size, window=None):
    """Scale a size tuple or int for DPI."""
    factor = get_dpi_scale_factor(window)
    if isinstance(size, tuple):
        return (int(size[0] * factor), int(size[1] * factor))
    return int(size * factor)


# ============================================================
# VISUAL EDITOR STYLES - Dark/Light Theme Aware
# ============================================================

class VisualEditorStyles:
    """Style definitions for the visual editor."""
    
    # Font sizes in points
    FONT_SIZE_NORMAL = 11
    FONT_SIZE_H1 = 22
    FONT_SIZE_H2 = 18
    FONT_SIZE_H3 = 14
    FONT_SIZE_CODE = 10
    
    # List markers
    BULLET_CHARS = ["•", "◦", "▪"]
    CHECKBOX_UNCHECKED = "☐"
    CHECKBOX_CHECKED = "☑"
    
    # Divider
    DIVIDER_CHAR = "─" * 40
    
    @classmethod
    def get_heading_style(cls, level: int, dark_mode: bool = False) -> rt.RichTextAttr:
        """Get heading style for level 1-3."""
        attr = rt.RichTextAttr()
        
        if level == 1:
            attr.SetFontSize(cls.FONT_SIZE_H1)
            attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
            attr.SetParagraphSpacingBefore(20)
            attr.SetParagraphSpacingAfter(10)
        elif level == 2:
            attr.SetFontSize(cls.FONT_SIZE_H2)
            attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
            attr.SetParagraphSpacingBefore(16)
            attr.SetParagraphSpacingAfter(8)
        else:  # H3
            attr.SetFontSize(cls.FONT_SIZE_H3)
            attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
            attr.SetParagraphSpacingBefore(12)
            attr.SetParagraphSpacingAfter(6)
        
        # Set text color based on theme
        if dark_mode:
            attr.SetTextColour(wx.Colour(255, 255, 255))
        else:
            attr.SetTextColour(wx.Colour(30, 30, 30))
        
        return attr
    
    @classmethod
    def get_normal_style(cls, dark_mode: bool = False) -> rt.RichTextAttr:
        """Get normal paragraph style."""
        attr = rt.RichTextAttr()
        attr.SetFontSize(cls.FONT_SIZE_NORMAL)
        attr.SetFontWeight(wx.FONTWEIGHT_NORMAL)
        attr.SetFontStyle(wx.FONTSTYLE_NORMAL)
        attr.SetFontUnderlined(False)
        attr.SetParagraphSpacingBefore(4)
        attr.SetParagraphSpacingAfter(4)
        
        if dark_mode:
            attr.SetTextColour(wx.Colour(230, 230, 230))
        else:
            attr.SetTextColour(wx.Colour(50, 50, 50))
        
        return attr
    
    @classmethod
    def get_code_style(cls, dark_mode: bool = False) -> rt.RichTextAttr:
        """Get code/monospace style."""
        attr = rt.RichTextAttr()
        attr.SetFontSize(cls.FONT_SIZE_CODE)
        attr.SetFontFaceName("Consolas" if os.name == 'nt' else "Monaco")
        
        if dark_mode:
            attr.SetTextColour(wx.Colour(152, 195, 121))  # Green-ish
            attr.SetBackgroundColour(wx.Colour(40, 44, 52))
        else:
            attr.SetTextColour(wx.Colour(200, 40, 40))
            attr.SetBackgroundColour(wx.Colour(245, 245, 245))
        
        return attr
    
    @classmethod
    def get_link_style(cls, dark_mode: bool = False) -> rt.RichTextAttr:
        """Get hyperlink style."""
        attr = rt.RichTextAttr()
        attr.SetFontSize(cls.FONT_SIZE_NORMAL)
        attr.SetFontUnderlined(True)
        
        if dark_mode:
            attr.SetTextColour(wx.Colour(97, 175, 239))  # Light blue
        else:
            attr.SetTextColour(wx.Colour(0, 102, 204))  # Standard link blue
        
        return attr
    
    @classmethod
    def get_table_header_style(cls, dark_mode: bool = False) -> rt.RichTextAttr:
        """Get table header cell style."""
        attr = rt.RichTextAttr()
        attr.SetFontSize(cls.FONT_SIZE_NORMAL)
        attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
        
        if dark_mode:
            attr.SetTextColour(wx.Colour(255, 255, 255))
            attr.SetBackgroundColour(wx.Colour(58, 58, 60))
        else:
            attr.SetTextColour(wx.Colour(30, 30, 30))
            attr.SetBackgroundColour(wx.Colour(240, 240, 240))
        
        return attr
    
    @classmethod
    def get_table_cell_style(cls, dark_mode: bool = False) -> rt.RichTextAttr:
        """Get table cell style."""
        attr = rt.RichTextAttr()
        attr.SetFontSize(cls.FONT_SIZE_NORMAL)
        attr.SetFontWeight(wx.FONTWEIGHT_NORMAL)
        
        if dark_mode:
            attr.SetTextColour(wx.Colour(230, 230, 230))
        else:
            attr.SetTextColour(wx.Colour(50, 50, 50))
        
        return attr


# ============================================================
# VISUAL NOTE EDITOR - Main Editor Control
# ============================================================

class VisualNoteEditor(wx.Panel):
    """
    WYSIWYG Rich Text Editor for KiNotes.
    
    Provides a Notion-like editing experience with:
    - Toolbar with formatting buttons
    - Rich text editing capabilities
    - Automatic Markdown conversion on save
    - Dark mode support
    - KiCad 9+ / wxWidgets 3.2+ compatible
    """
    
    def __init__(self, parent, dark_mode: bool = False, style: int = 0):
        """
        Initialize the Visual Note Editor.
        
        Args:
            parent: Parent wx.Window
            dark_mode: Enable dark theme colors
            style: Window style flags (e.g., wx.BORDER_NONE)
        """
        super().__init__(parent, style=style)
        
        self._dark_mode = dark_mode
        self._modified = False
        self._current_list_type = None  # 'bullet', 'numbered', 'checkbox'
        self._list_item_number = 0
        
        # Theme colors - custom colors override defaults
        self._custom_bg_color = None  # User-selected background color
        self._custom_text_color = None  # User-selected text color
        self._update_theme_colors()
        self.SetBackgroundColour(self._bg_color)
        
        self._init_ui()
        self._bind_events()
    
    def _update_theme_colors(self):
        """Update colors based on current theme, respecting custom colors."""
        # Set default theme colors based on dark/light mode
        if self._dark_mode:
            default_bg = wx.Colour(28, 28, 30)
            default_text = wx.Colour(255, 255, 255)
            self._toolbar_bg = wx.Colour(44, 44, 46)
            self._secondary_text = wx.Colour(152, 152, 157)
            self._accent_color = wx.Colour(10, 132, 255)
            self._border_color = wx.Colour(58, 58, 60)
            self._button_bg = wx.Colour(58, 58, 60)
            self._button_hover = wx.Colour(72, 72, 74)
        else:
            default_bg = wx.Colour(255, 255, 255)
            default_text = wx.Colour(30, 30, 30)
            self._toolbar_bg = wx.Colour(248, 248, 248)
            self._secondary_text = wx.Colour(142, 142, 147)
            self._accent_color = wx.Colour(0, 122, 255)
            self._border_color = wx.Colour(220, 220, 220)
            self._button_bg = wx.Colour(240, 240, 240)
            self._button_hover = wx.Colour(225, 225, 225)
        
        # Apply custom colors if set, otherwise use defaults
        self._bg_color = self._custom_bg_color if self._custom_bg_color else default_bg
        self._text_color = self._custom_text_color if self._custom_text_color else default_text
    
    def update_dark_mode(self, dark_mode: bool, force_refresh: bool = False):
        """
        Update editor to new dark mode setting.
        
        Args:
            dark_mode: True for dark theme, False for light
            force_refresh: Force refresh even if mode unchanged
        """
        mode_changed = self._dark_mode != dark_mode
        if not mode_changed and not force_refresh:
            return
        
        self._dark_mode = dark_mode
        self._update_theme_colors()
        self._apply_visual_theme()
    
    def set_custom_colors(self, bg_color: wx.Colour = None, text_color: wx.Colour = None):
        """
        Set custom background and text colors that persist across theme updates.
        
        Args:
            bg_color: Custom background color (or None to reset to default)
            text_color: Custom text color (or None to reset to default)
        """
        # Store custom colors (they will persist across dark mode toggles)
        self._custom_bg_color = bg_color
        self._custom_text_color = text_color
        
        # Update the active colors
        if bg_color:
            self._bg_color = bg_color
        if text_color:
            self._text_color = text_color
        
        # Apply the visual changes
        self._apply_visual_theme()
    
    def _apply_visual_theme(self):
        """Apply current theme colors to all UI elements."""
        try:
            # Update panel and toolbar colors
            self.SetBackgroundColour(self._bg_color)
            if hasattr(self, '_toolbar') and self._toolbar:
                self._toolbar.SetBackgroundColour(self._toolbar_bg)
            
            # Update editor colors
            if hasattr(self, '_editor') and self._editor:
                self._editor.SetBackgroundColour(self._bg_color)
                # Re-apply basic style with new colors
                basic_style = rt.RichTextAttr()
                basic_style.SetTextColour(self._text_color)
                basic_style.SetBackgroundColour(self._bg_color)
                self._editor.SetBasicStyle(basic_style)
                
                # Update default style for new text
                self._editor.SetDefaultStyle(basic_style)
                
                # Apply new text color to ALL existing text
                text_length = self._editor.GetLastPosition()
                if text_length > 0:
                    # Create style for existing text (preserve formatting, change color)
                    color_attr = rt.RichTextAttr()
                    color_attr.SetTextColour(self._text_color)
                    color_attr.SetFlags(wx.TEXT_ATTR_TEXT_COLOUR)
                    self._editor.SetStyleEx(
                        rt.RichTextRange(0, text_length),
                        color_attr,
                        rt.RICHTEXT_SETSTYLE_WITH_UNDO
                    )
            
            # Update toolbar buttons
            if hasattr(self, '_toolbar_buttons') and self._toolbar_buttons:
                for btn in self._toolbar_buttons.values():
                    btn.SetBackgroundColour(self._toolbar_bg)
                    btn.SetForegroundColour(self._text_color)
            
            # Only refresh if we're shown
            if self.IsShown():
                self.Refresh()
                self.Layout()
        except Exception:
            # Silently handle theme update errors to prevent crashes
            pass
    
    @property
    def editor(self):
        """Get the underlying RichTextCtrl editor."""
        return self._editor

    def _init_ui(self):
        """Initialize UI components."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create formatting toolbar
        self._toolbar = self._create_toolbar()
        main_sizer.Add(self._toolbar, 0, wx.EXPAND)
        
        # Create rich text editor
        self._editor = rt.RichTextCtrl(
            self,
            style=wx.VSCROLL | wx.HSCROLL | wx.BORDER_NONE | wx.WANTS_CHARS
        )
        
        # Configure editor appearance
        self._editor.SetBackgroundColour(self._bg_color)
        self._configure_editor_styles()
        
        main_sizer.Add(self._editor, 1, wx.EXPAND | wx.ALL, 8)
        
        self.SetSizer(main_sizer)
    
    def _create_toolbar(self) -> wx.Panel:
        """Create the formatting toolbar with all buttons."""
        toolbar = wx.Panel(self)
        toolbar.SetBackgroundColour(self._toolbar_bg)
        toolbar.SetMinSize((-1, scale_size(44, self)))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(scale_size(8, self))
        
        # Define toolbar buttons
        # Format: (label, tooltip, callback, is_toggle)
        button_groups = [
            # Text formatting - unified simple text icons
            [
                ("B", "Bold (Ctrl+B)", self._on_bold, True),
                ("I", "Italic (Ctrl+I)", self._on_italic, True),
                ("U", "Underline (Ctrl+U)", self._on_underline, True),
                ("ab", "Strikethrough", self._on_strikethrough, True),
            ],
            # Headings
            [
                ("H1", "Heading 1", self._on_heading1, False),
                ("H2", "Heading 2", self._on_heading2, False),
                ("H3", "Heading 3", self._on_heading3, False),
            ],
            # Lists
            [
                ("•", "Bullet List", self._on_bullet_list, False),
                ("1.", "Numbered List", self._on_numbered_list, False),
            ],
            # Insert
            [
                ("—", "Divider", self._on_divider, False),
                ("⏱", "Timestamp", self._on_timestamp, False),
                ("⛓", "Link", self._on_insert_link, False),
                ("🖼", "Image", self._on_insert_image, False),
                ("⊞", "Table", self._on_insert_table, False),
            ],
            # Undo/Redo
            [
                ("↶", "Undo (Ctrl+Z)", self._on_undo, False),
                ("↷", "Redo (Ctrl+Y)", self._on_redo, False),
            ],
        ]
        
        self._toolbar_buttons = {}
        
        for group_idx, group in enumerate(button_groups):
            if group_idx > 0:
                # Add separator
                sep = wx.StaticLine(toolbar, style=wx.LI_VERTICAL)
                sep.SetMinSize((1, scale_size(28, self)))
                sizer.Add(sep, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, scale_size(6, self))
            
            for label, tooltip, callback, is_toggle in group:
                btn = self._create_toolbar_button(toolbar, label, tooltip, callback)
                self._toolbar_buttons[label] = btn
                sizer.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, scale_size(2, self))
        
        sizer.AddStretchSpacer()
        
        # Clear formatting button on right
        clear_btn = self._create_toolbar_button(toolbar, "✕", "Clear Formatting", self._on_clear_format)
        sizer.Add(clear_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, scale_size(8, self))
        
        toolbar.SetSizer(sizer)
        return toolbar
    
    def _create_toolbar_button(self, parent, label: str, tooltip: str, callback) -> wx.Button:
        """Create a toolbar button with consistent styling."""
        btn_size = scale_size((36, 32), self)
        btn = wx.Button(parent, label=label, size=btn_size, style=wx.BORDER_NONE)
        btn.SetBackgroundColour(self._toolbar_bg)
        btn.SetForegroundColour(self._text_color)
        btn.SetToolTip(tooltip)
        
        # Store active state for toggle buttons
        btn._is_active = False
        btn._base_label = label
        
        # Set font - unified styling for all buttons
        if label in ("B", "I", "U"):
            # Bold/Italic/Underline with appropriate style
            style = wx.FONTSTYLE_ITALIC if label == "I" else wx.FONTSTYLE_NORMAL
            btn.SetFont(wx.Font(13, wx.FONTFAMILY_DEFAULT, style, wx.FONTWEIGHT_BOLD))
        elif label == "ab":
            # Strikethrough - smaller font
            btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        elif len(label) <= 2:
            btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        else:
            btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        btn.Bind(wx.EVT_BUTTON, callback)
        btn.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        
        # Hover effect - respects active state
        def on_enter(evt):
            if not btn._is_active:
                btn.SetBackgroundColour(self._button_hover)
                btn.Refresh()
        
        def on_leave(evt):
            if not btn._is_active:
                btn.SetBackgroundColour(self._toolbar_bg)
                btn.Refresh()
        
        btn.Bind(wx.EVT_ENTER_WINDOW, on_enter)
        btn.Bind(wx.EVT_LEAVE_WINDOW, on_leave)
        
        return btn
    
    def _set_button_active(self, btn, active: bool):
        """Set a toolbar button's active (highlighted) state."""
        if not hasattr(btn, '_is_active'):
            return
        
        btn._is_active = active
        
        if active:
            # Highlighted state - accent color background
            btn.SetBackgroundColour(self._accent_color)
            btn.SetForegroundColour(wx.Colour(255, 255, 255))
        else:
            # Normal state
            btn.SetBackgroundColour(self._toolbar_bg)
            btn.SetForegroundColour(self._text_color)
        
        btn.Refresh()
    
    def _update_toolbar_states(self):
        """Update toolbar button highlight states based on current text formatting."""
        if not hasattr(self, '_toolbar_buttons') or not self._toolbar_buttons:
            return
        
        try:
            # Get style at current position
            attr = rt.RichTextAttr()
            pos = self._editor.GetInsertionPoint()
            
            # Try to get style from selection or insertion point
            if self._editor.HasSelection():
                self._editor.GetStyleForRange(self._editor.GetSelectionRange(), attr)
            else:
                self._editor.GetStyle(pos, attr)
            
            # Check Bold
            if "B" in self._toolbar_buttons:
                is_bold = attr.HasFontWeight() and attr.GetFontWeight() == wx.FONTWEIGHT_BOLD
                self._set_button_active(self._toolbar_buttons["B"], is_bold)
            
            # Check Italic
            if "I" in self._toolbar_buttons:
                is_italic = attr.HasFontItalic() and attr.GetFontStyle() == wx.FONTSTYLE_ITALIC
                self._set_button_active(self._toolbar_buttons["I"], is_italic)
            
            # Check Underline
            if "U" in self._toolbar_buttons:
                is_underline = attr.HasFontUnderlined() and attr.GetFontUnderlined()
                self._set_button_active(self._toolbar_buttons["U"], is_underline)
            
            # Check Strikethrough
            if "ab" in self._toolbar_buttons:
                effects = attr.GetTextEffects() if attr.HasTextEffects() else 0
                is_strike = bool(effects & wx.TEXT_ATTR_EFFECT_STRIKETHROUGH)
                self._set_button_active(self._toolbar_buttons["ab"], is_strike)
        
        except Exception:
            # Silently handle errors during state update
            pass
    
    def _on_selection_changed(self, event):
        """Handle selection or style change - update toolbar button states."""
        self._update_toolbar_states()
        event.Skip()
    
    def _on_focus_change(self, event):
        """Handle focus change - update toolbar states."""
        self._update_toolbar_states()
        event.Skip()
    
    def _configure_editor_styles(self):
        """Configure the rich text editor default styles."""
        # Get the style sheet
        stylesheet = self._editor.GetStyleSheet()
        if stylesheet is None:
            stylesheet = rt.RichTextStyleSheet()
            self._editor.SetStyleSheet(stylesheet)
        
        # Set default font
        default_font = wx.Font(
            VisualEditorStyles.FONT_SIZE_NORMAL,
            wx.FONTFAMILY_DEFAULT,
            wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self._editor.SetFont(default_font)
        
        # Set default text color
        basic_style = rt.RichTextAttr()
        basic_style.SetTextColour(self._text_color)
        basic_style.SetBackgroundColour(self._bg_color)
        self._editor.SetBasicStyle(basic_style)
    
    def _bind_events(self):
        """Bind editor events."""
        self._editor.Bind(wx.EVT_TEXT, self._on_text_changed)
        self._editor.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
        self._editor.Bind(wx.EVT_LEFT_UP, self._on_click)
        # Update toolbar button states on selection change
        self._editor.Bind(wx.EVT_SET_FOCUS, self._on_focus_change)
        self._editor.Bind(rt.EVT_RICHTEXT_SELECTION_CHANGED, self._on_selection_changed)
        self._editor.Bind(rt.EVT_RICHTEXT_STYLE_CHANGED, self._on_selection_changed)
    
    # ============================================================
    # FORMATTING HANDLERS
    # ============================================================
    
    def _on_bold(self, event):
        """Toggle bold formatting."""
        self._editor.ApplyBoldToSelection()
        self._modified = True
        self._update_toolbar_states()
    
    def _on_italic(self, event):
        """Toggle italic formatting."""
        self._editor.ApplyItalicToSelection()
        self._modified = True
        self._update_toolbar_states()
    
    def _on_underline(self, event):
        """Toggle underline formatting."""
        self._editor.ApplyUnderlineToSelection()
        self._modified = True
        self._update_toolbar_states()
    
    def _on_strikethrough(self, event):
        """Toggle strikethrough formatting."""
        # RichTextCtrl doesn't have built-in strikethrough
        # We'll use a text effect workaround
        attr = rt.RichTextAttr()
        attr.SetTextEffects(wx.TEXT_ATTR_EFFECT_STRIKETHROUGH)
        attr.SetTextEffectFlags(wx.TEXT_ATTR_EFFECT_STRIKETHROUGH)
        self._editor.SetStyleEx(
            self._editor.GetSelectionRange(),
            attr,
            rt.RICHTEXT_SETSTYLE_WITH_UNDO
        )
        self._modified = True
        self._update_toolbar_states()
    
    def _apply_heading(self, level: int):
        """Apply heading style to current paragraph."""
        attr = VisualEditorStyles.get_heading_style(level, self._dark_mode)
        
        # Get current paragraph range
        pos = self._editor.GetInsertionPoint()
        line_start = self._editor.XYToPosition(0, self._editor.PositionToXY(pos)[2])
        line_end = line_start
        
        # Find end of line
        text = self._editor.GetValue()
        while line_end < len(text) and text[line_end] != '\n':
            line_end += 1
        
        # Apply style to paragraph
        self._editor.SetStyleEx(
            rt.RichTextRange(line_start, line_end),
            attr,
            rt.RICHTEXT_SETSTYLE_WITH_UNDO | rt.RICHTEXT_SETSTYLE_PARAGRAPHS_ONLY
        )
        self._modified = True
    
    def _insert_heading(self, text: str, level: int):
        """
        Insert a new heading with proper styling.
        
        Args:
            text: The heading text to insert
            level: Heading level (1, 2, or 3)
        """
        attr = VisualEditorStyles.get_heading_style(level, self._dark_mode)
        
        # Begin the styled paragraph
        self._editor.BeginStyle(attr)
        self._editor.WriteText(text)
        self._editor.EndStyle()
        self._editor.WriteText("\n")
        self._modified = True
    
    def _on_heading1(self, event):
        """Apply H1 heading."""
        self._apply_heading(1)
    
    def _on_heading2(self, event):
        """Apply H2 heading."""
        self._apply_heading(2)
    
    def _on_heading3(self, event):
        """Apply H3 heading."""
        self._apply_heading(3)
    
    def _on_bullet_list(self, event):
        """Insert bullet list item."""
        self._insert_list_item("bullet")
    
    def _on_numbered_list(self, event):
        """Insert numbered list item."""
        self._insert_list_item("numbered")
    
    def _on_checkbox(self, event):
        """Insert checkbox list item."""
        self._insert_list_item("checkbox")
    
    def _insert_list_item(self, list_type: str):
        """Insert a list item of the specified type."""
        pos = self._editor.GetInsertionPoint()
        
        # Determine prefix based on type
        if list_type == "bullet":
            prefix = "• "
        elif list_type == "numbered":
            self._list_item_number += 1
            prefix = f"{self._list_item_number}. "
        else:  # checkbox
            prefix = "☐ "
        
        # Insert at beginning of line or current position
        text = self._editor.GetValue()
        if pos > 0 and text[pos - 1] != '\n':
            prefix = "\n" + prefix
        
        self._editor.WriteText(prefix)
        self._modified = True
    
    def _on_divider(self, event):
        """Insert horizontal divider."""
        pos = self._editor.GetInsertionPoint()
        text = self._editor.GetValue()
        
        # Ensure we're on a new line
        prefix = ""
        if pos > 0 and text[pos - 1] != '\n':
            prefix = "\n"
        
        self._editor.WriteText(f"{prefix}{'─' * 40}\n")
        self._modified = True
    
    def _on_timestamp(self, event):
        """Insert current timestamp."""
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M")
        self._editor.WriteText(f"[{timestamp}] ")
        self._modified = True
    
    def _on_insert_link(self, event):
        """Insert a hyperlink."""
        dlg = wx.TextEntryDialog(
            self,
            "Enter URL:",
            "Insert Link",
            ""
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            url = dlg.GetValue().strip()
            if url:
                # Get selected text or use URL as text
                selection = self._editor.GetStringSelection()
                link_text = selection if selection else url
                
                # Insert link with styling
                attr = VisualEditorStyles.get_link_style(self._dark_mode)
                attr.SetURL(url)
                
                if selection:
                    self._editor.SetStyleEx(
                        self._editor.GetSelectionRange(),
                        attr,
                        rt.RICHTEXT_SETSTYLE_WITH_UNDO
                    )
                else:
                    self._editor.BeginStyle(attr)
                    self._editor.WriteText(link_text)
                    self._editor.EndStyle()
                
                self._modified = True
        
        dlg.Destroy()
    
    def _on_insert_image(self, event):
        """Insert an image."""
        wildcard = "Image files (*.png;*.jpg;*.jpeg;*.gif;*.bmp)|*.png;*.jpg;*.jpeg;*.gif;*.bmp"
        
        dlg = wx.FileDialog(
            self,
            "Select Image",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            image_path = dlg.GetPath()
            try:
                # Load and insert image
                image = wx.Image(image_path, wx.BITMAP_TYPE_ANY)
                
                # Scale if too large
                max_width = 400
                if image.GetWidth() > max_width:
                    ratio = max_width / image.GetWidth()
                    new_height = int(image.GetHeight() * ratio)
                    image = image.Scale(max_width, new_height, wx.IMAGE_QUALITY_HIGH)
                
                self._editor.WriteImage(image)
                self._modified = True
            except Exception as e:
                wx.MessageBox(f"Failed to insert image: {e}", "Error", wx.OK | wx.ICON_ERROR)
        
        dlg.Destroy()
    
    def _on_insert_table(self, event):
        """Insert a proper RichText table with visual styling."""
        # Ask for table dimensions - scale dialog size for DPI
        dlg_size = scale_size((320, 320), self)
        dlg = wx.Dialog(self, title="Insert Table", size=dlg_size,
                       style=wx.DEFAULT_DIALOG_STYLE)
        dlg.SetBackgroundColour(self._bg_color)
        
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.AddSpacer(scale_size(16, self))
        
        # Rows input
        row_sizer = wx.BoxSizer(wx.HORIZONTAL)
        row_label = wx.StaticText(dlg, label="Rows:")
        row_label.SetForegroundColour(self._text_color)
        row_label.SetMinSize((scale_size(100, self), -1))
        row_sizer.Add(row_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, scale_size(10, self))
        row_spin = wx.SpinCtrl(dlg, min=2, max=50, initial=4)
        row_spin.SetMinSize((scale_size(100, self), -1))
        row_sizer.Add(row_spin, 0, wx.EXPAND)
        panel_sizer.Add(row_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, scale_size(20, self))
        
        panel_sizer.AddSpacer(scale_size(10, self))
        
        # Columns input
        col_sizer = wx.BoxSizer(wx.HORIZONTAL)
        col_label = wx.StaticText(dlg, label="Columns:")
        col_label.SetForegroundColour(self._text_color)
        col_label.SetMinSize((scale_size(100, self), -1))
        col_sizer.Add(col_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, scale_size(10, self))
        col_spin = wx.SpinCtrl(dlg, min=2, max=10, initial=4)
        col_spin.SetMinSize((scale_size(100, self), -1))
        col_sizer.Add(col_spin, 0, wx.EXPAND)
        panel_sizer.Add(col_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, scale_size(20, self))
        
        panel_sizer.AddSpacer(scale_size(10, self))
        
        # Row Height input
        height_sizer = wx.BoxSizer(wx.HORIZONTAL)
        height_label = wx.StaticText(dlg, label="Row Height:")
        height_label.SetForegroundColour(self._text_color)
        height_label.SetMinSize((scale_size(100, self), -1))
        height_sizer.Add(height_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, scale_size(10, self))
        height_spin = wx.SpinCtrl(dlg, min=20, max=200, initial=30)
        height_spin.SetMinSize((scale_size(80, self), -1))
        height_sizer.Add(height_spin, 0)
        height_unit = wx.StaticText(dlg, label="px")
        height_unit.SetForegroundColour(self._text_color)
        height_sizer.Add(height_unit, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, scale_size(5, self))
        panel_sizer.Add(height_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, scale_size(20, self))
        
        panel_sizer.AddSpacer(scale_size(10, self))
        
        # Column Width input
        width_sizer = wx.BoxSizer(wx.HORIZONTAL)
        width_label = wx.StaticText(dlg, label="Column Width:")
        width_label.SetForegroundColour(self._text_color)
        width_label.SetMinSize((scale_size(100, self), -1))
        width_sizer.Add(width_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, scale_size(10, self))
        width_spin = wx.SpinCtrl(dlg, min=40, max=500, initial=100)
        width_spin.SetMinSize((scale_size(80, self), -1))
        width_sizer.Add(width_spin, 0)
        width_unit = wx.StaticText(dlg, label="px")
        width_unit.SetForegroundColour(self._text_color)
        width_sizer.Add(width_unit, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, scale_size(5, self))
        panel_sizer.Add(width_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, scale_size(20, self))
        
        panel_sizer.AddStretchSpacer()
        
        # Buttons - ensure visibility
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddStretchSpacer()
        
        cancel_btn = wx.Button(dlg, wx.ID_CANCEL, "Cancel")
        cancel_btn.SetMinSize(scale_size((80, 32), self))
        btn_sizer.Add(cancel_btn, 0, wx.RIGHT, scale_size(10, self))
        
        ok_btn = wx.Button(dlg, wx.ID_OK, "Insert Table")
        ok_btn.SetMinSize(scale_size((100, 32), self))
        ok_btn.SetDefault()
        btn_sizer.Add(ok_btn, 0)
        
        panel_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, scale_size(16, self))
        
        dlg.SetSizer(panel_sizer)
        dlg.Layout()
        dlg.CenterOnParent()
        
        if dlg.ShowModal() == wx.ID_OK:
            rows = row_spin.GetValue()
            cols = col_spin.GetValue()
            row_height = height_spin.GetValue()
            col_width = width_spin.GetValue()
            self._insert_rich_table(rows, cols, False, row_height=row_height, col_width=col_width)
        
        dlg.Destroy()
    
    def _insert_rich_table(self, rows: int, cols: int, has_header: bool = True, 
                          headers: List[str] = None, data: List[List[str]] = None,
                          row_height: int = None, col_width: int = None):
        """
        Insert a proper RichTextTable with styling.
        
        Args:
            rows: Number of rows (including header if has_header)
            cols: Number of columns
            has_header: Whether first row is header
            headers: Optional header text list
            data: Optional data rows list
            row_height: Optional row height in pixels
            col_width: Optional column width in pixels
        """
        # Ensure we're at end of line
        pos = self._editor.GetInsertionPoint()
        text = self._editor.GetValue()
        if pos > 0 and len(text) > 0 and text[pos - 1] != '\n':
            self._editor.WriteText("\n")
        
        # Calculate column widths - use provided width or auto-calculate
        if col_width is None:
            editor_width = self._editor.GetClientSize().GetWidth() - 40
            col_width = max(80, editor_width // cols)
        
        # Default row height if not provided
        if row_height is None:
            row_height = 30
        
        # Create the table with row/col dimensions
        table = self._editor.WriteTable(rows, cols)
        
        if table:
            # Style the table cells
            for row_idx in range(rows):
                for col_idx in range(cols):
                    cell = table.GetCell(row_idx, col_idx)
                    if cell:
                        # Set cell properties
                        cell_attr = rt.RichTextAttr()
                        
                        # Header row styling
                        if has_header and row_idx == 0:
                            cell_attr = VisualEditorStyles.get_table_header_style(self._dark_mode)
                            # Set header text
                            if headers and col_idx < len(headers):
                                cell_text = headers[col_idx]
                            else:
                                cell_text = f"Column {col_idx + 1}"
                        else:
                            cell_attr = VisualEditorStyles.get_table_cell_style(self._dark_mode)
                            # Set data text
                            data_row = row_idx - (1 if has_header else 0)
                            if data and data_row < len(data) and col_idx < len(data[data_row]):
                                cell_text = str(data[data_row][col_idx])
                            else:
                                cell_text = ""
                        
                        # Write cell content
                        self._editor.SetCaretPosition(cell.GetRange().GetStart())
                        self._editor.BeginStyle(cell_attr)
                        self._editor.WriteText(cell_text)
                        self._editor.EndStyle()
        
        # Move cursor to end of document after table insertion
        self._editor.MoveEnd()
        self._editor.WriteText("\n\n")
        self._modified = True
    
    def insert_data_table(self, headers: List[str], data: List[List[str]], title: str = None):
        """
        Public method to insert a formatted data table (for BOM, metadata, etc.)
        
        Args:
            headers: List of column header strings
            data: List of row data (each row is a list of cell values)
            title: Optional title to insert before table
        """
        # Insert title if provided
        if title:
            self._editor.BeginBold()
            self._editor.BeginFontSize(14)
            self._editor.WriteText(f"\n{title}\n")
            self._editor.EndFontSize()
            self._editor.EndBold()
        
        rows = len(data) + 1  # +1 for header
        cols = len(headers)
        
        if rows > 1 and cols > 0:
            self._insert_rich_table(rows, cols, True, headers, data)
        
        self._modified = True
    
    def insert_markdown_as_formatted(self, markdown_text: str):
        """
        Parse markdown text and insert as properly formatted rich text.
        Handles tables, headings, lists, etc.
        
        Args:
            markdown_text: Markdown formatted string
        """
        lines = markdown_text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for markdown table
            if line.strip().startswith('|') and '|' in line[1:]:
                # Collect all table lines
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i])
                    i += 1
                
                # Parse and insert as rich table
                self._parse_and_insert_markdown_table(table_lines)
                continue
            
            # Check for heading
            if line.startswith('#'):
                match = re.match(r'^(#{1,3})\s+(.+)$', line)
                if match:
                    level = len(match.group(1))
                    text = match.group(2)
                    self._insert_heading(text, level)
                    i += 1
                    continue
            
            # Check for bullet list
            if re.match(r'^\s*[-*+]\s+', line):
                match = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
                if match:
                    text = match.group(2)
                    self._editor.WriteText(f"• {text}\n")
                    i += 1
                    continue
            
            # Regular text
            if line.strip():
                self._editor.WriteText(line + "\n")
            else:
                self._editor.WriteText("\n")
            i += 1
        
        self._modified = True
    
    def _parse_and_insert_markdown_table(self, table_lines: List[str]):
        """Parse markdown table lines and insert as RichTextTable."""
        if len(table_lines) < 2:
            return
        
        # Parse headers (first line)
        header_line = table_lines[0]
        headers = [cell.strip() for cell in header_line.strip('|').split('|')]
        headers = [h for h in headers if h]  # Remove empty
        
        # Skip separator line (second line with ---)
        # Parse data rows
        data = []
        for line in table_lines[2:]:
            if '---' in line:
                continue
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            cells = [c for c in cells if c is not None]
            if cells:
                data.append(cells)
        
        # Insert as rich table
        if headers:
            self.insert_data_table(headers, data)
    
    def _on_undo(self, event):
        """Undo last action."""
        self._editor.Undo()
    
    def _on_redo(self, event):
        """Redo last undone action."""
        self._editor.Redo()
    
    def _on_clear_format(self, event):
        """Clear all formatting from selection."""
        attr = VisualEditorStyles.get_normal_style(self._dark_mode)
        self._editor.SetStyleEx(
            self._editor.GetSelectionRange(),
            attr,
            rt.RICHTEXT_SETSTYLE_WITH_UNDO | rt.RICHTEXT_SETSTYLE_REMOVE
        )
        self._modified = True
    
    # ============================================================
    # EVENT HANDLERS
    # ============================================================
    
    def _on_text_changed(self, event):
        """Handle text changes."""
        self._modified = True
        event.Skip()
    
    def _on_key_down(self, event):
        """Handle keyboard shortcuts."""
        key = event.GetKeyCode()
        ctrl = event.ControlDown()
        shift = event.ShiftDown()
        alt = event.AltDown()
        
        # ESC key - clear selection and update toolbar
        if key == wx.WXK_ESCAPE:
            if self._editor.HasSelection():
                # Clear selection - move cursor to end of selection
                sel_end = self._editor.GetSelectionRange().GetEnd()
                self._editor.SetInsertionPoint(sel_end)
                self._editor.SelectNone()
            self._update_toolbar_states()
            return
        
        # Keyboard shortcuts
        if ctrl and not shift and not alt:
            if key == ord('B'):
                self._on_bold(None)
                return
            elif key == ord('I'):
                self._on_italic(None)
                return
            elif key == ord('U'):
                self._on_underline(None)
                return
            elif key == ord('1'):
                self._on_heading1(None)
                return
            elif key == ord('2'):
                self._on_heading2(None)
                return
            elif key == ord('3'):
                self._on_heading3(None)
                return
            elif key == ord('Z'):
                self._on_undo(None)
                return
            elif key == ord('Y'):
                self._on_redo(None)
                return
        
        elif ctrl and shift:
            if key == ord('B'):
                self._on_bullet_list(None)
                return
            elif key == ord('N'):
                self._on_numbered_list(None)
                return
            elif key == ord('X'):
                self._on_checkbox(None)
                return
            elif key == ord('H'):
                self._on_divider(None)
                return
        
        elif alt:
            if key == ord('T'):
                self._on_timestamp(None)
                return
        
        # Handle Enter key for list continuation
        if key == wx.WXK_RETURN:
            self._handle_enter_key()
            return
        
        event.Skip()
    
    def _handle_enter_key(self):
        """Handle Enter key - continue lists if applicable."""
        pos = self._editor.GetInsertionPoint()
        text = self._editor.GetValue()
        
        # Find start of current line
        line_start = text.rfind('\n', 0, pos) + 1
        current_line = text[line_start:pos]
        
        # Check for list prefixes
        bullet_match = re.match(r'^([•◦▪]\s)', current_line)
        number_match = re.match(r'^(\d+)\.\s', current_line)
        checkbox_match = re.match(r'^([☐☑]\s)', current_line)
        
        if bullet_match:
            # Continue bullet list
            self._editor.WriteText('\n• ')
        elif number_match:
            # Continue numbered list
            next_num = int(number_match.group(1)) + 1
            self._editor.WriteText(f'\n{next_num}. ')
        elif checkbox_match:
            # Continue checkbox list
            self._editor.WriteText('\n☐ ')
        else:
            # Normal enter
            self._editor.WriteText('\n')
    
    def _on_click(self, event):
        """Handle mouse clicks - toggle checkboxes and update toolbar states."""
        pos = self._editor.GetInsertionPoint()
        text = self._editor.GetValue()
        
        # Only check for checkbox if there's actual text and position is valid
        if text and pos > 0 and pos <= len(text):
            # Get character at click position (pos-1 since pos is after character)
            char = text[pos - 1] if pos > 0 else ''
            
            # Only toggle if we clicked directly on a checkbox character
            # This prevents accidental checkbox insertion on empty lines or double-clicks
            if char in '☐☑':
                check_pos = pos - 1
                current_char = text[check_pos]
                new_char = '☑' if current_char == '☐' else '☐'
                
                # Replace the checkbox character
                self._editor.SetSelection(check_pos, check_pos + 1)
                self._editor.WriteText(new_char)
                self._modified = True
        
        # Update toolbar button states based on current formatting
        wx.CallAfter(self._update_toolbar_states)
        
        event.Skip()
    
    # ============================================================
    # PUBLIC API
    # ============================================================
    
    def SetValue(self, markdown_text: str):
        """
        Load Markdown content into the visual editor.
        Converts Markdown to rich text formatting.
        
        Args:
            markdown_text: Markdown formatted string
        """
        from .markdown_converter import MarkdownToRichText
        converter = MarkdownToRichText(self._editor, self._dark_mode)
        converter.convert(markdown_text)
        self._modified = False
    
    def GetValue(self) -> str:
        """
        Get content as Markdown string.
        Converts rich text formatting to Markdown.
        
        Returns:
            Markdown formatted string
        """
        from .markdown_converter import RichTextToMarkdown
        converter = RichTextToMarkdown(self._editor)
        return converter.convert()
    
    def GetRawText(self) -> str:
        """Get plain text content without formatting."""
        return self._editor.GetValue()
    
    def IsModified(self) -> bool:
        """Check if content has been modified."""
        return self._modified
    
    def SetModified(self, modified: bool):
        """Set the modified state."""
        self._modified = modified
    
    def SetDarkMode(self, dark_mode: bool):
        """
        Switch between dark and light mode.
        
        Args:
            dark_mode: True for dark mode, False for light mode
        """
        # Use the unified method with force refresh
        self.update_dark_mode(dark_mode, force_refresh=True)
    
    def Clear(self):
        """Clear all content."""
        self._editor.Clear()
        self._modified = False
    
    def SetInsertionPointEnd(self):
        """Move cursor to end of document."""
        self._editor.SetInsertionPointEnd()
    
    def GetInsertionPoint(self) -> int:
        """Get current cursor position."""
        return self._editor.GetInsertionPoint()
    
    def SetInsertionPoint(self, pos: int):
        """Set cursor position."""
        self._editor.SetInsertionPoint(pos)
    
    def CanUndo(self) -> bool:
        """Check if undo is available."""
        return self._editor.CanUndo()
    
    def CanRedo(self) -> bool:
        """Check if redo is available."""
        return self._editor.CanRedo()
    
    def GetEditor(self) -> rt.RichTextCtrl:
        """Get the underlying RichTextCtrl for advanced operations."""
        return self._editor
