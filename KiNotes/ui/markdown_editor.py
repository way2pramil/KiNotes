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
License: Apache-2.0
"""
import wx
try:
    import wx.html
    _WX_HTML_AVAILABLE = True
except Exception:
    wx.html = None
    _WX_HTML_AVAILABLE = False
import re
import html
import os
from datetime import datetime
from typing import Optional, Callable

try:
    from ..core.kicad_extractor import get_project_dir, get_project_name
except Exception:
    try:
        from core.kicad_extractor import get_project_dir, get_project_name
    except Exception:
        def get_project_dir():
            return None
        def get_project_name():
            return None

try:
    import markdown as _markdown
    _MARKDOWN_AVAILABLE = True
except Exception:
    _markdown = None
    _MARKDOWN_AVAILABLE = False

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
        self._preview_enabled = True
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create formatting toolbar
        self._toolbar = self._create_toolbar()
        main_sizer.Add(self._toolbar, 0, wx.EXPAND)

        # Splitter for editor + live preview
        self._splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE | wx.BORDER_NONE)
        self._splitter.SetMinimumPaneSize(200)

        editor_panel = wx.Panel(self._splitter)
        preview_panel = wx.Panel(self._splitter)

        # Create text editor
        self._editor = wx.TextCtrl(
            editor_panel,
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

        # Editor panel layout
        editor_sizer = wx.BoxSizer(wx.VERTICAL)
        editor_sizer.Add(self._editor, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, EDITOR_LAYOUT['margin_left'])
        editor_sizer.Add((0, EDITOR_LAYOUT['padding_bottom']))
        editor_panel.SetSizer(editor_sizer)
        editor_panel.SetBackgroundColour(self._bg_color)

        # Preview (HTML) panel
        self._preview = None
        if self._preview_enabled and _WX_HTML_AVAILABLE:
            try:
                self._preview = wx.html.HtmlWindow(preview_panel, style=wx.BORDER_NONE)
                self._preview.SetBackgroundColour(self._bg_color)
                preview_sizer = wx.BoxSizer(wx.VERTICAL)
                preview_sizer.Add(self._preview, 1, wx.EXPAND | wx.ALL, EDITOR_LAYOUT['padding_horizontal'])
                preview_panel.SetSizer(preview_sizer)
                preview_panel.SetBackgroundColour(self._bg_color)
                self._splitter.SplitVertically(editor_panel, preview_panel, sashPosition=600)
            except Exception:
                self._preview = None
                self._splitter.Initialize(editor_panel)
        else:
            self._splitter.Initialize(editor_panel)

        main_sizer.Add(self._splitter, 1, wx.EXPAND)
        
        self.SetSizer(main_sizer)
        self.SetBackgroundColour(self._bg_color)

        # Initial preview render
        self._render_preview(self._editor.GetValue())
    
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
        self._render_preview(content)
    
    def WriteText(self, text: str):
        """Insert text at cursor position."""
        self._editor.WriteText(text)
        self._render_preview(self._editor.GetValue())
    
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
        if hasattr(self, '_preview'):
            self._preview.SetBackgroundColour(self._bg_color)
        
        # Update text style
        font = self._editor.GetFont()
        text_attr = wx.TextAttr(self._text_color, self._bg_color, font)
        self._editor.SetDefaultStyle(text_attr)
        self._editor.SetStyle(0, self._editor.GetLastPosition(), text_attr)

        self._render_preview(self._editor.GetValue())
        
        self.Refresh()
    
    # ============================================================
    # EVENT HANDLERS
    # ============================================================
    
    def _on_text_changed(self, event):
        """Handle text change event."""
        if self._on_text_changed_callback:
            self._on_text_changed_callback(event)
        self._render_preview(self._editor.GetValue())
        event.Skip()

    def _render_preview(self, text: str):
        """Render markdown to HTML for live preview."""
        if not self._preview or not self._preview_enabled:
            return
        try:
            self._preview.SetBackgroundColour(wx.Colour(30, 30, 30))
        except Exception:
            pass
        processed = self._preprocess_markdown(text)
        has_rtl = self._contains_rtl(processed)
        if not _MARKDOWN_AVAILABLE:
            safe = html.escape(processed)
            html = (
                "<div style='font-size:12px;opacity:0.8;margin-bottom:8px;'>"
                "Live preview requires the <b>Markdown</b> package. "
                "Install with: <code>pip install Markdown</code>"
                "</div>"
                f"<pre>{safe}</pre>"
            )
        else:
            html = _markdown.markdown(
                processed,
                extensions=[
                    "extra",
                    "tables",
                    "fenced_code",
                    "sane_lists",
                    "nl2br",
                ],
            )

        html += self._build_links_html(processed)

        body_dir = "rtl" if has_rtl else "ltr"
        wrapped = f'<div class="md-root" dir="{body_dir}">{html}</div>'
        page = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{self._get_preview_css()}
</style>
</head>
<body>
{wrapped}
</body>
</html>"""
        self._preview.SetPage(page)

    def _contains_rtl(self, text: str) -> bool:
        rtl_pattern = re.compile(r'[\u0590-\u08FF\uFB1D-\uFDFD\uFE70-\uFEFC]')
        return bool(rtl_pattern.search(text))

    def _extract_wikilinks(self, text: str):
        return re.findall(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', text)

    def _preprocess_markdown(self, text: str) -> str:
        """Handle Obsidian-style features in Markdown."""
        lines = text.splitlines()
        out = []
        in_code = False
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith("```"):
                in_code = not in_code
                out.append(line)
                i += 1
                continue

            if not in_code:
                callout_match = re.match(r'^\s*>\s*\[!(\w+)\]\s*(.*)$', line)
                if callout_match:
                    callout_type = callout_match.group(1).lower()
                    title = callout_match.group(1).capitalize()
                    content_lines = [callout_match.group(2)]
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        if next_line.lstrip().startswith(">"):
                            content_lines.append(next_line.lstrip()[1:].lstrip())
                            i += 1
                        else:
                            break
                    content = "\n".join(content_lines).strip()
                    out.append(
                        f"<div class=\"callout callout-{callout_type}\">"
                        f"<div class=\"callout-title\">{html.escape(title)}</div>"
                        f"<div class=\"callout-content\">\n{content}\n</div>"
                        f"</div>"
                    )
                    continue

                line = re.sub(
                    r'(^|[\s\(])(#([A-Za-z0-9_-]+))',
                    r'\1<span class="tag">#\3</span>',
                    line,
                )
                line = re.sub(
                    r'\[\[([^\]|]+)\|([^\]]+)\]\]',
                    r'<span class="wikilink" data-target="\1">\2</span>',
                    line,
                )
                line = re.sub(
                    r'\[\[([^\]]+)\]\]',
                    r'<span class="wikilink" data-target="\1">\1</span>',
                    line,
                )

            out.append(line)
            i += 1

        return "\n".join(out)

    def _build_links_html(self, text: str) -> str:
        links = self._extract_wikilinks(text)
        if not links:
            return ""

        unique = []
        seen = set()
        for target, alias in links:
            label = alias or target
            if (target, label) not in seen:
                unique.append((target, label))
                seen.add((target, label))

        items = "".join(
            f"<li><span class=\"wikilink\" data-target=\"{html.escape(t)}\">{html.escape(l)}</span></li>"
            for t, l in unique
        )

        backlinks = self._find_backlinks()
        backlinks_html = ""
        if backlinks:
            backlinks_items = "".join(
                f"<li>{html.escape(name)}</li>" for name in backlinks
            )
            backlinks_html = (
                "<div class=\"backlinks\">"
                "<div class=\"backlinks-title\">Backlinks</div>"
                f"<ul>{backlinks_items}</ul>"
                "</div>"
            )

        return (
            "<div class=\"links-panel\">"
            "<div class=\"links-title\">Links</div>"
            f"<ul>{items}</ul>"
            "</div>"
            f"{backlinks_html}"
        )

    def _find_backlinks(self):
        project_dir = get_project_dir()
        project_name = get_project_name()
        if not project_dir or not project_name:
            return []

        target = f"[[{project_name}]]"
        results = []
        try:
            for root, _, files in os.walk(project_dir):
                for name in files:
                    if not name.endswith(".md"):
                        continue
                    path = os.path.join(root, name)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                            if target in fh.read():
                                results.append(name)
                    except Exception:
                        continue
        except Exception:
            return []

        return sorted(set(results))

    def _get_preview_css(self) -> str:
        """Build CSS for preview pane (dark only)."""
        bg = "#1E1E1E"
        fg = "#E6E6E6"
        muted = "#9A9A9A"
        code_bg = "#2A2A2A"
        link = "#8AB4F8"

        return f"""
body {{
  background: {bg};
  color: {fg};
  font-family: Arial, sans-serif;
  font-size: 13px;
  line-height: 1.6;
  padding: 12px;
  direction: ltr;
  unicode-bidi: plaintext;
}}
.md-root, html {{
  background: {bg};
}}
.md-root[dir="rtl"] {{
  direction: rtl;
  text-align: right;
}}
h1, h2, h3, h4, h5, h6 {{
  margin: 16px 0 8px;
  color: {fg};
}}
p {{ margin: 8px 0; }}
code, pre {{
  background: {code_bg};
  color: {fg};
  border-radius: 6px;
  padding: 2px 4px;
  font-family: Consolas, monospace;
}}
pre {{
  padding: 10px;
  overflow-x: auto;
}}
blockquote {{
  border-left: 3px solid {muted};
  padding-left: 10px;
  color: {muted};
  margin: 8px 0;
}}
a {{ color: {link}; text-decoration: none; }}
ul, ol {{ margin: 8px 0 8px 20px; }}
table {{
  border-collapse: collapse;
  width: 100%;
  margin: 10px 0;
}}
th, td {{
  border: 1px solid {muted};
  padding: 6px 8px;
}}
.tag {{
  display: inline-block;
  padding: 2px 6px;
  margin: 0 2px;
  border-radius: 6px;
  background: #2A2A2A;
  color: {fg};
  font-size: 12px;
}}
.wikilink {{
  color: {link};
  cursor: pointer;
  text-decoration: none;
}}
.callout {{
  border: 1px solid {muted};
  border-left: 4px solid {link};
  padding: 8px 10px;
  margin: 10px 0;
  border-radius: 8px;
  background: #232323;
}}
.callout-title {{
  font-weight: bold;
  margin-bottom: 4px;
}}
.links-panel, .backlinks {{
  margin-top: 16px;
  padding: 10px;
  border: 1px solid {muted};
  border-radius: 8px;
  background: #232323;
}}
.links-title, .backlinks-title {{
  font-weight: bold;
  margin-bottom: 6px;
}}
"""
    
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
            
        # Alt+Backspace = Word Deletion (macOS Option+Delete)
        if alt and not ctrl and keycode == wx.WXK_BACK:
            self._delete_word_backwards()
            return
        
        # Enter key in list - continue list
        if keycode == wx.WXK_RETURN:
            self._handle_list_continuation()
            return
        
        event.Skip()
    
    def _delete_word_backwards(self):
        """Implement macOS-style Option+Delete word deletion."""
        start, end = self._editor.GetSelection()
        if start != end:
            self._editor.Remove(start, end)
            return

        pos = self._editor.GetInsertionPoint()
        if pos <= 0:
            return

        text = self._editor.GetValue()
        if not text:
            return

        # Ensure pos is within bounds
        pos = min(pos, len(text))
        new_pos = pos

        # Scan backward to skip immediate whitespace/punctuation if any
        while new_pos > 0 and not text[new_pos-1].isalnum():
            new_pos -= 1
            
        if new_pos == 0:
            self._editor.Remove(0, pos)
            return
            
        # Scan backward until we hit a non-alphanumeric character (word start)
        while new_pos > 0 and text[new_pos-1].isalnum():
            new_pos -= 1
            
        self._editor.Remove(new_pos, pos)

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
