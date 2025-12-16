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
import sys
import datetime
from typing import Optional, Tuple, List

from .debug_event_logger import EventLevel


def _kinotes_log(msg: str):
    """Log message to console, handling KiCad's None stdout."""
    try:
        if sys.stdout is not None:
            print(msg)
            sys.stdout.flush()
    except:
        pass  # Silently ignore if stdout not available


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
    
    # Font sizes in points (FONT_SIZE_NORMAL can be overridden by user settings)
    FONT_SIZE_NORMAL = 11  # Default, can be changed via settings (8-24)
    FONT_SIZE_H1 = 22
    FONT_SIZE_H2 = 18
    FONT_SIZE_H3 = 14
    FONT_SIZE_CODE = 10
    
    @classmethod
    def set_normal_font_size(cls, size: int):
        """Set the normal font size (8-24 points)."""
        cls.FONT_SIZE_NORMAL = max(8, min(24, size))
    
    # List markers
    BULLET_CHARS = ["•", "◦", "▪"]
    CHECKBOX_UNCHECKED = "☐"
    CHECKBOX_CHECKED = "☑"
    
    # Divider
    DIVIDER_CHAR = "─" * 40
    
    @classmethod
    def get_heading_style(cls, level: int, dark_mode: bool = False, text_color: wx.Colour = None) -> rt.RichTextAttr:
        """Get heading style for level 1-3.
        
        Args:
            level: Heading level (1, 2, or 3)
            dark_mode: Whether dark mode is enabled
            text_color: Custom text color (uses theme default if None)
        """
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
        
        # Set text color - use custom color if provided, else theme default
        if text_color:
            attr.SetTextColour(text_color)
        elif dark_mode:
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
    def get_table_header_style(cls, dark_mode: bool = False, text_color: wx.Colour = None, bg_color: wx.Colour = None) -> rt.RichTextAttr:
        """Get table header cell style.
        
        Args:
            dark_mode: Whether dark mode is enabled
            text_color: Custom text color (uses theme default if None)
            bg_color: Custom background color for header (uses theme default if None)
        """
        attr = rt.RichTextAttr()
        attr.SetFontSize(cls.FONT_SIZE_NORMAL)
        attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
        
        # Text color
        if text_color:
            attr.SetTextColour(text_color)
        elif dark_mode:
            attr.SetTextColour(wx.Colour(255, 255, 255))
        else:
            attr.SetTextColour(wx.Colour(30, 30, 30))
        
        # Header background - slightly different from main bg for contrast
        if bg_color:
            # Adjust provided bg for header contrast
            r, g, b = bg_color.Red(), bg_color.Green(), bg_color.Blue()
            if dark_mode:
                attr.SetBackgroundColour(wx.Colour(min(255, r + 20), min(255, g + 20), min(255, b + 20)))
            else:
                attr.SetBackgroundColour(wx.Colour(max(0, r - 15), max(0, g - 15), max(0, b - 15)))
        elif dark_mode:
            attr.SetBackgroundColour(wx.Colour(58, 58, 60))
        else:
            attr.SetBackgroundColour(wx.Colour(240, 240, 240))
        
        return attr
    
    @classmethod
    def get_table_cell_style(cls, dark_mode: bool = False, text_color: wx.Colour = None) -> rt.RichTextAttr:
        """Get table cell style.
        
        Args:
            dark_mode: Whether dark mode is enabled
            text_color: Custom text color (uses theme default if None)
        """
        attr = rt.RichTextAttr()
        attr.SetFontSize(cls.FONT_SIZE_NORMAL)
        attr.SetFontWeight(wx.FONTWEIGHT_NORMAL)
        
        if text_color:
            attr.SetTextColour(text_color)
        elif dark_mode:
            attr.SetTextColour(wx.Colour(230, 230, 230))
        else:
            attr.SetTextColour(wx.Colour(50, 50, 50))
        
        return attr


# ============================================================
# MARGIN PANEL - Clean left margin for breathing space
# ============================================================

class MarginPanel(wx.Panel):
    """
    Simple left margin panel for the visual editor.
    Provides breathing space between panel edge and text content.
    Matches theme colors seamlessly.
    """
    
    def __init__(self, parent, dark_mode: bool = False):
        super().__init__(parent, style=wx.BORDER_NONE)
        
        self._dark_mode = dark_mode
        
        # Margin width - 20 pixels for clean breathing space
        self._width = 20
        self.SetMinSize((self._width, 100))
        self.SetSize((self._width, -1))
        
        self._update_colors()
        self.SetBackgroundColour(self._bg_color)
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
    
    def _update_colors(self):
        """Update colors based on dark mode."""
        if self._dark_mode:
            # Match dark editor background
            self._bg_color = wx.Colour(30, 30, 32)
        else:
            # Match light editor background
            self._bg_color = wx.Colour(255, 255, 255)
    
    def set_editor(self, editor):
        """Set the associated editor (for API compatibility)."""
        pass  # No longer needed, but keep for compatibility
    
    def update_from_editor(self):
        """Update from editor (for API compatibility)."""
        pass  # No longer needed
    
    def _update_line_height(self):
        """For API compatibility."""
        pass
    
    def update_dark_mode(self, dark_mode: bool):
        """Update dark mode setting."""
        self._dark_mode = dark_mode
        self._update_colors()
        self.SetBackgroundColour(self._bg_color)
        self.Refresh()
    
    def _on_paint(self, event):
        """Paint the margin - just a clean solid color."""
        dc = wx.BufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self._bg_color))
        dc.Clear()


