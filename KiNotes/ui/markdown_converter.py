"""
KiNotes Markdown Converter - Bidirectional Markdown/RichText Conversion
========================================================================
Provides conversion between Markdown text and wx.richtext.RichTextCtrl
formatting for seamless Visual/Markdown mode switching.

Features:
- Markdown → RichText: Parse MD and apply formatting
- RichText → Markdown: Extract formatting and generate clean MD
- Preserves: Bold, Italic, Underline, Headings, Lists, Checkboxes,
             Links, Images, Tables, Code blocks, Dividers

Compatible with: KiCad 9+ / wxPython 4.1+ / Python 3.8+

Author: KiNotes Team (pcbtools.xyz)
License: MIT
"""
import wx
import wx.richtext as rt
import os
import re
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class MarkdownBlock:
    """Represents a parsed Markdown block."""
    type: str  # 'paragraph', 'heading', 'bullet', 'numbered', 'checkbox', 'code', 'divider', 'table', 'image'
    content: str
    level: int = 0  # For headings (1-3) or list indentation
    checked: bool = False  # For checkboxes
    url: str = ""  # For links/images
    children: List['MarkdownBlock'] = field(default_factory=list)


@dataclass 
class TextSpan:
    """Represents a span of formatted text."""
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    code: bool = False
    link_url: str = ""


# ============================================================
# MARKDOWN PARSER
# ============================================================

