"""
KiNotes Markdown Editor - Plain Text Markdown Editor for KiCad 9+
========================================================================
A plain text markdown editor using wx.TextCtrl for power users who prefer
direct markdown editing. Provides:
- Formatting toolbar (Bold, Italic, Underline, Headings, Lists)
- Auto list continuation
- Keyboard shortcuts
- @REF designator click-to-highlight

This is the fallback/power-user alternative to the Visual Editor.

Author: KiNotes Team (pcbtools.xyz)
License: MIT
"""
import wx
import re
from datetime import datetime
from typing import Optional, Callable

# Handle imports for both KiCad plugin context and standalone
try:
    from .themes import hex_to_colour, DARK_THEME, LIGHT_THEME
    from ..core.defaultsConfig import EDITOR_LAYOUT
except ImportError:
    try:
        from themes import hex_to_colour, DARK_THEME, LIGHT_THEME
        from core.defaultsConfig import EDITOR_LAYOUT
    except ImportError:
        # Standalone fallback - define minimal required values
        def hex_to_colour(hex_str):
            """Convert hex color string to wx.Colour."""
            hex_str = hex_str.lstrip('#')
            r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
            return wx.Colour(r, g, b)
        
        DARK_THEME = {
            "bg_editor": "#1C1C1E",
            "bg_toolbar": "#2C2C2E", 
            "text_primary": "#FFFFFF",
            "text_secondary": "#8E8E93",
        }
        LIGHT_THEME = {
            "bg_editor": "#FFFFFF",
            "bg_toolbar": "#F2F2F7",
            "text_primary": "#1C1C1E",
            "text_secondary": "#8E8E93",
        }
        EDITOR_LAYOUT = {'margin_left': 12, 'margin_right': 8, 'padding_horizontal': 4, 'padding_bottom': 4}