# Alias for backward compatibility
LineNumberPanel = MarginPanel


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
    - Smart cross-probe for PCB designators
    - KiCad 9+ / wxWidgets 3.2+ compatible
    """
    
    def __init__(self, parent, dark_mode: bool = False, style: int = 0, beta_features: bool = False):
        """
        Initialize the Visual Note Editor.
        
        Args:
            parent: Parent wx.Window
            dark_mode: Enable dark theme colors
            style: Window style flags (e.g., wx.BORDER_NONE)
            beta_features: Enable beta features like Table insertion
        """
        super().__init__(parent, style=style)
        
        self._dark_mode = dark_mode
        self._beta_features = beta_features
        self._modified = False
        self._current_list_type = None  # 'bullet', 'numbered', 'checkbox'
        self._list_item_number = 0
        self._font_size = VisualEditorStyles.FONT_SIZE_NORMAL  # User-configurable
        
        # Cross-probe settings
        self._crossprobe_enabled = True
        self._designator_linker = None  # Set by main panel
        self._net_linker = None  # Set by main panel (Beta)
        self._debug_logger = None
        self._debug_modules = {"net": False, "designator": False}
        
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
        
        # Update line numbers panel
        if hasattr(self, '_line_numbers') and self._line_numbers:
            self._line_numbers.update_dark_mode(dark_mode)
    
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
                
                # Apply new text color AND background to ALL existing text
                text_length = self._editor.GetLastPosition()
                if text_length > 0:
                    # Create style for existing text - update both text and background color
                    color_attr = rt.RichTextAttr()
                    color_attr.SetTextColour(self._text_color)
                    color_attr.SetBackgroundColour(self._bg_color)
                    color_attr.SetFlags(wx.TEXT_ATTR_TEXT_COLOUR | wx.TEXT_ATTR_BACKGROUND_COLOUR)
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
        
        # Create horizontal sizer for line numbers + editor
        editor_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Create line number panel
        self._line_numbers = LineNumberPanel(self, self._dark_mode)
        editor_sizer.Add(self._line_numbers, 0, wx.EXPAND)
        
        # Create rich text editor
        self._editor = rt.RichTextCtrl(
            self,
            style=wx.VSCROLL | wx.HSCROLL | wx.BORDER_NONE | wx.WANTS_CHARS
        )
        
        # Configure editor appearance
        self._editor.SetBackgroundColour(self._bg_color)
        self._configure_editor_styles()
        
        # Connect line numbers to editor
        self._line_numbers.set_editor(self._editor)
        
        editor_sizer.Add(self._editor, 1, wx.EXPAND)
        
        main_sizer.Add(editor_sizer, 1, wx.EXPAND | wx.ALL, 8)
        
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
        
        # Insert group - Table only shown when beta features enabled
        insert_buttons = [
            ("—", "Divider", self._on_divider, False),
            ("⏱", "Timestamp", self._on_timestamp, False),
            ("⛓", "Link", self._on_insert_link, False),
            ("🖼", "Image", self._on_insert_image, False),
        ]
        if self._beta_features:
            insert_buttons.append(("⊞", "Table (Beta)", self._on_insert_table, False))
        
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
            insert_buttons,
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
        try:
            print(f"[KiNotes] _configure_editor_styles: Entering")
            # Always create a fresh style sheet to avoid stale references
            print(f"[KiNotes] _configure_editor_styles: Creating fresh style sheet")
            try:
                stylesheet = rt.RichTextStyleSheet()
                self._editor.SetStyleSheet(stylesheet)
            except Exception as e:
                print(f"[KiNotes] _configure_editor_styles: Style sheet creation warning: {e}")
            
            print(f"[KiNotes] _configure_editor_styles: Creating font with size {self._font_size}")
            # Set default font using instance font size
            default_font = wx.Font(
                self._font_size,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL
            )
            print(f"[KiNotes] _configure_editor_styles: Setting font on editor")
            self._editor.SetFont(default_font)
            
            print(f"[KiNotes] _configure_editor_styles: Creating basic style")
            # Set default text color
            basic_style = rt.RichTextAttr()
            basic_style.SetTextColour(self._text_color)
            basic_style.SetBackgroundColour(self._bg_color)
            basic_style.SetFontSize(self._font_size)
            print(f"[KiNotes] _configure_editor_styles: Setting basic style on editor")
            self._editor.SetBasicStyle(basic_style)
            print(f"[KiNotes] _configure_editor_styles: Success!")
        except Exception as e:
            print(f"[KiNotes] Configure editor styles warning: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_normal_style_with_theme(self) -> rt.RichTextAttr:
        """Get normal style that respects the current theme colors."""
        attr = rt.RichTextAttr()
        attr.SetFontSize(VisualEditorStyles.FONT_SIZE_NORMAL)
        attr.SetFontWeight(wx.FONTWEIGHT_NORMAL)
        attr.SetFontStyle(wx.FONTSTYLE_NORMAL)
        attr.SetFontUnderlined(False)
        attr.SetParagraphSpacingBefore(4)
        attr.SetParagraphSpacingAfter(4)
        # Use the editor's actual theme colors
        attr.SetTextColour(self._text_color)
        attr.SetBackgroundColour(self._bg_color)
        return attr
    
    def set_font_size(self, size: int):
        """Set the editor font size (8-24 points)."""
        try:
            print(f"[KiNotes] set_font_size: Entering with size={size}")
            self._font_size = max(8, min(24, size))
            print(f"[KiNotes] set_font_size: About to call _configure_editor_styles()")
            self._configure_editor_styles()
            print(f"[KiNotes] set_font_size: _configure_editor_styles() completed")
            # Update line numbers panel line height (with safety checks)
            if hasattr(self, '_line_numbers') and self._line_numbers:
                try:
                    print(f"[KiNotes] set_font_size: About to update line height")
                    self._line_numbers._update_line_height()
                    print(f"[KiNotes] set_font_size: Line height updated")
                except Exception as e:
                    print(f"[KiNotes] Line number height update warning: {e}")
                try:
                    print(f"[KiNotes] set_font_size: About to update line numbers from editor")
                    self._line_numbers.update_from_editor()
                    print(f"[KiNotes] set_font_size: Line numbers updated")
                except Exception as e:
                    print(f"[KiNotes] Line number update warning: {e}")
            print(f"[KiNotes] set_font_size: Exiting successfully")
        except Exception as e:
            print(f"[KiNotes] Font size setting warning: {e}")
            import traceback
            traceback.print_exc()
    
    def _bind_events(self):
        """Bind editor events."""
        self._editor.Bind(wx.EVT_TEXT, self._on_text_changed)
        self._editor.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
        self._editor.Bind(wx.EVT_KEY_UP, self._on_key_up)
        self._editor.Bind(wx.EVT_LEFT_UP, self._on_click)
        # Update toolbar button states on selection change
        self._editor.Bind(wx.EVT_SET_FOCUS, self._on_focus_change)
        self._editor.Bind(rt.EVT_RICHTEXT_SELECTION_CHANGED, self._on_selection_changed)
        self._editor.Bind(rt.EVT_RICHTEXT_STYLE_CHANGED, self._on_selection_changed)
    
    def cleanup(self):
        """Clean up resources before destruction."""
        try:
            # Unbind all editor events
            if hasattr(self, '_editor') and self._editor:
                try:
                    self._editor.Unbind(wx.EVT_TEXT)
                    self._editor.Unbind(wx.EVT_KEY_DOWN)
                    self._editor.Unbind(wx.EVT_KEY_UP)
                    self._editor.Unbind(wx.EVT_LEFT_UP)
                    self._editor.Unbind(wx.EVT_SET_FOCUS)
                    self._editor.Unbind(rt.EVT_RICHTEXT_SELECTION_CHANGED)
                    self._editor.Unbind(rt.EVT_RICHTEXT_STYLE_CHANGED)
                except:
                    pass
                # Clear content to release memory
                try:
                    self._editor.Clear()
                except:
                    pass
            
            # Clear references
            self._editor = None
            self._line_numbers = None
            self._toolbar = None
            self._toolbar_buttons = None
            self._designator_linker = None
            self._net_linker = None
            self._debug_logger = None
        except Exception as e:
            print(f"[KiNotes] Visual editor cleanup warning: {e}")
    
    def _ensure_cursor_visible(self):
        """
        Ensure the cursor is visible by scrolling if necessary.
        This provides auto-scroll when cursor moves out of visible area.
        """
        if not self._editor:
            return
        
        try:
            # Use RichTextCtrl's built-in method to show the caret
            self._editor.ShowPosition(self._editor.GetInsertionPoint())
            
            # Update line numbers panel after scroll
            if hasattr(self, '_line_numbers') and self._line_numbers:
                wx.CallAfter(self._line_numbers.update_from_editor)
        except:
            pass
    
    def _on_key_up(self, event):
        """Handle key up - ensure cursor visible after navigation."""
        key = event.GetKeyCode()
        
        # Navigation keys that might move cursor out of view
        nav_keys = [
            wx.WXK_UP, wx.WXK_DOWN, wx.WXK_PAGEUP, wx.WXK_PAGEDOWN,
            wx.WXK_HOME, wx.WXK_END, wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER
        ]
        
        if key in nav_keys:
            # Ensure cursor is visible after navigation
            wx.CallAfter(self._ensure_cursor_visible)
            # Also update line numbers
            if hasattr(self, '_line_numbers') and self._line_numbers:
                wx.CallAfter(self._line_numbers.update_from_editor)
        
        event.Skip()
    
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
        # Use editor's theme text color for headings
        attr = VisualEditorStyles.get_heading_style(level, self._dark_mode, self._text_color)
        
        # Get current paragraph range
        pos = self._editor.GetInsertionPoint()
        line_start = self._editor.XYToPosition(0, self._editor.PositionToXY(pos)[2])
        line_end = line_start
        
        # Find end of line
        text = self._editor.GetValue()
        while line_end < len(text) and text[line_end] != '\n':
            line_end += 1
        
        # Apply BOTH character and paragraph styles
        # First apply character formatting (font size, weight, color)
        self._editor.SetStyleEx(
            rt.RichTextRange(line_start, line_end),
            attr,
            rt.RICHTEXT_SETSTYLE_WITH_UNDO | rt.RICHTEXT_SETSTYLE_CHARACTERS_ONLY
        )
        # Then apply paragraph formatting (spacing)
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
        # Use editor's theme text color for headings
        attr = VisualEditorStyles.get_heading_style(level, self._dark_mode, self._text_color)
        
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
                # Ensure URL has protocol
                if url and not url.startswith(('http://', 'https://', 'mailto:')):
                    url = 'https://' + url
                
                # Get selected text or use URL as text
                selection = self._editor.GetStringSelection()
                link_text = selection if selection else url
                
                if selection:
                    # IMPORTANT: Preserve existing formatting when adding link
                    # Get the current style at selection start
                    sel_range = self._editor.GetSelectionRange()
                    existing_attr = rt.RichTextAttr()
                    self._editor.GetStyle(sel_range.GetStart(), existing_attr)
                    
                    # Modify the existing style to add link properties
                    existing_attr.SetURL(url)
                    existing_attr.SetFontUnderlined(True)
                    # Change color to link blue while preserving bold/italic
                    if self._dark_mode:
                        existing_attr.SetTextColour(wx.Colour(97, 175, 239))  # Light blue
                    else:
                        existing_attr.SetTextColour(wx.Colour(0, 102, 204))  # Standard link blue
                    
                    # Apply the modified style
                    self._editor.SetStyleEx(
                        sel_range,
                        existing_attr,
                        rt.RICHTEXT_SETSTYLE_WITH_UNDO
                    )
                else:
                    # No selection - insert new link text
                    attr = VisualEditorStyles.get_link_style(self._dark_mode)
                    attr.SetURL(url)
                    
                    self._editor.BeginStyle(attr)
                    self._editor.WriteText(link_text)
                    self._editor.EndStyle()
                
                self._modified = True
        
        dlg.Destroy()
    
    def _on_insert_image(self, event):
        """Insert an image."""
        wildcard = "Image files (*.png;*.jpg;*.jpeg;*.gif;*.bmp)|*.png;*.jpg;*.jpeg;*.gif;*.bmp"
        
        # Default to .kinotes/ folder if available
        default_dir = ""
        if hasattr(self, 'project_dir') and self.project_dir:
            kinotes_dir = os.path.join(self.project_dir, '.kinotes')
            if os.path.exists(kinotes_dir):
                default_dir = kinotes_dir
        
        dlg = wx.FileDialog(
            self,
            "Select Image",
            defaultDir=default_dir,
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
        
        # Rows input (including header row)
        row_sizer = wx.BoxSizer(wx.HORIZONTAL)
        row_label = wx.StaticText(dlg, label="Rows:")
        row_label.SetForegroundColour(self._text_color)
        row_label.SetMinSize((scale_size(100, self), -1))
        row_sizer.Add(row_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, scale_size(10, self))
        row_spin = wx.SpinCtrl(dlg, min=2, max=100, initial=4)
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
            # Create header row with "Column 1", "Column 2", etc.
            headers = [f"Column {i+1}" for i in range(cols)]
            self._insert_rich_table(rows, cols, True, headers=headers, row_height=row_height, col_width=col_width)
        
        dlg.Destroy()
    
    def _insert_rich_table(self, rows: int, cols: int, has_header: bool = True, 
                          headers: List[str] = None, data: List[List[str]] = None,
                          row_height: int = None, col_width: int = None):
        """
        Insert a proper RichTextTable with styling and borders.
        
        Args:
            rows: Number of rows (including header if has_header)
            cols: Number of columns
            has_header: Whether first row is header
            headers: Optional header text list
            data: Optional data rows list
            row_height: Optional row height in pixels (default: 30)
            col_width: Optional column width in pixels (default: auto-calculated)
        """
        # Ensure we're at end of line
        pos = self._editor.GetInsertionPoint()
        text = self._editor.GetValue()
        if pos > 0 and len(text) > 0 and text[pos - 1] != '\n':
            self._editor.WriteText("\n")
        
        # Default column width - auto-calculate based on editor width
        if col_width is None:
            editor_width = self._editor.GetClientSize().GetWidth() - 60
            col_width = max(80, min(200, editor_width // cols))
        
        # Default row height
        if row_height is None:
            row_height = 30
        
        # Set border color based on theme
        if self._dark_mode:
            border_color = wx.Colour(100, 100, 100)  # Gray border for dark mode
        else:
            border_color = wx.Colour(180, 180, 180)  # Light gray for light mode
        
        # Create table attributes with proper column widths
        table_attr = rt.RichTextAttr()
        try:
            # Set up text box attributes for the table
            text_box_attr = table_attr.GetTextBoxAttr()
            
            # Set table width to total of all columns
            total_width = col_width * cols
            text_box_attr.GetWidth().SetValue(total_width, rt.TEXT_ATTR_UNITS_PIXELS)
            
            # Set border
            text_box_attr.GetBorder().SetColour(border_color)
            text_box_attr.GetBorder().SetWidth(1, rt.TEXT_ATTR_UNITS_PIXELS)
            text_box_attr.GetBorder().SetStyle(wx.BORDER_SIMPLE)
        except Exception as e:
            pass  # Table attribute API may vary
        
        # Create the table with attributes
        table = self._editor.WriteTable(rows, cols, table_attr)
        
        if table is None:
            # Table creation failed - raise exception to trigger fallback
            raise Exception("WriteTable returned None - rich table not supported")
        
        # Set cell properties (width, height, border) without writing text
        # Writing text into cells with SetCaretPosition causes crashes in KiCad
        for row_idx in range(rows):
            for col_idx in range(cols):
                cell = table.GetCell(row_idx, col_idx)
                if cell:
                    try:
                        cell_props = cell.GetProperties()
                        cell_box = cell_props.GetTextBoxAttr()
                        
                        # Set cell width
                        cell_box.GetWidth().SetValue(col_width, rt.TEXT_ATTR_UNITS_PIXELS)
                        
                        # Set cell height
                        cell_box.GetHeight().SetValue(row_height, rt.TEXT_ATTR_UNITS_PIXELS)
                        
                        # Set cell padding
                        cell_box.GetPadding().Set(5, rt.TEXT_ATTR_UNITS_PIXELS)
                        
                        # Set cell border
                        cell_box.GetBorder().SetColour(border_color)
                        cell_box.GetBorder().SetWidth(1, rt.TEXT_ATTR_UNITS_PIXELS)
                        cell_box.GetBorder().SetStyle(wx.BORDER_SIMPLE)
                        
                        cell.SetProperties(cell_props)
                    except Exception as e:
                        pass  # Cell properties API may vary
        
        # Move cursor to end of document after table insertion
        self._editor.MoveEnd()
        self._editor.WriteText("\n\n")
        self._modified = True
        self._editor.WriteText("\n\n")
        self._modified = True
    
    def insert_data_table(self, headers: List[str], data: List[List[str]], title: str = None):
        """
        Public method to insert a formatted data table (for BOM, metadata, etc.)
        Uses ASCII table format for reliable cross-platform rendering.
        
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
        
        # Always use ASCII table for reliable rendering
        # RichTextTable has issues with cell positioning in KiCad's wxPython
        if headers:
            self._insert_ascii_table(headers, data if data else [])
        
        self._modified = True
    
    def insert_markdown_as_formatted(self, markdown_text: str):
        """
        Parse markdown text and insert as properly formatted rich text.
        Handles tables, headings, lists, inline bold/italic, etc.
        
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
                    self._editor.WriteText("• ")
                    self._write_inline_formatted_text(text)
                    self._editor.WriteText("\n")
                    i += 1
                    continue
            
            # Regular text with possible inline formatting
            if line.strip():
                self._write_inline_formatted_text(line)
                self._editor.WriteText("\n")
            else:
                self._editor.WriteText("\n")
            i += 1
        
        self._modified = True
    
    def _write_inline_formatted_text(self, text: str):
        """
        Write text with inline markdown formatting (bold, italic).
        Handles **bold**, *italic*, and ***bold italic***.
        """
        # Pattern to match **bold**, *italic*, or ***bold italic***
        # Process from left to right, handling nested formatting
        pattern = r'(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*)'
        
        last_end = 0
        for match in re.finditer(pattern, text):
            # Write any text before this match as normal
            if match.start() > last_end:
                self._editor.WriteText(text[last_end:match.start()])
            
            full_match = match.group(0)
            
            # Determine formatting type
            if full_match.startswith('***'):
                # Bold italic
                content = match.group(2)
                attr = rt.RichTextAttr()
                attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
                attr.SetFontStyle(wx.FONTSTYLE_ITALIC)
                self._editor.BeginStyle(attr)
                self._editor.WriteText(content)
                self._editor.EndStyle()
            elif full_match.startswith('**'):
                # Bold
                content = match.group(3)
                attr = rt.RichTextAttr()
                attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
                self._editor.BeginStyle(attr)
                self._editor.WriteText(content)
                self._editor.EndStyle()
            elif full_match.startswith('*'):
                # Italic
                content = match.group(4)
                attr = rt.RichTextAttr()
                attr.SetFontStyle(wx.FONTSTYLE_ITALIC)
                self._editor.BeginStyle(attr)
                self._editor.WriteText(content)
                self._editor.EndStyle()
            
            last_end = match.end()
        
        # Write any remaining text after the last match
        if last_end < len(text):
            self._editor.WriteText(text[last_end:])
    
    def _parse_and_insert_markdown_table(self, table_lines: List[str]):
        """Parse markdown table lines and insert as RichTextTable."""
        if len(table_lines) < 2:
            return
        
        # Parse headers (first line)
        header_line = table_lines[0]
        headers = [cell.strip() for cell in header_line.strip('|').split('|')]
        headers = [h for h in headers if h]  # Remove empty strings
        
        if not headers:
            return
        
        # Skip separator line (second line with ---)
        # Parse data rows
        data = []
        for line in table_lines[2:]:
            if '---' in line or not line.strip():
                continue
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            cells = [c for c in cells if c]  # Remove empty strings
            if cells:
                # Ensure row has same number of columns as headers
                while len(cells) < len(headers):
                    cells.append("")
                data.append(cells[:len(headers)])  # Trim to header count
        
        # Try to insert as rich table, fallback to ASCII table if it fails
        if headers and data:
            try:
                self.insert_data_table(headers, data)
            except Exception as e:
                # Fallback: Insert as formatted ASCII table
                self._insert_ascii_table(headers, data)
        elif headers:
            # No data rows - just show headers
            self._insert_ascii_table(headers, [])
    
    def _insert_ascii_table(self, headers: List[str], data: List[List[str]]):
        """Insert table as formatted ASCII text with proper alignment."""
        if not headers:
            return
        
        # Ensure newline before table
        pos = self._editor.GetInsertionPoint()
        text = self._editor.GetValue()
        if pos > 0 and len(text) > 0 and text[pos - 1] != '\n':
            self._editor.WriteText("\n")
        
        # Calculate column widths (min 8 chars for readability)
        col_widths = [max(8, len(str(h))) for h in headers]
        for row in data:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Cap max width to prevent overly wide columns
        col_widths = [min(w, 40) for w in col_widths]
        
        # Insert header row with bold
        self._editor.BeginBold()
        header_cells = []
        for i, h in enumerate(headers):
            if i < len(col_widths):
                header_cells.append(str(h)[:col_widths[i]].ljust(col_widths[i]))
        self._editor.WriteText(" │ ".join(header_cells) + "\n")
        self._editor.EndBold()
        
        # Insert separator line
        separator_parts = ["─" * w for w in col_widths]
        self._editor.WriteText("─┼─".join(separator_parts) + "\n")
        
        # Insert data rows
        for row in data:
            cells_padded = []
            for i in range(len(headers)):
                if i < len(row):
                    cell_text = str(row[i])[:col_widths[i]]  # Truncate if needed
                else:
                    cell_text = ""
                cells_padded.append(cell_text.ljust(col_widths[i]))
            self._editor.WriteText(" │ ".join(cells_padded) + "\n")
        
        # Add empty line after table
        self._editor.WriteText("\n")
    
    def _on_undo(self, event):
        """Undo last action."""
        self._editor.Undo()
    
    def _on_redo(self, event):
        """Redo last undone action."""
        self._editor.Redo()
    
    def _on_clear_format(self, event):
        """Clear all formatting from selection or current paragraph."""
        # Use theme-aware normal style
        normal_attr = self._get_normal_style_with_theme()
        
        if self._editor.HasSelection():
            # Clear formatting on selection
            self._editor.SetStyleEx(
                self._editor.GetSelectionRange(),
                normal_attr,
                rt.RICHTEXT_SETSTYLE_WITH_UNDO
            )
        else:
            # Clear formatting on current paragraph (if has text)
            self._clear_current_paragraph_format()
        
        # Always reset default style for future typing - uses theme colors
        self._editor.SetDefaultStyle(normal_attr)
        
        # Also set basic style to ensure new text uses theme colors
        self._editor.SetBasicStyle(normal_attr)
        
        self._modified = True
        self._update_toolbar_states()
    
    def _clear_current_paragraph_format(self):
        """Clear formatting on the current paragraph/line."""
        # Use theme-aware normal style
        normal_attr = self._get_normal_style_with_theme()
        
        pos = self._editor.GetInsertionPoint()
        text = self._editor.GetValue()
        
        # Find paragraph boundaries
        line_start = text.rfind('\n', 0, pos) + 1
        line_end = text.find('\n', pos)
        if line_end == -1:
            line_end = len(text)
        
        # Apply normal style to paragraph if it has content
        if line_end > line_start:
            self._editor.SetStyleEx(
                rt.RichTextRange(line_start, line_end),
                normal_attr,
                rt.RICHTEXT_SETSTYLE_WITH_UNDO
            )
        
        # Always set default style for future typing
        self._editor.SetDefaultStyle(normal_attr)
    
    # ============================================================
    # EVENT HANDLERS
    # ============================================================
    
    def _on_text_changed(self, event):
        """Handle text changes."""
        self._modified = True
        # Ensure cursor stays visible when typing
        wx.CallAfter(self._ensure_cursor_visible)
        # Update line numbers panel
        if hasattr(self, '_line_numbers') and self._line_numbers:
            wx.CallAfter(self._line_numbers.update_from_editor)
        event.Skip()
    
    def _on_key_down(self, event):
        """Handle keyboard shortcuts."""
        key = event.GetKeyCode()
        ctrl = event.ControlDown()
        shift = event.ShiftDown()
        alt = event.AltDown()
        
        # ESC key - clear formatting and reset to normal text
        if key == wx.WXK_ESCAPE:
            # Clear any selection
            if self._editor.HasSelection():
                sel_end = self._editor.GetSelectionRange().GetEnd()
                self._editor.SetInsertionPoint(sel_end)
                self._editor.SelectNone()
            
            # Use theme-aware normal style
            normal_attr = self._get_normal_style_with_theme()
            
            # Reset default and basic style to use theme colors
            self._editor.SetDefaultStyle(normal_attr)
            self._editor.SetBasicStyle(normal_attr)
            
            # Also clear formatting on current paragraph if has text
            self._clear_current_paragraph_format()
            
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
        """Handle Enter key - new line with normal text style."""
        pos = self._editor.GetInsertionPoint()
        text = self._editor.GetValue()
        
        # Find start of current line
        line_start = text.rfind('\n', 0, pos) + 1
        current_line = text[line_start:pos]
        
        # Check for list prefixes to continue them
        bullet_match = re.match(r'^([•◦▪]\s)', current_line)
        number_match = re.match(r'^(\d+)\.\s', current_line)
        checkbox_match = re.match(r'^([☐☑]\s)', current_line)
        
        # Get theme-aware normal style for the new line
        normal_attr = self._get_normal_style_with_theme()
        
        if bullet_match:
            # Continue bullet list but check if line is empty (just bullet)
            line_content = current_line[len(bullet_match.group(1)):].strip()
            if not line_content:
                # Empty bullet - end list, insert normal newline
                self._editor.WriteText('\n')
            else:
                self._editor.WriteText('\n• ')
        elif number_match:
            # Continue numbered list but check if line is empty
            line_content = current_line[len(number_match.group(0)):].strip()
            if not line_content:
                # Empty number - end list
                self._editor.WriteText('\n')
            else:
                next_num = int(number_match.group(1)) + 1
                self._editor.WriteText(f'\n{next_num}. ')
        elif checkbox_match:
            # Continue checkbox list but check if line is empty
            line_content = current_line[len(checkbox_match.group(1)):].strip()
            if not line_content:
                # Empty checkbox - end list
                self._editor.WriteText('\n')
            else:
                self._editor.WriteText('\n☐ ')
        else:
            # Normal enter - insert newline
            self._editor.WriteText('\n')
        
        # Reset to theme-aware normal style for the new line
        self._editor.SetDefaultStyle(normal_attr)
        self._modified = True
    
    def _on_click(self, event):
        """Handle mouse clicks - toggle checkboxes, open links, cross-probe designators/nets, update toolbar states."""
        # Use cursor position after click (original working logic)
        click_pos = self._editor.GetInsertionPoint()
        text = self._editor.GetValue()
        
        _kinotes_log(f"[KiNotes Click] Click position: {click_pos}, Text length: {len(text)}")
        
        # Check for link at click position - Ctrl+Click or just Click to open
        try:
            attr = rt.RichTextAttr()
            if self._editor.GetStyle(click_pos, attr):
                url = attr.GetURL()
                if url:
                    _kinotes_log(f"[KiNotes Click] Found link URL: {url}")
                    import webbrowser
                    webbrowser.open(url)
                    event.Skip()
                    return
        except Exception as e:
            _kinotes_log(f"[KiNotes Click] Error checking for link: {e}")
        
        # Only check for checkbox if there's actual text and position is valid
        if text and click_pos > 0 and click_pos <= len(text):
            # Get character at click position (pos-1 since pos is after character)
            char = text[click_pos - 1] if click_pos > 0 else ''
            
            _kinotes_log(f"[KiNotes Click] Char at pos-1: '{char}'")
            
            # Only toggle if we clicked directly on a checkbox character
            # This prevents accidental checkbox insertion on empty lines or double-clicks
            if char in '☐☑':
                check_pos = click_pos - 1
                current_char = text[check_pos]
                new_char = '☑' if current_char == '☐' else '☐'
                
                # Replace the checkbox character
                self._editor.SetSelection(check_pos, check_pos + 1)
                self._editor.WriteText(new_char)
                self._modified = True
                _kinotes_log(f"[KiNotes Click] Toggled checkbox")
            else:
                # Check for net highlighting first: [[NET:name]] pattern (Beta)
                if self._crossprobe_enabled:
                    self._log_debug("net", EventLevel.DEBUG, f"[KiNotes Click] Crossprobe enabled, checking for nets...")
                    net_info = self._get_net_at_click_with_pos(click_pos)
                    if net_info:
                        net_name, start_pos, end_pos = net_info
                        self._log_debug("net", EventLevel.INFO, f"[KiNotes Click] Found net: {net_name}")
                        self._try_net_highlight_with_style(net_name, start_pos, end_pos)
                    else:
                        self._log_debug("net", EventLevel.DEBUG, f"[KiNotes Click] No net found, checking designators...")
                        # Fall back to cross-probe on designators (R1, C5, U3, etc.)
                        word_info = self._get_designator_at_click_with_pos(click_pos)
                        if word_info:
                            designator, start_pos, end_pos = word_info
                            self._log_debug("designator", EventLevel.INFO, f"[KiNotes Click] Found designator: {designator}")
                            self._try_crossprobe_with_style(designator, start_pos, end_pos)
                        else:
                            self._log_debug("designator", EventLevel.DEBUG, f"[KiNotes Click] No designator found either")
                else:
                    self._log_debug("designator", EventLevel.DEBUG, f"[KiNotes Click] Crossprobe disabled")
        else:
            _kinotes_log(f"[KiNotes Click] Invalid position or no text")
        
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
        # Pass theme colors to converter for proper heading/text coloring
        converter = MarkdownToRichText(
            self._editor, 
            self._dark_mode, 
            text_color=self._text_color,
            bg_color=self._bg_color
        )
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
    
    # ============================================================
    # CROSS-PROBE API
    # ============================================================
    
    def set_crossprobe_enabled(self, enabled: bool):
        """Enable or disable cross-probe functionality."""
        self._crossprobe_enabled = enabled
    
    def set_designator_linker(self, linker):
        """Set the designator linker for cross-probe functionality."""
        self._designator_linker = linker
    
    def set_net_linker(self, linker):
        """Set the net linker for net highlighting (Beta)."""
        self._net_linker = linker
        if linker:
            print("[KiNotes] Visual editor received net linker")
            self._log_debug("net", EventLevel.INFO, "[KiNotes] Visual editor received net linker")
        else:
            print("[KiNotes] Visual editor cleared net linker")

    def set_debug_logging(self, logger, modules: dict):
        """Attach debug logger and module filters."""
        self._debug_logger = logger
        self._debug_modules = modules or {}
        for key in ("net", "designator"):
            if key not in self._debug_modules:
                self._debug_modules[key] = False

    def _log_debug(self, module: str, level: EventLevel, message: str):
        """Log to console and optional debug panel if module enabled."""
        _kinotes_log(message)
        try:
            if self._debug_logger and self._debug_modules.get(module, False):
                self._debug_logger.log(level, message)
        except Exception:
            pass
    
    def _get_word_at_position(self, pos: int) -> Tuple[str, int, int]:
        """
        Get the word at the given position.
        Returns (word, start_pos, end_pos).
        Supports alphanumeric + underscore + hyphen for designators.
        """
        text = self._editor.GetValue()
        if not text or pos < 0 or pos > len(text):
            return ("", pos, pos)
        
        # Find word boundaries
        start = pos
        end = pos
        
        # Scan backward to find word start
        while start > 0 and (text[start - 1].isalnum() or text[start - 1] in '_-'):
            start -= 1
        
        # Scan forward to find word end
        while end < len(text) and (text[end].isalnum() or text[end] in '_-'):
            end += 1
        
        return (text[start:end], start, end)

    def _get_net_word_at_position(self, pos: int) -> Tuple[str, int, int]:
        """
        Get a net name at the given position (more permissive than regular word).
        Supports net chars: alphanumeric + underscore + hyphen + plus.
        Returns (net_name, start_pos, end_pos).
        """
        text = self._editor.GetValue()
        if not text or pos < 0 or pos > len(text):
            return ("", pos, pos)
        
        # Find word boundaries (net chars include +, -, _, alnum)
        start = pos
        end = pos
        
        # Scan backward to find net start
        while start > 0 and (text[start - 1].isalnum() or text[start - 1] in '_-+'):
            start -= 1
        
        # Scan forward to find net end
        while end < len(text) and (text[end].isalnum() or text[end] in '_-+'):
            end += 1
        
        return (text[start:end], start, end)
    
    def _check_for_designator_at_click(self, pos: int) -> Optional[str]:
        """
        Check if click position is on a valid designator.
        Returns the designator string or None.
        """
        if not self._crossprobe_enabled or not self._designator_linker:
            return None
        
        word, start, end = self._get_word_at_position(pos)
        if not word:
            return None
        
        # Check if it matches a designator pattern
        word_upper = word.upper()
        
        # Use the smart pattern from designator linker
        import re
        # Standard EE designator prefixes
        prefixes = ['R', 'C', 'L', 'D', 'U', 'Q', 'J', 'P', 'K', 'SW', 'S', 'F', 'FB', 
                   'TP', 'Y', 'X', 'T', 'M', 'LED', 'IC', 'CON', 'RLY', 'XTAL', 'ANT', 
                   'BT', 'VR', 'RV', 'TR', 'FID', 'MH', 'JP', 'LS', 'SP', 'MIC']
        
        pattern = re.compile(
            r'^(' + '|'.join(sorted(prefixes, key=len, reverse=True)) + r')(\d+[A-Z]?)$',
            re.IGNORECASE
        )
        
        if pattern.match(word_upper):
            return word_upper
        
        return None
    
    def _ensure_net_linker(self):
        """Lazy-load net linker from cache manager on demand (inside KiCad only)."""
        if self._net_linker:
            return  # Already have one
        # Try to get linker from cache manager (use absolute import to avoid relative import issues)
        try:
            from KiNotes.core.net_cache_manager import get_net_cache_manager
            cache_manager = get_net_cache_manager()
            self._net_linker = cache_manager.get_linker()
            if self._net_linker:
                print("[KiNotes] Net linker acquired from cache manager")
            else:
                print("[KiNotes] Net linker is None from cache manager (no board?)")
        except ImportError as e:
            print(f"[KiNotes] Net linker lazy-load import error: {e}")
            # Fallback: try parent chain
            try:
                parent = self.GetParent()
                while parent:
                    if hasattr(parent, 'net_cache_manager') and parent.net_cache_manager:
                        self._net_linker = parent.net_cache_manager.get_linker()
                        if self._net_linker:
                            print("[KiNotes] Net linker acquired from parent's cache manager (fallback)")
                            return
                    parent = parent.GetParent()
            except Exception as e2:
                print(f"[KiNotes] Net linker fallback warning: {e2}")
        except Exception as e:
            print(f"[KiNotes] Net linker lazy-load error: {e}")

    def _get_net_at_click_with_pos(self, pos: int) -> Optional[Tuple[str, int, int]]:
        """
        Check if click position is on a net reference.
        Returns (net_name, start_pos, end_pos) or None.
        
        Supports multiple syntaxes:
        - [[NET:VCC]]    (explicit, no false positives)
        - @VCC           (short form, like designators use @R1)
        - VCC            (implicit, if VCC is a known net in the cache)
        """
        # Lazy-load net linker on first click
        self._ensure_net_linker()
        if not self._net_linker:
            self._log_debug("net", EventLevel.DEBUG, "[KiNotes Net Detection] No net_linker available (KiCad board not found)")
            return None
        
        text = self._editor.GetValue()
        if not text or pos < 0 or pos > len(text):
            self._log_debug("net", EventLevel.DEBUG, f"[KiNotes Net Detection] Invalid position: {pos}, text length: {len(text)}")
            return None
        
        self._log_debug("net", EventLevel.DEBUG, f"[KiNotes Net Detection] Searching around position {pos}")
        
        search_start = max(0, pos - 50)
        search_text = text[search_start:pos + 50]
        
        self._log_debug("net", EventLevel.DEBUG, f"[KiNotes Net Detection] Search snippet: '{search_text}'")
        
        import re
        
        # Try explicit syntax first: [[NET:NETNAME]] (supports special chars like +3V3, AC_N)
        pattern_explicit = r'\[\[NET:([A-Za-z0-9_+\-]+)\]\]'
        for match in re.finditer(pattern_explicit, search_text):
            match_start = search_start + match.start()
            match_end = search_start + match.end()
            if match_start <= pos < match_end:
                net_name = match.group(1)
                self._log_debug("net", EventLevel.INFO, f"[KiNotes Net Detection] ✓ Found explicit pattern: {net_name}")
                return (net_name, match_start, match_end)
        
        # Try short form: @NETNAME (supports special chars like +3V3, AC_N)
        pattern_short = r'@([A-Za-z0-9_+\-]+)'
        for match in re.finditer(pattern_short, search_text):
            match_start = search_start + match.start()
            match_end = search_start + match.end()
            if match_start <= pos < match_end:
                net_name = match.group(1)
                self._log_debug("net", EventLevel.INFO, f"[KiNotes Net Detection] ✓ Found short form: {net_name}")
                return (net_name, match_start, match_end)
        
        # Try implicit: bare word if it's a known net (get from net_linker cache)
        # Use net-specific word extraction to handle nets like +3V3, AC_N, etc.
        word, start, end = self._get_net_word_at_position(pos)
        self._log_debug("net", EventLevel.DEBUG, f"[KiNotes Net Detection] Extracted net word: '{word}'")
        
        # CHEAT CODE: Blank extraction = clear highlight signal
        # (User clicked on empty/whitespace → clear any active highlight on PCB board)
        if word == '':
            self._log_debug("net", EventLevel.INFO, f"[KiNotes Net Detection] Blank extraction → clearing PCB board highlights")
            if hasattr(self._net_linker, 'clear_highlight'):
                self._net_linker.clear_highlight()
            return None  # Signal no net found
        
        if word and hasattr(self._net_linker, 'is_valid_net'):
            is_valid = self._net_linker.is_valid_net(word.upper())
            self._log_debug("net", EventLevel.DEBUG, f"[KiNotes Net Detection] Is '{word}' valid net? {is_valid}")
            if is_valid:
                self._log_debug("net", EventLevel.INFO, f"[KiNotes Net Detection] ✓ Found implicit net: {word}")
                return (word.upper(), start, end)
        
        self._log_debug("net", EventLevel.DEBUG, f"[KiNotes Net Detection] ✗ No net pattern found")
        return None
    
    def _get_designator_at_click_with_pos(self, pos: int) -> Optional[Tuple[str, int, int]]:
        """
        Check if click position is on a valid designator.
        Returns (designator, start_pos, end_pos) or None.
        Uses the designator_linker's pattern which includes custom prefixes.
        """
        if not self._crossprobe_enabled or not self._designator_linker:
            return None
        
        word, start, end = self._get_word_at_position(pos)
        if not word:
            return None
        
        # Use the designator linker's pattern (includes custom prefixes from settings)
        word_upper = word.upper()
        
        # Check using the linker's SMART_DESIGNATOR_PATTERN which has custom prefixes
        if hasattr(self._designator_linker, 'SMART_DESIGNATOR_PATTERN'):
            if self._designator_linker.SMART_DESIGNATOR_PATTERN.match(word):
                self._log_debug("designator", EventLevel.DEBUG, f"[KiNotes] Matched designator: {word_upper}")
                return (word_upper, start, end)
        
        # Fallback: check using DESIGNATOR_PATTERN for generic validation
        if hasattr(self._designator_linker, 'DESIGNATOR_PATTERN'):
            if self._designator_linker.DESIGNATOR_PATTERN.match(word):
                return (word_upper, start, end)
        
        return None
    
    def _try_crossprobe_with_style(self, designator: str, start_pos: int, end_pos: int) -> bool:
        """
        Attempt to cross-probe and apply visual styling to the designator text.
        Green bold = found on board, Red bold = not found.
        """
        self._log_debug("designator", EventLevel.INFO, f"[KiNotes Cross-Probe] Attempting to highlight: {designator}")
        
        if not self._crossprobe_enabled:
            self._log_debug("designator", EventLevel.DEBUG, "[KiNotes Cross-Probe] Cross-probe is disabled in settings")
            return False
        
        if not self._designator_linker:
            self._log_debug("designator", EventLevel.ERROR, "[KiNotes Cross-Probe] No designator linker available")
            return False
        
        try:
            result = self._designator_linker.highlight(designator)
            
            # Apply visual styling to the designator text
            self._apply_crossprobe_style(start_pos, end_pos, success=result)
            
            if result:
                self._log_debug("designator", EventLevel.SUCCESS, f"[KiNotes Cross-Probe] Successfully highlighted {designator}")
                
                # === MERGED TOOLTIP: Show component info ===
                tooltip_text = self._get_component_tooltip(designator)
                self._editor.SetToolTip(tooltip_text)
            else:
                self._log_debug("designator", EventLevel.WARNING, f"[KiNotes Cross-Probe] Component {designator} not found on board")
                self._editor.SetToolTip(f"✗ {designator} not found on board")
            
            # Clear tooltip after 3 seconds (longer for reading component info)
            wx.CallLater(3000, lambda: self._editor.SetToolTip(""))
            return result
            
        except Exception as e:
            self._log_debug("designator", EventLevel.ERROR, f"[KiNotes Cross-Probe] Error: {e}")
            return False
    
    def _get_component_tooltip(self, designator: str) -> str:
        """
        Build component tooltip with info from ComponentTooltipProvider.
        Shows: Reference, Value, MPN, Footprint, Type, Layer
        """
        try:
            from core.component_tooltip import ComponentTooltipProvider
            
            tooltip = ComponentTooltipProvider()
            info = tooltip.get_component_info(designator)
            
            if info:
                # Build multi-line tooltip
                lines = [f"✓ {info.reference} selected"]
                
                if info.value and str(info.value) != "~":
                    lines.append(f"Value: {info.value}")
                
                # Show MPN if available (always labeled as MPN:)
                if info.mpn:
                    lines.append(f"MPN: {info.mpn}")
                
                if info.footprint:
                    # Show just the footprint name, not full library path
                    # Convert to str first (KiCad returns UTF8 object)
                    fp_str = str(info.footprint)
                    fp_name = fp_str.split(':')[-1] if ':' in fp_str else fp_str
                    lines.append(f"Footprint: {fp_name}")
                
                if info.component_type:
                    lines.append(f"Type: {info.component_type.value}")
                
                if info.layer:
                    lines.append(f"Layer: {info.layer}")
                
                return "\n".join(lines)
            else:
                return f"✓ {designator} selected on PCB"
                
        except Exception as e:
            # Fallback to simple tooltip if component info fails
            _kinotes_log(f"[KiNotes Tooltip] Error getting component info: {e}")
            return f"✓ {designator} selected on PCB"
    
    def _apply_crossprobe_style(self, start_pos: int, end_pos: int, success: bool):
        """Apply Bold + Color styling to designator based on cross-probe result."""
        try:
            attr = rt.RichTextAttr()
            
            # Set bold
            attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
            
            # Set color based on result
            if success:
                # Green for found
                attr.SetTextColour(wx.Colour(76, 175, 80))  # Material Green 500
            else:
                # Red for not found  
                attr.SetTextColour(wx.Colour(244, 67, 54))  # Material Red 500
            
            # Apply style to the designator text
            text_range = rt.RichTextRange(start_pos, end_pos)
            self._editor.SetStyleEx(text_range, attr, rt.RICHTEXT_SETSTYLE_WITH_UNDO)
            
            # Flash effect - briefly make it brighter, then settle
            wx.CallLater(150, lambda: self._flash_designator(start_pos, end_pos, success))
            
        except Exception as e:
            _kinotes_log(f"[KiNotes Cross-Probe] Style error: {e}")
    
    def _flash_designator(self, start_pos: int, end_pos: int, success: bool):
        """Apply final settled style after flash."""
        try:
            attr = rt.RichTextAttr()
            attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
            
            if success:
                # Settled green
                attr.SetTextColour(wx.Colour(56, 142, 60))  # Darker green
            else:
                # Settled red
                attr.SetTextColour(wx.Colour(211, 47, 47))  # Darker red
            
            text_range = rt.RichTextRange(start_pos, end_pos)
            self._editor.SetStyleEx(text_range, attr, rt.RICHTEXT_SETSTYLE_WITH_UNDO)
        except:
            pass

    def _try_net_highlight_with_style(self, net_name: str, start_pos: int, end_pos: int) -> bool:
        """
        Attempt to highlight net by name and apply visual styling.
        Blue bold = successfully highlighted, Gray bold = not found (Beta feature).
        """
        self._log_debug("net", EventLevel.INFO, f"[KiNotes Net Linker] Attempting to highlight net: {net_name} (Beta)")
        
        if not self._net_linker:
            self._log_debug("net", EventLevel.ERROR, "[KiNotes Net Linker] No net linker available (Beta feature may be disabled)")
            return False
        
        try:
            result = self._net_linker.highlight(net_name)
            
            # Apply visual styling to the net pattern
            self._apply_net_style(start_pos, end_pos, success=result)
            
            if result:
                self._log_debug("net", EventLevel.SUCCESS, f"[KiNotes Net Linker] Successfully highlighted net {net_name}")
                self._editor.SetToolTip(f"✓ Net {net_name} highlighted on PCB")
            else:
                self._log_debug("net", EventLevel.WARNING, f"[KiNotes Net Linker] Net {net_name} not found on board")
                self._editor.SetToolTip(f"✗ Net {net_name} not found on board")
            
            # Clear tooltip after 2 seconds
            wx.CallLater(2000, lambda: self._editor.SetToolTip(""))
            return result
            
        except Exception as e:
            self._log_debug("net", EventLevel.ERROR, f"[KiNotes Net Linker] Error: {e}")
            return False
    
    def _apply_net_style(self, start_pos: int, end_pos: int, success: bool):
        """Apply Bold + Color styling to net pattern based on highlighting result."""
        try:
            attr = rt.RichTextAttr()
            
            # Set bold
            attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
            
            # Set color based on result (use blue for success, gray for not found)
            if success:
                # Blue for successfully highlighted
                attr.SetTextColour(wx.Colour(33, 150, 243))  # Material Blue 500
            else:
                # Gray for not found
                attr.SetTextColour(wx.Colour(158, 158, 158))  # Material Gray 500
            
            # Apply style to the net pattern text
            text_range = rt.RichTextRange(start_pos, end_pos)
            self._editor.SetStyleEx(text_range, attr, rt.RICHTEXT_SETSTYLE_WITH_UNDO)
            
            # Flash effect
            wx.CallLater(150, lambda: self._flash_net(start_pos, end_pos, success))
            
        except Exception as e:
            _kinotes_log(f"[KiNotes Net Linker] Style error: {e}")
    
    def _flash_net(self, start_pos: int, end_pos: int, success: bool):
        """Apply final settled style to net pattern after flash."""
        try:
            attr = rt.RichTextAttr()
            attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
            
            if success:
                # Settled blue (darker)
                attr.SetTextColour(wx.Colour(13, 71, 161))  # Material Blue 900
            else:
                # Settled gray (darker)
                attr.SetTextColour(wx.Colour(97, 97, 97))  # Material Gray 700
            
            text_range = rt.RichTextRange(start_pos, end_pos)
            self._editor.SetStyleEx(text_range, attr, rt.RICHTEXT_SETSTYLE_WITH_UNDO)
        except:
            pass

    def _try_crossprobe(self, designator: str) -> bool:
        """
        Attempt to cross-probe (highlight on PCB) the given designator.
        Returns True if successful.
        """
        _kinotes_log(f"[KiNotes Cross-Probe] Attempting to highlight: {designator}")
        
        if not self._crossprobe_enabled:
            _kinotes_log("[KiNotes Cross-Probe] Cross-probe is disabled in settings")
            return False
        
        if not self._designator_linker:
            _kinotes_log("[KiNotes Cross-Probe] No designator linker available")
            return False
        
        linker_type = type(self._designator_linker).__name__
        _kinotes_log(f"[KiNotes Cross-Probe] Using linker: {linker_type}")
        
        try:
            result = self._designator_linker.highlight(designator)
            if result:
                # Show visual feedback
                self._show_crossprobe_feedback(designator, success=True)
                _kinotes_log(f"[KiNotes Cross-Probe] Successfully highlighted {designator}")
            else:
                self._show_crossprobe_feedback(designator, success=False)
                _kinotes_log(f"[KiNotes Cross-Probe] Component {designator} not found on board")
            return result
        except Exception as e:
            _kinotes_log(f"[KiNotes Cross-Probe] Error: {e}")
            return False
    
    def _show_crossprobe_feedback(self, designator: str, success: bool):
        """Show visual feedback for cross-probe action."""
        if success:
            # Brief tooltip or status indication
            try:
                wx.ToolTip.Enable(True)
                self._editor.SetToolTip(f"✓ Highlighted {designator} on PCB")
                # Clear tooltip after 2 seconds
                wx.CallLater(2000, lambda: self._editor.SetToolTip(""))
            except:
                pass
        else:
            try:
                self._editor.SetToolTip(f"✗ {designator} not found on board")
                wx.CallLater(2000, lambda: self._editor.SetToolTip(""))
            except:
                pass