class MarkdownParser:
    """
    Parse Markdown text into structured blocks.
    Supports common Markdown syntax used in notes.
    """
    
    # Regex patterns
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$')
    BULLET_PATTERN = re.compile(r'^(\s*)[-*+]\s+(.+)$')
    NUMBERED_PATTERN = re.compile(r'^(\s*)(\d+)\.\s+(.+)$')
    CHECKBOX_PATTERN = re.compile(r'^(\s*)[-*]\s+\[([ xX])\]\s+(.+)$')
    DIVIDER_PATTERN = re.compile(r'^[-─═_]{3,}$')
    CODE_BLOCK_START = re.compile(r'^```(\w*)$')
    CODE_BLOCK_END = re.compile(r'^```$')
    IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    TABLE_ROW_PATTERN = re.compile(r'^\|(.+)\|$')
    
    # Inline formatting patterns
    BOLD_PATTERN = re.compile(r'\*\*(.+?)\*\*|__(.+?)__')
    ITALIC_PATTERN = re.compile(r'\*(.+?)\*|_(.+?)_')
    STRIKETHROUGH_PATTERN = re.compile(r'~~(.+?)~~')
    CODE_INLINE_PATTERN = re.compile(r'`([^`]+)`')
    
    def parse(self, markdown_text: str) -> List[MarkdownBlock]:
        """
        Parse Markdown text into blocks.
        
        Args:
            markdown_text: Raw Markdown string
            
        Returns:
            List of MarkdownBlock objects
        """
        blocks = []
        lines = markdown_text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Preserve empty lines as empty paragraphs
            if not line.strip():
                blocks.append(MarkdownBlock(type='empty', content=''))
                i += 1
                continue
            
            # Code block
            code_match = self.CODE_BLOCK_START.match(line)
            if code_match:
                language = code_match.group(1)
                code_lines = []
                i += 1
                while i < len(lines) and not self.CODE_BLOCK_END.match(lines[i]):
                    code_lines.append(lines[i])
                    i += 1
                blocks.append(MarkdownBlock(
                    type='code',
                    content='\n'.join(code_lines),
                    level=0
                ))
                i += 1  # Skip closing ```
                continue
            
            # Heading
            heading_match = self.HEADING_PATTERN.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                content = heading_match.group(2)
                blocks.append(MarkdownBlock(
                    type='heading',
                    content=content,
                    level=min(level, 3)
                ))
                i += 1
                continue
            
            # Checkbox
            checkbox_match = self.CHECKBOX_PATTERN.match(line)
            if checkbox_match:
                indent = len(checkbox_match.group(1))
                checked = checkbox_match.group(2).lower() == 'x'
                content = checkbox_match.group(3)
                blocks.append(MarkdownBlock(
                    type='checkbox',
                    content=content,
                    level=indent // 2,
                    checked=checked
                ))
                i += 1
                continue
            
            # Bullet list
            bullet_match = self.BULLET_PATTERN.match(line)
            if bullet_match:
                indent = len(bullet_match.group(1))
                content = bullet_match.group(2)
                blocks.append(MarkdownBlock(
                    type='bullet',
                    content=content,
                    level=indent // 2
                ))
                i += 1
                continue
            
            # Numbered list
            numbered_match = self.NUMBERED_PATTERN.match(line)
            if numbered_match:
                indent = len(numbered_match.group(1))
                number = int(numbered_match.group(2))
                content = numbered_match.group(3)
                blocks.append(MarkdownBlock(
                    type='numbered',
                    content=content,
                    level=indent // 2
                ))
                i += 1
                continue
            
            # Divider
            if self.DIVIDER_PATTERN.match(line.strip()):
                blocks.append(MarkdownBlock(type='divider', content=''))
                i += 1
                continue
            
            # Table (collect all table rows)
            if self.TABLE_ROW_PATTERN.match(line):
                table_lines = [line]
                i += 1
                while i < len(lines) and self.TABLE_ROW_PATTERN.match(lines[i]):
                    table_lines.append(lines[i])
                    i += 1
                blocks.append(MarkdownBlock(
                    type='table',
                    content='\n'.join(table_lines)
                ))
                continue
            
            # Image (standalone)
            image_match = self.IMAGE_PATTERN.match(line.strip())
            if image_match:
                alt_text = image_match.group(1)
                url = image_match.group(2)
                blocks.append(MarkdownBlock(
                    type='image',
                    content=alt_text,
                    url=url
                ))
                i += 1
                continue
            
            # Regular paragraph
            blocks.append(MarkdownBlock(
                type='paragraph',
                content=line
            ))
            i += 1
        
        return blocks
    
    def parse_inline(self, text: str) -> List[TextSpan]:
        """
        Parse inline formatting in text.
        
        Args:
            text: Text with potential inline formatting
            
        Returns:
            List of TextSpan objects with formatting info
        """
        spans = []
        
        # Handle nested formatting: **[text](url)** or *[text](url)*
        # Strategy: Process outer formatting first, then inner
        
        import re
        
        # Pattern for bold link: **[text](url)** 
        bold_link_pattern = re.compile(r'\*\*\[([^\]]+)\]\(([^)]+)\)\*\*')
        # Pattern for italic link: *[text](url)*
        italic_link_pattern = re.compile(r'(?<!\*)\*(?!\*)\[([^\]]+)\]\(([^)]+)\)\*(?!\*)')
        # Pattern for plain link: [text](url)
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        # Pattern for bold: **text**
        bold_pattern = re.compile(r'\*\*([^*\[\]]+?)\*\*')
        # Pattern for italic: *text*
        italic_pattern = re.compile(r'(?<!\*)\*(?!\*)([^*\[\]]+?)\*(?!\*)')
        # Pattern for code: `text`
        code_pattern = re.compile(r'`([^`]+)`')
        
        pos = 0
        while pos < len(text):
            # Find the earliest match among all patterns
            best_match = None
            best_type = None
            best_start = len(text)
            
            # Check bold+link
            m = bold_link_pattern.search(text, pos)
            if m and m.start() < best_start:
                best_match = m
                best_type = 'bold_link'
                best_start = m.start()
            
            # Check italic+link
            m = italic_link_pattern.search(text, pos)
            if m and m.start() < best_start:
                best_match = m
                best_type = 'italic_link'
                best_start = m.start()
            
            # Check plain link
            m = link_pattern.search(text, pos)
            if m and m.start() < best_start:
                best_match = m
                best_type = 'link'
                best_start = m.start()
            
            # Check bold
            m = bold_pattern.search(text, pos)
            if m and m.start() < best_start:
                best_match = m
                best_type = 'bold'
                best_start = m.start()
            
            # Check italic
            m = italic_pattern.search(text, pos)
            if m and m.start() < best_start:
                best_match = m
                best_type = 'italic'
                best_start = m.start()
            
            # Check code
            m = code_pattern.search(text, pos)
            if m and m.start() < best_start:
                best_match = m
                best_type = 'code'
                best_start = m.start()
            
            if best_match:
                # Add plain text before this match
                if best_start > pos:
                    spans.append(TextSpan(text=text[pos:best_start]))
                
                # Add the formatted span
                if best_type == 'bold_link':
                    spans.append(TextSpan(text=best_match.group(1), bold=True, link_url=best_match.group(2)))
                elif best_type == 'italic_link':
                    spans.append(TextSpan(text=best_match.group(1), italic=True, link_url=best_match.group(2)))
                elif best_type == 'link':
                    spans.append(TextSpan(text=best_match.group(1), link_url=best_match.group(2)))
                elif best_type == 'bold':
                    spans.append(TextSpan(text=best_match.group(1), bold=True))
                elif best_type == 'italic':
                    spans.append(TextSpan(text=best_match.group(1), italic=True))
                elif best_type == 'code':
                    spans.append(TextSpan(text=best_match.group(1), code=True))
                
                pos = best_match.end()
            else:
                # No more matches - add remaining text
                if pos < len(text):
                    spans.append(TextSpan(text=text[pos:]))
                break
        
        # If no spans were created, return the whole text as a single span
        if not spans:
            spans.append(TextSpan(text=text))
        
        return spans