class MarkdownEditor(wx.Panel):
    """
    Plain text Markdown editor with formatting toolbar.
    
    Provides a power-user interface for direct markdown editing with
    toolbar buttons and keyboard shortcuts for common formatting.
    """
    
    def __init__(
        self,
        parent,
        dark_mode: bool = False,
        bg_color: wx.Colour = None,
        text_color: wx.Colour = None,
        designator_linker = None,
        on_text_changed: Callable = None,
    ):
        """
        Initialize the Markdown Editor.
        
        Args:
            parent: Parent wx window
            dark_mode: Whether to use dark theme
            bg_color: Background color for editor
            text_color: Text color for editor
            designator_linker: Optional linker for @REF click highlighting
            on_text_changed: Optional callback when text changes
        """
        super().__init__(parent)
        
        self._dark_mode = dark_mode
        self._theme = DARK_THEME if dark_mode else LIGHT_THEME
        self._bg_color = bg_color or hex_to_colour(self._theme["bg_editor"])
        self._text_color = text_color or hex_to_colour(self._theme["text_primary"])
        self._designator_linker = designator_linker
        self._on_text_changed_callback = on_text_changed
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create formatting toolbar
        self._toolbar = self._create_toolbar()
        main_sizer.Add(self._toolbar, 0, wx.EXPAND)
        
        # Create text editor
        self._editor = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_RICH2 | wx.BORDER_NONE
        )
        self._editor.SetBackgroundColour(self._bg_color)
        self._editor.SetForegroundColour(self._text_color)
        self._editor.SetFont(wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        # Set default text style
        font = self._editor.GetFont()
        text_attr = wx.TextAttr(self._text_color, self._bg_color, font)
        self._editor.SetDefaultStyle(text_attr)
        
        # Bind events
        self._editor.Bind(wx.EVT_TEXT, self._on_text_changed)
        self._editor.Bind(wx.EVT_LEFT_DOWN, self._on_text_click)
        self._editor.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
        
        # Add editor with padding from centralized EDITOR_LAYOUT config
        main_sizer.Add(self._editor, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, EDITOR_LAYOUT['margin_left'])
        main_sizer.Add((0, EDITOR_LAYOUT['padding_bottom']))  # Bottom padding
        
        self.SetSizer(main_sizer)
        self.SetBackgroundColour(self._bg_color)
    
    def _create_toolbar(self) -> wx.Panel:
        """Create formatting toolbar with all buttons."""
        toolbar = wx.Panel(self)
        toolbar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        toolbar.SetMinSize((-1, 48))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSpacer(12)
        
        # Formatting buttons: (label, tooltip, handler, font_weight)
        buttons = [
            ("B", "Bold (Ctrl+B)", self._on_format_bold, wx.FONTWEIGHT_BOLD),
            ("I", "Italic (Ctrl+I)", self._on_format_italic, None),
            ("U", "Underline (Ctrl+U)", self._on_format_underline, None),
            ("|", None, None, None),  # Separator
            ("H1", "Heading 1 (Ctrl+1)", self._on_format_h1, None),
            ("H2", "Heading 2 (Ctrl+2)", self._on_format_h2, None),
            ("|", None, None, None),  # Separator
            ("•", "Bullet List (Ctrl+Shift+B)", self._on_format_bullet, None),
            ("1.", "Numbered List (Ctrl+Shift+N)", self._on_format_numbered, None),
            ("☐", "Task Checkbox (Ctrl+Shift+X)", self._on_format_checkbox, None),
            ("|", None, None, None),  # Separator
            ("—", "Insert Divider (Ctrl+Shift+H)", self._on_format_divider, None),
            ("🕒", "Insert Timestamp (Alt+T)", self._on_format_timestamp, None),
        ]
        
        self._format_buttons = []
        
        for item in buttons:
            if item[0] == "|":
                # Vertical separator
                sep = wx.StaticLine(toolbar, style=wx.LI_VERTICAL, size=(1, 32))
                sep.SetBackgroundColour(hex_to_colour(self._theme["text_secondary"]))
                sizer.Add(sep, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 8)
            else:
                label, tooltip, handler, font_weight = item
                btn = wx.Button(toolbar, label=label, size=(36, 36), style=wx.BORDER_NONE)
                btn.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
                btn.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
                
                # Set font
                if font_weight:
                    btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, font_weight))
                elif label == "I":
                    btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
                elif label in ["H1", "H2"]:
                    btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
                else:
                    btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
                
                if tooltip:
                    btn.SetToolTip(tooltip)
                if handler:
                    btn.Bind(wx.EVT_BUTTON, handler)
                
                btn.SetCursor(wx.Cursor(wx.CURSOR_HAND))
                self._format_buttons.append(btn)
                sizer.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        
        toolbar.SetSizer(sizer)
        return toolbar
    
    # ============================================================
    # PUBLIC API (matches VisualEditor interface)
    # ============================================================
    
    def GetValue(self) -> str:
        """Get the editor content as markdown text."""
        return self._editor.GetValue()
    
    def SetValue(self, content: str):
        """Set the editor content."""
        self._editor.SetValue(content)
    
    def WriteText(self, text: str):
        """Insert text at cursor position."""
        self._editor.WriteText(text)
    
    def SetBackgroundColour(self, colour: wx.Colour):
        """Set editor background color."""
        super().SetBackgroundColour(colour)
        self._bg_color = colour
        if hasattr(self, '_editor'):
            self._editor.SetBackgroundColour(colour)
    
    def SetForegroundColour(self, colour: wx.Colour):
        """Set editor text color."""
        super().SetForegroundColour(colour)
        self._text_color = colour
        if hasattr(self, '_editor'):
            self._editor.SetForegroundColour(colour)
    
    def set_designator_linker(self, linker):
        """Set the designator linker for @REF click handling."""
        self._designator_linker = linker
    
    def apply_theme(self, dark_mode: bool, bg_color: wx.Colour = None, text_color: wx.Colour = None):
        """Apply theme colors to the editor."""
        self._dark_mode = dark_mode
        self._theme = DARK_THEME if dark_mode else LIGHT_THEME
        
        if bg_color:
            self._bg_color = bg_color
        if text_color:
            self._text_color = text_color
        
        # Update toolbar
        self._toolbar.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
        for btn in self._format_buttons:
            btn.SetBackgroundColour(hex_to_colour(self._theme["bg_toolbar"]))
            btn.SetForegroundColour(hex_to_colour(self._theme["text_primary"]))
        
        # Update editor
        self._editor.SetBackgroundColour(self._bg_color)
        self._editor.SetForegroundColour(self._text_color)
        
        # Update text style
        font = self._editor.GetFont()
        text_attr = wx.TextAttr(self._text_color, self._bg_color, font)
        self._editor.SetDefaultStyle(text_attr)
        self._editor.SetStyle(0, self._editor.GetLastPosition(), text_attr)
        
        self.Refresh()
    
    # ============================================================
    # EVENT HANDLERS
    # ============================================================
    
    def _on_text_changed(self, event):
        """Handle text change event."""
        if self._on_text_changed_callback:
            self._on_text_changed_callback(event)
        event.Skip()
    
    def _on_text_click(self, event):
        """Handle @REF clicks for designator highlighting."""
        if not self._designator_linker:
            event.Skip()
            return
        
        try:
            pos = self._editor.HitTestPos(event.GetPosition())[1]
            if pos >= 0:
                text = self._editor.GetValue()
                word = self._get_word_at_pos(text, pos)
                if word.startswith("@"):
                    self._designator_linker.highlight(word[1:])
                    return
        except:
            pass
        event.Skip()
    
    def _get_word_at_pos(self, text: str, pos: int) -> str:
        """Get word at text position."""
        if pos < 0 or pos >= len(text):
            return ""
        start = end = pos
        while start > 0 and (text[start-1].isalnum() or text[start-1] in "@_"):
            start -= 1
        while end < len(text) and (text[end].isalnum() or text[end] in "@_"):
            end += 1
        return text[start:end]
    
    def _on_key_down(self, event):
        """Handle keyboard shortcuts for formatting."""
        keycode = event.GetKeyCode()
        ctrl = event.ControlDown()
        shift = event.ShiftDown()
        alt = event.AltDown()
        
        # Ctrl+B = Bold
        if ctrl and not shift and keycode == ord('B'):
            self._on_format_bold(None)
            return
        
        # Ctrl+I = Italic
        if ctrl and not shift and keycode == ord('I'):
            self._on_format_italic(None)
            return
        
        # Ctrl+U = Underline
        if ctrl and not shift and keycode == ord('U'):
            self._on_format_underline(None)
            return
        
        # Ctrl+1 = H1
        if ctrl and not shift and keycode == ord('1'):
            self._on_format_h1(None)
            return
        
        # Ctrl+2 = H2
        if ctrl and not shift and keycode == ord('2'):
            self._on_format_h2(None)
            return
        
        # Ctrl+Shift+B = Bullet
        if ctrl and shift and keycode == ord('B'):
            self._on_format_bullet(None)
            return
        
        # Ctrl+Shift+N = Numbered
        if ctrl and shift and keycode == ord('N'):
            self._on_format_numbered(None)
            return
        
        # Ctrl+Shift+X = Checkbox
        if ctrl and shift and keycode == ord('X'):
            self._on_format_checkbox(None)
            return
        
        # Ctrl+Shift+H = Divider
        if ctrl and shift and keycode == ord('H'):
            self._on_format_divider(None)
            return
        
        # Alt+T = Timestamp
        if alt and not ctrl and keycode == ord('T'):
            self._on_format_timestamp(None)
            return
        
        # Enter key in list - continue list
        if keycode == wx.WXK_RETURN:
            self._handle_list_continuation()
            return
        
        event.Skip()
    
    # ============================================================
    # FORMATTING HANDLERS
    # ============================================================
    
    def _on_format_bold(self, event):
        """Apply bold formatting."""
        self._wrap_selection("**", "**")
    
    def _on_format_italic(self, event):
        """Apply italic formatting."""
        self._wrap_selection("*", "*")
    
    def _on_format_underline(self, event):
        """Apply underline formatting."""
        self._wrap_selection("<u>", "</u>")
    
    def _on_format_h1(self, event):
        """Apply Heading 1 formatting."""
        self._apply_line_prefix("# ")
    
    def _on_format_h2(self, event):
        """Apply Heading 2 formatting."""
        self._apply_line_prefix("## ")
    
    def _on_format_bullet(self, event):
        """Apply bullet list formatting."""
        self._apply_line_prefix("- ")
    
    def _on_format_numbered(self, event):
        """Apply numbered list formatting."""
        self._apply_line_prefix("1. ")
    
    def _on_format_checkbox(self, event):
        """Apply task checkbox formatting."""
        self._apply_line_prefix("- [ ] ")
    
    def _on_format_divider(self, event):
        """Insert horizontal divider."""
        pos = self._editor.GetInsertionPoint()
        self._editor.WriteText("\n---\n")
        self._editor.SetInsertionPoint(pos + 5)
    
    def _on_format_timestamp(self, event):
        """Insert current timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._editor.WriteText(timestamp)
    
    def _wrap_selection(self, prefix: str, suffix: str):
        """Wrap selected text with prefix and suffix."""
        start, end = self._editor.GetSelection()
        
        if start == end:
            # No selection - insert template and select placeholder
            self._editor.WriteText(prefix + "text" + suffix)
            new_pos = start + len(prefix)
            self._editor.SetSelection(new_pos, new_pos + 4)
        else:
            # Wrap selection
            selected_text = self._editor.GetStringSelection()
            self._editor.Replace(start, end, prefix + selected_text + suffix)
            # Restore selection to wrapped content
            self._editor.SetSelection(start + len(prefix), end + len(prefix))
    
    def _apply_line_prefix(self, prefix: str):
        """Apply prefix to current line or selected lines."""
        start, end = self._editor.GetSelection()
        
        # Get line boundaries
        line_start = self._editor.GetRange(0, start).rfind('\n')
        line_start = 0 if line_start == -1 else line_start + 1
        
        line_end = self._editor.GetRange(end, self._editor.GetLastPosition()).find('\n')
        line_end = self._editor.GetLastPosition() if line_end == -1 else end + line_end
        
        # Get current line content
        line_content = self._editor.GetRange(line_start, line_end)
        
        # Remove existing heading/list markers
        cleaned = re.sub(r'^(#{1,6}\s+|- \[ \] |- \[x\] |- |1\. |\d+\. )', '', line_content)
        
        # Apply new prefix
        new_content = prefix + cleaned
        self._editor.Replace(line_start, line_end, new_content)
        
        # Restore cursor position
        self._editor.SetInsertionPoint(line_start + len(new_content))
    
    def _handle_list_continuation(self):
        """Auto-continue lists when pressing Enter."""
        pos = self._editor.GetInsertionPoint()
        
        # Get current line
        line_start = self._editor.GetRange(0, pos).rfind('\n')
        line_start = 0 if line_start == -1 else line_start + 1
        line_content = self._editor.GetRange(line_start, pos)
        
        # Check for list markers
        bullet_match = re.match(r'^(\s*- )', line_content)
        checkbox_match = re.match(r'^(\s*- \[ \] )', line_content)
        numbered_match = re.match(r'^(\s*)(\d+)\. ', line_content)
        
        if checkbox_match:
            # Continue checkbox list
            indent = checkbox_match.group(1)
            self._editor.WriteText('\n' + indent)
        elif bullet_match:
            # Continue bullet list
            indent = bullet_match.group(1)
            self._editor.WriteText('\n' + indent)
        elif numbered_match:
            # Continue numbered list with incremented number
            indent = numbered_match.group(1)
            num = int(numbered_match.group(2)) + 1
            self._editor.WriteText(f'\n{indent}{num}. ')
        else:
            # Normal enter
            self._editor.WriteText('\n')