# ============================================================
# MARKDOWN → RICH TEXT CONVERTER
# ============================================================

class MarkdownToRichText:
    """
    Convert Markdown text to wx.richtext.RichTextCtrl formatting.
    """
    
    def __init__(self, editor: rt.RichTextCtrl, dark_mode: bool = False, 
                 text_color: wx.Colour = None, bg_color: wx.Colour = None):
        """
        Initialize converter.
        
        Args:
            editor: Target RichTextCtrl
            dark_mode: Use dark theme colors
            text_color: Custom text color (uses theme default if None)
            bg_color: Custom background color (uses theme default if None)
        """
        self.editor = editor
        self.dark_mode = dark_mode
        self.custom_text_color = text_color
        self.custom_bg_color = bg_color
        self.parser = MarkdownParser()
    
    def convert(self, markdown_text: str):
        """
        Convert Markdown to rich text and populate editor.
        
        Args:
            markdown_text: Markdown formatted string
        """
        # Clear editor
        self.editor.Clear()
        
        # Parse markdown
        blocks = self.parser.parse(markdown_text)
        
        # Convert each block
        for block in blocks:
            self._convert_block(block)
    
    def _convert_block(self, block: MarkdownBlock):
        """Convert a single block to rich text."""
        if block.type == 'heading':
            self._write_heading(block)
        elif block.type == 'paragraph':
            self._write_paragraph(block)
        elif block.type == 'empty':
            self._write_empty_line()
        elif block.type == 'bullet':
            self._write_bullet(block)
        elif block.type == 'numbered':
            self._write_numbered(block)
        elif block.type == 'checkbox':
            self._write_checkbox(block)
        elif block.type == 'code':
            self._write_code(block)
        elif block.type == 'divider':
            self._write_divider(block)
        elif block.type == 'table':
            self._write_table(block)
        elif block.type == 'image':
            self._write_image(block)
    
    def _get_text_color(self) -> wx.Colour:
        """Get appropriate text color for theme."""
        if self.custom_text_color:
            return self.custom_text_color
        if self.dark_mode:
            return wx.Colour(230, 230, 230)
        return wx.Colour(50, 50, 50)
    
    def _get_heading_color(self) -> wx.Colour:
        """Get heading text color - uses custom theme color if available."""
        if self.custom_text_color:
            return self.custom_text_color
        if self.dark_mode:
            return wx.Colour(255, 255, 255)
        return wx.Colour(30, 30, 30)
    
    def _write_heading(self, block: MarkdownBlock):
        """Write heading block."""
        # Determine font size based on heading level
        if block.level == 1:
            font_size = 22
        elif block.level == 2:
            font_size = 18
        else:
            font_size = 14
        
        heading_color = self._get_heading_color()
        
        # Set paragraph attributes (spacing)
        para_attr = rt.RichTextAttr()
        para_attr.SetParagraphSpacingBefore(16)
        para_attr.SetParagraphSpacingAfter(8)
        self.editor.BeginStyle(para_attr)
        
        # Write inline text with heading's font size and bold
        self._write_inline_text(block.content, base_font_size=font_size, base_bold=True, base_color=heading_color)
        
        self.editor.EndStyle()
        self.editor.Newline()
    
    def _write_paragraph(self, block: MarkdownBlock):
        """Write paragraph block."""
        text_color = self._get_text_color()
        
        # Set paragraph attributes
        para_attr = rt.RichTextAttr()
        para_attr.SetParagraphSpacingBefore(4)
        para_attr.SetParagraphSpacingAfter(4)
        self.editor.BeginStyle(para_attr)
        
        # Write inline text with normal font size
        self._write_inline_text(block.content, base_font_size=11, base_bold=False, base_color=text_color)
        
        self.editor.EndStyle()
        self.editor.Newline()
    
    def _write_empty_line(self):
        """Write an empty line to preserve spacing."""
        self.editor.Newline()
    
    def _write_bullet(self, block: MarkdownBlock):
        """Write bullet list item."""
        indent = "  " * block.level
        bullet = "•"
        text_color = self._get_text_color()
        
        attr = rt.RichTextAttr()
        attr.SetFontSize(11)
        attr.SetTextColour(text_color)
        
        self.editor.BeginStyle(attr)
        self.editor.WriteText(f"{indent}{bullet} ")
        self.editor.EndStyle()
        
        # Write content with inline formatting
        self._write_inline_text(block.content, base_font_size=11, base_bold=False, base_color=text_color)
        self.editor.Newline()
    
    def _write_numbered(self, block: MarkdownBlock):
        """Write numbered list item."""
        indent = "  " * block.level
        text_color = self._get_text_color()
        
        attr = rt.RichTextAttr()
        attr.SetFontSize(11)
        attr.SetTextColour(text_color)
        
        self.editor.BeginStyle(attr)
        # We don't track actual numbers, just use placeholder
        self.editor.WriteText(f"{indent}1. ")
        self.editor.EndStyle()
        
        # Write content with inline formatting
        self._write_inline_text(block.content, base_font_size=11, base_bold=False, base_color=text_color)
        self.editor.Newline()
    
    def _write_checkbox(self, block: MarkdownBlock):
        """Write checkbox list item."""
        indent = "  " * block.level
        checkbox = "☑" if block.checked else "☐"
        text_color = self._get_text_color()
        
        attr = rt.RichTextAttr()
        attr.SetFontSize(11)
        attr.SetTextColour(text_color)
        
        self.editor.BeginStyle(attr)
        self.editor.WriteText(f"{indent}{checkbox} ")
        self.editor.EndStyle()
        
        # Write content with inline formatting
        self._write_inline_text(block.content, base_font_size=11, base_bold=False, base_color=text_color)
        self.editor.Newline()
    
    def _write_code(self, block: MarkdownBlock):
        """Write code block."""
        attr = rt.RichTextAttr()
        attr.SetFontSize(10)
        attr.SetFontFaceName("Consolas" if hasattr(wx, 'msw') else "Monaco")
        
        if self.dark_mode:
            attr.SetTextColour(wx.Colour(152, 195, 121))
            attr.SetBackgroundColour(wx.Colour(40, 44, 52))
        else:
            attr.SetTextColour(wx.Colour(50, 50, 50))
            attr.SetBackgroundColour(wx.Colour(245, 245, 245))
        
        self.editor.BeginStyle(attr)
        self.editor.WriteText(block.content)
        self.editor.EndStyle()
        self.editor.Newline()
    
    def _write_divider(self, block: MarkdownBlock):
        """Write horizontal divider."""
        attr = rt.RichTextAttr()
        attr.SetTextColour(wx.Colour(180, 180, 180))
        attr.SetParagraphSpacingBefore(8)
        attr.SetParagraphSpacingAfter(8)
        
        self.editor.BeginStyle(attr)
        self.editor.WriteText("─" * 40)
        self.editor.EndStyle()
        self.editor.Newline()
    
    def _write_table(self, block: MarkdownBlock):
        """Write table (as monospace text for now)."""
        attr = rt.RichTextAttr()
        attr.SetFontSize(10)
        attr.SetFontFaceName("Consolas" if hasattr(wx, 'msw') else "Monaco")
        attr.SetTextColour(self._get_text_color())
        
        self.editor.BeginStyle(attr)
        self.editor.WriteText(block.content)
        self.editor.EndStyle()
        self.editor.Newline()
    
    def _write_image(self, block: MarkdownBlock):
        """Write image."""
        try:
            if block.url.startswith(('http://', 'https://')):
                # For URLs, just show placeholder text
                attr = rt.RichTextAttr()
                attr.SetTextColour(wx.Colour(100, 100, 100))
                attr.SetFontStyle(wx.FONTSTYLE_ITALIC)
                
                self.editor.BeginStyle(attr)
                self.editor.WriteText(f"[Image: {block.content or block.url}]")
                self.editor.EndStyle()
            else:
                # Try to load local image
                if os.path.exists(block.url):
                    image = wx.Image(block.url, wx.BITMAP_TYPE_ANY)
                    if image.IsOk():
                        # Scale if needed
                        max_width = 400
                        if image.GetWidth() > max_width:
                            ratio = max_width / image.GetWidth()
                            new_height = int(image.GetHeight() * ratio)
                            image = image.Scale(max_width, new_height, wx.IMAGE_QUALITY_HIGH)
                        self.editor.WriteImage(image)
                    else:
                        self.editor.WriteText(f"[Image not found: {block.url}]")
                else:
                    self.editor.WriteText(f"[Image: {block.url}]")
        except Exception as e:
            self.editor.WriteText(f"[Image error: {e}]")
        
        self.editor.Newline()
    
    def _write_inline_text(self, text: str, base_font_size: int = 11, base_bold: bool = False, base_color: wx.Colour = None):
        """
        Write text with inline formatting.
        
        Args:
            text: The text to write with inline markdown parsed
            base_font_size: Font size to use (inherited from parent block like heading)
            base_bold: Whether base text should be bold (e.g., headings)
            base_color: Base text color (if None, uses theme default)
        """
        spans = self.parser.parse_inline(text)
        
        if base_color is None:
            base_color = self._get_text_color()
        
        for span in spans:
            attr = rt.RichTextAttr()
            attr.SetFontSize(base_font_size)
            attr.SetTextColour(base_color)
            
            # Apply base bold if specified (for headings)
            if base_bold:
                attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
            
            # Apply inline formatting on top of base
            if span.bold:
                attr.SetFontWeight(wx.FONTWEIGHT_BOLD)
            if span.italic:
                attr.SetFontStyle(wx.FONTSTYLE_ITALIC)
            if span.underline:
                attr.SetFontUnderlined(True)
            if span.code:
                attr.SetFontFaceName("Consolas" if hasattr(wx, 'msw') else "Monaco")
                if self.dark_mode:
                    attr.SetTextColour(wx.Colour(152, 195, 121))
                else:
                    attr.SetTextColour(wx.Colour(200, 40, 40))
            if span.link_url:
                attr.SetFontUnderlined(True)
                if self.dark_mode:
                    attr.SetTextColour(wx.Colour(97, 175, 239))
                else:
                    attr.SetTextColour(wx.Colour(0, 102, 204))
                attr.SetURL(span.link_url)
            
            self.editor.BeginStyle(attr)
            self.editor.WriteText(span.text)
            self.editor.EndStyle()


# ============================================================
# RICH TEXT → MARKDOWN CONVERTER
# ============================================================

class RichTextToMarkdown:
    """
    Convert wx.richtext.RichTextCtrl content to Markdown text.
    """
    
    def __init__(self, editor: rt.RichTextCtrl):
        """
        Initialize converter.
        
        Args:
            editor: Source RichTextCtrl
        """
        self.editor = editor
    
    def convert(self) -> str:
        """
        Convert rich text to Markdown.
        
        Returns:
            Markdown formatted string
        """
        lines = []
        text = self.editor.GetValue()
        
        if not text:
            return ""
        
        # Process line by line
        text_lines = text.split('\n')
        
        for line_num, line in enumerate(text_lines):
            if not line.strip():
                lines.append("")
                continue
            
            # Get position in editor
            pos = self._get_line_start_position(line_num)
            
            # Check if this is a divider
            if line.strip() and all(c in '─═-_' for c in line.strip()):
                lines.append("---")
                continue
            
            # Check for list prefixes
            if line.startswith('• '):
                content = self._convert_line_inline(line[2:], pos + 2)
                lines.append(f"- {content}")
                continue
            elif line.startswith('◦ '):
                content = self._convert_line_inline(line[2:], pos + 2)
                lines.append(f"  - {content}")
                continue
            elif re.match(r'^\d+\.\s', line):
                match = re.match(r'^(\d+)\.\s(.*)$', line)
                if match:
                    num = match.group(1)
                    content = self._convert_line_inline(match.group(2), pos + len(num) + 2)
                    lines.append(f"{num}. {content}")
                    continue
            elif line.startswith('☐ ') or line.startswith('☑ '):
                checked = line[0] == '☑'
                content = self._convert_line_inline(line[2:], pos + 2)
                checkbox = "[x]" if checked else "[ ]"
                lines.append(f"- {checkbox} {content}")
                continue
            
            # Check for heading (by font size)
            heading_level = self._get_heading_level(pos)
            if heading_level > 0:
                content = self._convert_line_inline(line, pos)
                lines.append(f"{'#' * heading_level} {content}")
                continue
            
            # Regular paragraph
            content = self._convert_line_inline(line, pos)
            lines.append(content)
        
        return '\n'.join(lines)
    
    def _get_line_start_position(self, line_num: int) -> int:
        """Get the character position at the start of a line."""
        text = self.editor.GetValue()
        lines = text.split('\n')
        
        pos = 0
        for i in range(line_num):
            if i < len(lines):
                pos += len(lines[i]) + 1  # +1 for newline
        
        return pos
    
    def _get_heading_level(self, pos: int) -> int:
        """Determine heading level by checking font size at position."""
        try:
            attr = rt.RichTextAttr()
            if self.editor.GetStyle(pos, attr):
                font_size = attr.GetFontSize()
                
                if font_size >= 20:
                    return 1
                elif font_size >= 16:
                    return 2
                elif font_size >= 13:
                    return 3
        except:
            pass
        
        return 0
    
    def _convert_line_inline(self, line: str, start_pos: int) -> str:
        """Convert a line with inline formatting to Markdown."""
        result = []
        
        print(f"[KiNotes MD] Converting line: {repr(line)}, start_pos: {start_pos}")
        
        i = 0
        while i < len(line):
            char_pos = start_pos + i
            
            # Get style at this position
            attr = rt.RichTextAttr()
            has_style = False
            try:
                has_style = self.editor.GetStyle(char_pos, attr)
            except:
                pass
            
            # Find extent of this formatting
            j = i + 1
            while j < len(line):
                next_attr = rt.RichTextAttr()
                try:
                    self.editor.GetStyle(start_pos + j, next_attr)
                    if not self._same_formatting(attr, next_attr):
                        break
                except:
                    break
                j += 1
            
            # Get the text span
            span_text = line[i:j]
            
            # Debug output
            url = attr.GetURL() if has_style else ""
            is_bold = attr.GetFontWeight() == wx.FONTWEIGHT_BOLD if has_style else False
            print(f"[KiNotes MD]   Span [{i}:{j}]: {repr(span_text)}, bold={is_bold}, url={repr(url)}")
            
            # Apply Markdown formatting
            if has_style:
                is_bold = attr.GetFontWeight() == wx.FONTWEIGHT_BOLD
                is_italic = attr.GetFontStyle() == wx.FONTSTYLE_ITALIC
                is_underline = attr.GetFontUnderlined()
                
                # Check for links FIRST - link text should be plain
                url = attr.GetURL()
                if url:
                    # Link text should NOT have formatting markers inside
                    # Format: **[text](url)** for bold link, not [**text**](url)
                    link_part = f"[{span_text}]({url})"
                    # Now wrap the entire link with bold/italic if needed
                    if is_bold and is_italic:
                        span_text = f"***{link_part}***"
                    elif is_bold:
                        span_text = f"**{link_part}**"
                    elif is_italic:
                        span_text = f"*{link_part}*"
                    else:
                        span_text = link_part
                else:
                    # No link - apply formatting normally
                    if is_bold:
                        span_text = f"**{span_text}**"
                    if is_italic:
                        span_text = f"*{span_text}*"
            
            result.append(span_text)
            i = j
        
        return ''.join(result)
    
    def _same_formatting(self, attr1: rt.RichTextAttr, attr2: rt.RichTextAttr) -> bool:
        """Check if two attributes have the same formatting."""
        try:
            return (attr1.GetFontWeight() == attr2.GetFontWeight() and
                    attr1.GetFontStyle() == attr2.GetFontStyle() and
                    attr1.GetFontUnderlined() == attr2.GetFontUnderlined() and
                    attr1.GetURL() == attr2.GetURL())
        except:
            return True


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def markdown_to_richtext(editor: rt.RichTextCtrl, markdown_text: str, dark_mode: bool = False,
                         text_color: wx.Colour = None, bg_color: wx.Colour = None):
    """
    Convenience function to convert Markdown to RichText.
    
    Args:
        editor: Target RichTextCtrl
        markdown_text: Markdown string
        dark_mode: Use dark theme colors
        text_color: Custom text color (optional)
        bg_color: Custom background color (optional)
    """
    converter = MarkdownToRichText(editor, dark_mode, text_color, bg_color)
    converter.convert(markdown_text)


def richtext_to_markdown(editor: rt.RichTextCtrl) -> str:
    """
    Convenience function to convert RichText to Markdown.
    
    Args:
        editor: Source RichTextCtrl
        
    Returns:
        Markdown string
    """
    converter = RichTextToMarkdown(editor)
    return converter.convert()


def sanitize_markdown(text: str) -> str:
    """
    Sanitize Markdown text to prevent HTML injection.
    
    Args:
        text: Raw text that might contain HTML
        
    Returns:
        Sanitized text
    """
    # Escape HTML entities
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    return text


def clean_markdown_output(text: str) -> str:
    """
    Clean up generated Markdown for better readability.
    
    Args:
        text: Generated Markdown
        
    Returns:
        Cleaned Markdown
    """
    # Remove excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Ensure file ends with single newline
    text = text.rstrip() + '\n'
    
    return text
