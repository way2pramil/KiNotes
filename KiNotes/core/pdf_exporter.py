"""
KiNotes PDF Exporter - Export notes as PDF
"""
import os
from datetime import datetime

from .defaultsConfig import debug_print

try:
    import wx
    HAS_WX = True
except ImportError:
    HAS_WX = False

try:
    import pcbnew
    HAS_PCBNEW = True
except ImportError:
    HAS_PCBNEW = False


class PDFExporter:
    """Export notes to PDF format."""
    
    def __init__(self, project_dir):
        """Initialize with project directory."""
        self.project_dir = project_dir
    
    def _get_project_name(self):
        """Get project name from directory or board."""
        if HAS_PCBNEW:
            try:
                board = pcbnew.GetBoard()
                if board:
                    filename = board.GetFileName()
                    if filename:
                        return os.path.splitext(os.path.basename(filename))[0]
            except:
                pass
        
        return os.path.basename(self.project_dir)
    
    def _get_default_filename(self):
        """Generate default PDF filename."""
        project_name = self._get_project_name()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return f"{project_name}_notes_{timestamp}.pdf"
    
    def export(self, content, filepath=None):
        """
        Export notes content to PDF.
        
        Args:
            content: Markdown text content
            filepath: Optional output path. If None, prompts user.
        
        Returns:
            Path to exported file, or None if cancelled/failed
        """
        if not HAS_WX:
            raise RuntimeError("wxPython required for PDF export")
        
        # Get output path
        if not filepath:
            filepath = self._prompt_save_location()
            if not filepath:
                return None
        
        try:
            # Use wx.html2 for rendering or simple text-based PDF
            # Since we want no external dependencies, we'll use wx printing
            return self._export_with_wx_printing(content, filepath)
        except Exception as e:
            raise RuntimeError(f"PDF export failed: {e}")
    
    def export_visual(self, rich_text_ctrl, filepath=None):
        """
        Export from Visual Editor (RichTextCtrl) with formatting preserved.
        
        Args:
            rich_text_ctrl: wx.richtext.RichTextCtrl instance
            filepath: Optional output path. If None, prompts user.
        
        Returns:
            Path to exported file, or None if cancelled/failed
        """
        if not HAS_WX:
            raise RuntimeError("wxPython required for PDF export")
        
        # Get output path
        if not filepath:
            filepath = self._prompt_save_location()
            if not filepath:
                return None
        
        try:
            # Try reportlab first for best results
            actual_pdf = self._try_create_visual_pdf(rich_text_ctrl, filepath)
            if actual_pdf:
                return actual_pdf
            
            # Fallback: Use wx printing with RichTextCtrl
            return self._export_visual_with_wx_printing(rich_text_ctrl, filepath)
        except Exception as e:
            raise RuntimeError(f"Visual PDF export failed: {e}")
    
    def _try_create_visual_pdf(self, rich_text_ctrl, filepath):
        """Try to create PDF from RichTextCtrl using reportlab - convert via markdown first."""
        try:
            debug_print("[KiNotes PDF] Starting visual PDF export...")
            
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, cm
            from reportlab.lib.colors import HexColor
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
            
            debug_print("[KiNotes PDF] reportlab imported successfully")
            
            # Use the markdown converter to extract formatting properly
            try:
                from ui.markdown_converter import richtext_to_markdown
                debug_print("[KiNotes PDF] markdown_converter imported (method 1)")
            except ImportError:
                try:
                    from ..ui.markdown_converter import richtext_to_markdown
                    debug_print("[KiNotes PDF] markdown_converter imported (method 2)")
                except ImportError:
                    # Fallback: direct import for different package structures
                    import sys
                    import os
                    plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if plugin_dir not in sys.path:
                        sys.path.insert(0, plugin_dir)
                    from ui.markdown_converter import richtext_to_markdown
                    debug_print("[KiNotes PDF] markdown_converter imported (method 3)")
            
            # Convert RichTextCtrl to Markdown (this extracts all formatting)
            debug_print("[KiNotes PDF] Converting RichText to Markdown...")
            markdown_content = richtext_to_markdown(rich_text_ctrl)
            
            # DEBUG: Show first 500 chars of markdown
            debug_print(f"[KiNotes PDF] Markdown content ({len(markdown_content)} chars):")
            debug_print("=" * 50)
            for line in markdown_content.split('\n')[:15]:
                debug_print(f"  {repr(line)}")
            debug_print("=" * 50)
            
            # Check if formatting markers exist
            has_bold = '**' in markdown_content
            has_italic = '*' in markdown_content.replace('**', '')
            has_heading = markdown_content.strip().startswith('#') or '\n#' in markdown_content
            has_hr = '---' in markdown_content or '___' in markdown_content
            debug_print(f"[KiNotes PDF] Formatting detected: bold={has_bold}, italic={has_italic}, heading={has_heading}, hr={has_hr}")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            project_name = self._get_project_name()
            
            def add_footer(canvas, doc):
                """Add footer with blue line, branding, and page number."""
                canvas.saveState()
                page_width, page_height = A4
                margin = 1.5 * cm
                footer_y = margin - 0.3 * cm
                
                # Blue horizontal line
                canvas.setStrokeColor(HexColor('#2196F3'))
                canvas.setLineWidth(1.5)
                canvas.line(margin, footer_y + 0.5 * cm, page_width - margin, footer_y + 0.5 * cm)
                
                # Branding
                canvas.setFont('Helvetica', 8)
                canvas.setFillColor(HexColor('#666666'))
                footer_text = f"Generated by KiNotes - PCBtools.xyz | {timestamp}"
                canvas.drawString(margin, footer_y, footer_text)
                
                # Page number
                canvas.setFont('Helvetica-Bold', 9)
                canvas.setFillColor(HexColor('#888888'))
                page_num = f"Page {doc.page}"
                canvas.drawRightString(page_width - margin, footer_y, page_num)
                
                canvas.restoreState()
            
            doc = SimpleDocTemplate(
                filepath, 
                pagesize=A4,
                leftMargin=1.5*cm,
                rightMargin=1.5*cm,
                topMargin=1.5*cm,
                bottomMargin=2*cm
            )
            
            styles = getSampleStyleSheet()
            story = []
            
            # Title - centered
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=8,
                alignment=1  # 1 = CENTER
            )
            story.append(Paragraph(f"{project_name} - Design Notes", title_style))
            story.append(Spacer(1, 0.1*inch))
            # Separator line after title
            story.append(HRFlowable(width="100%", thickness=1.5, color=HexColor('#2196F3'), spaceAfter=12))
            story.append(Spacer(1, 0.15*inch))
            
            # Define styles
            h1_style = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=16, spaceAfter=10, spaceBefore=12)
            h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=13, spaceAfter=8, spaceBefore=10)
            h3_style = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=11, spaceAfter=6, spaceBefore=8)
            body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, spaceAfter=6, leading=14)
            bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'], fontSize=10, spaceAfter=4, leftIndent=20, bulletIndent=10, leading=14)
            
            # Process markdown lines
            import re
            for line in markdown_content.split('\n'):
                # Check for headings
                heading_match = re.match(r'^(#{1,3})\s+(.+)$', line)
                if heading_match:
                    level = len(heading_match.group(1))
                    raw_text = heading_match.group(2)
                    if level == 1:
                        story.append(self._convert_and_paragraph(raw_text, h1_style))
                    elif level == 2:
                        story.append(self._convert_and_paragraph(raw_text, h2_style))
                    else:
                        story.append(self._convert_and_paragraph(raw_text, h3_style))
                    continue
                
                # Check for horizontal rule
                if re.match(r'^[-─═_]{3,}$', line.strip()):
                    story.append(Spacer(1, 0.1*inch))
                    story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#CCCCCC')))
                    story.append(Spacer(1, 0.1*inch))
                    continue
                
                # Check for bullet list
                bullet_match = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
                if bullet_match:
                    indent = len(bullet_match.group(1))
                    raw_text = bullet_match.group(2)
                    style = ParagraphStyle('BulletIndent', parent=bullet_style, leftIndent=20 + indent*10)
                    # Convert with link support, prepend bullet
                    formatted = self._convert_markdown_formatting(raw_text, enable_links=True)
                    story.append(self._safe_paragraph(f"• {formatted}", style))
                    continue
                
                # Check for numbered list
                num_match = re.match(r'^(\s*)(\d+)\.\s+(.+)$', line)
                if num_match:
                    indent = len(num_match.group(1))
                    num = num_match.group(2)
                    raw_text = num_match.group(3)
                    style = ParagraphStyle('NumIndent', parent=bullet_style, leftIndent=20 + indent*10)
                    formatted = self._convert_markdown_formatting(raw_text, enable_links=True)
                    story.append(self._safe_paragraph(f"{num}. {formatted}", style))
                    continue
                
                # Check for checkbox
                checkbox_match = re.match(r'^[-*]\s+\[([ xX])\]\s+(.+)$', line)
                if checkbox_match:
                    checked = checkbox_match.group(1).lower() == 'x'
                    raw_text = checkbox_match.group(2)
                    checkbox_char = "☑" if checked else "☐"
                    formatted = self._convert_markdown_formatting(raw_text, enable_links=True)
                    story.append(self._safe_paragraph(f"{checkbox_char} {formatted}", bullet_style))
                    continue
                
                # Regular paragraph - use full fallback chain
                if line.strip():
                    story.append(self._convert_and_paragraph(line, body_style))
                else:
                    story.append(Spacer(1, 0.1*inch))
            
            debug_print(f"[KiNotes PDF] Building PDF with {len(story)} story elements...")
            doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
            debug_print(f"[KiNotes PDF] SUCCESS! PDF created at: {filepath}")
            return filepath
            
        except ImportError as e:
            debug_print(f"[KiNotes PDF] IMPORT ERROR: {e}")
            return None
        except Exception as e:
            debug_print(f"[KiNotes PDF] EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _strip_all_markdown(self, text):
        """Strip all markdown formatting, returning plain text."""
        import re
        # Remove links - keep just the text
        text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
        # Remove orphaned link fragments like ](url)
        text = re.sub(r'\]\([^)]*\)', '', text)
        # Remove bold/italic markers
        text = re.sub(r'\*{1,3}', '', text)
        text = re.sub(r'_{1,3}', '', text)
        # Remove strikethrough
        text = re.sub(r'~~', '', text)
        # Escape HTML entities
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return text
    
    def _safe_paragraph(self, text, style):
        """Create a Paragraph, falling back to plain text if XML is malformed."""
        from reportlab.platypus import Paragraph
        try:
            return Paragraph(text, style)
        except ValueError as e:
            # XML parsing error - fall back to plain text
            debug_print(f"[KiNotes PDF] XML error in paragraph, using plain text")
            # Strip all XML tags and return plain text
            import re
            plain = re.sub(r'<[^>]+>', '', text)
            return Paragraph(plain, style)
    
    def _convert_and_paragraph(self, raw_text, style):
        """Convert markdown to XML and create Paragraph with link fallback.
        
        First tries with clickable links enabled.
        If that fails, retries with links stripped to plain text.
        If that still fails, strips all formatting.
        """
        from reportlab.platypus import Paragraph
        import re
        
        # Try 1: With clickable links
        try:
            formatted = self._convert_markdown_formatting(raw_text, enable_links=True)
            return Paragraph(formatted, style)
        except ValueError as e:
            debug_print(f"[KiNotes PDF] Link conversion failed, retrying without links")
        
        # Try 2: Without links (plain text links)
        try:
            formatted = self._convert_markdown_formatting(raw_text, enable_links=False)
            return Paragraph(formatted, style)
        except ValueError as e:
            debug_print(f"[KiNotes PDF] Formatting failed, using plain text")
        
        # Try 3: Plain text only
        plain = self._strip_all_markdown(raw_text)
        return Paragraph(plain, style)
    
    def _convert_markdown_formatting(self, text, enable_links=True):
        """Convert Markdown inline formatting to reportlab XML tags.
        
        IMPORTANT: reportlab requires properly nested XML tags.
        If we open <b> then <i>, we must close </i> then </b>.
        
        Args:
            text: Markdown text to convert
            enable_links: If True, convert [text](url) to clickable <a> tags.
                         If False, strip links to plain text (fallback mode).
        """
        import re
        
        # Escape HTML entities first
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        if enable_links:
            # Convert links to clickable <a> tags
            # Handle [text](url) -> <a href="url" color="blue"><u>text</u></a>
            def convert_link(match):
                link_text = match.group(1)
                url = match.group(2)
                # Strip any formatting markers from link text for clean display
                link_text = re.sub(r'\*+', '', link_text)
                link_text = re.sub(r'_+', '', link_text)
                link_text = link_text.strip()
                if not link_text:
                    link_text = url  # Use URL as text if empty
                # Return clickable link with blue underline
                return f'<a href="{url}" color="blue"><u>{link_text}</u></a>'
            
            text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', convert_link, text)
        else:
            # Fallback: strip links to plain text
            text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
        
        # Clean orphaned link fragments
        text = re.sub(r'\]\([^)]*\)', '', text)  # orphaned ](url) -> nothing
        text = re.sub(r'\[([^\]]*)\]', r'\1', text)  # orphaned [text] -> text
        
        # Clean the text of any existing malformed asterisks patterns first
        # Remove sequences like **** or more
        text = re.sub(r'\*{4,}', '', text)
        
        # Now apply formatting in order, using non-greedy matches
        # Bold + Italic: ***text*** - must be processed FIRST
        text = re.sub(r'\*\*\*([^*]+)\*\*\*', r'<b><i>\1</i></b>', text)
        
        # Bold: **text**
        text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
        
        # Italic: *text* (single asterisks)
        # Be careful not to match inside already-converted tags
        text = re.sub(r'(?<!<[bi]>)\*([^*<>]+)\*(?!</[bi]>)', r'<i>\1</i>', text)
        
        # Strikethrough: ~~text~~
        text = re.sub(r'~~([^~]+)~~', r'<strike>\1</strike>', text)
        
        # Final cleanup - remove any leftover markdown characters
        text = re.sub(r'\*+', '', text)  # Remove any remaining asterisks
        text = re.sub(r'_+', '', text)  # Remove any remaining underscores (not in words)
        
        # Validate XML tag nesting - if broken, strip all tags
        if not self._validate_xml_nesting(text):
            debug_print(f"[KiNotes PDF] Invalid XML nesting detected, stripping tags")
            text = re.sub(r'<[^>]+>', '', text)
        
        return text
    
    def _validate_xml_nesting(self, text):
        """Check if XML tags are properly nested."""
        import re
        stack = []
        # Find all tags
        for match in re.finditer(r'<(/?)([a-z]+)>', text):
            is_close = match.group(1) == '/'
            tag = match.group(2)
            if is_close:
                if not stack or stack[-1] != tag:
                    return False  # Mismatched closing tag
                stack.pop()
            else:
                stack.append(tag)
        return len(stack) == 0  # All tags should be closed
    
    def _export_visual_with_wx_printing(self, rich_text_ctrl, filepath):
        """Export RichTextCtrl using wx printing."""
        try:
            import wx.richtext as rt
            
            # Get plain text as fallback
            content = rich_text_ctrl.GetValue()
            project_name = self._get_project_name()
            
            # Try text-based PDF
            actual_pdf = self._try_create_pdf(content, filepath, project_name)
            if actual_pdf:
                return actual_pdf
            
            # Final fallback to text file
            return self._export_as_text_pdf(content, filepath)
            
        except Exception as e:
            debug_print(f"KiNotes: wx printing visual export failed: {e}")
            # Fallback to markdown export
            content = rich_text_ctrl.GetValue()
            return self._export_as_text_pdf(content, filepath)
    
    def _prompt_save_location(self):
        """Show save dialog and return chosen path."""
        default_name = self._get_default_filename()
        # Default to .kinotes/ folder if it exists, otherwise project root
        kinotes_dir = os.path.join(self.project_dir, '.kinotes')
        default_dir = kinotes_dir if os.path.exists(kinotes_dir) else self.project_dir
        
        with wx.FileDialog(
            None,
            "Export Notes as PDF",
            defaultDir=default_dir,
            defaultFile=default_name,
            wildcard="PDF files (*.pdf)|*.pdf",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                return dialog.GetPath()
        return None
    
    def _export_with_wx_printing(self, content, filepath):
        """Export using wx printing framework."""
        try:
            # Create a printout
            printout = NotesPrintout(content, self._get_project_name())
            
            # Create printer DC for PDF
            print_data = wx.PrintData()
            print_data.SetFilename(filepath)
            print_data.SetPrintMode(wx.PRINT_MODE_FILE)
            
            # Set to PDF printer if available
            # Note: This creates a print file, not a true PDF on all platforms
            # For true PDF, would need reportlab or similar
            
            dc = wx.PrinterDC(print_data)
            
            if dc.IsOk():
                printout.SetDC(dc)
                printout.OnPrintPage(1)
                return filepath
            else:
                # Fallback: Save as formatted text file with .pdf extension
                # User can convert or we notify them
                return self._export_as_text_pdf(content, filepath)
                
        except Exception as e:
            # Fallback to text export
            return self._export_as_text_pdf(content, filepath)
    
    def _export_as_text_pdf(self, content, filepath):
        """
        Fallback: Export as nicely formatted text.
        Note: This creates a text file. For true PDF, recommend installing reportlab.
        """
        # Change extension to .txt and notify
        txt_path = filepath.replace('.pdf', '.txt')
        
        project_name = self._get_project_name()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        header = f"""{'='*60}
{project_name} - Design Notes
Exported: {timestamp}
{'='*60}

"""
        footer = f"""

{'='*60}
Generated by KiNotes - PCBtools.xyz
{'='*60}
"""
        
        formatted_content = header + content + footer
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        # Also try to create actual PDF if possible
        actual_pdf = self._try_create_pdf(content, filepath, project_name)
        if actual_pdf:
            return actual_pdf
        
        # Show message about text export with clear instructions
        if HAS_WX:
            wx.MessageBox(
                f"PDF export created text file:\n{txt_path}\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📦 To enable full PDF export with formatting:\n\n"
                "1. Open KiCad Command Prompt (or terminal)\n"
                "2. Run: pip install reportlab\n"
                "3. Restart KiCad\n\n"
                "📖 More info: pcbtools.xyz/tools/kinotes#requirements",
                "Export Note - PDF Package Required",
                wx.OK | wx.ICON_INFORMATION
            )
        
        return txt_path
    
    def _try_create_pdf(self, content, filepath, project_name):
        """Try to create actual PDF using reportlab if available."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, cm
            from reportlab.lib.colors import HexColor
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.enums import TA_RIGHT
            
            # Store timestamp for footer
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Custom canvas for footer on each page
            class FooterCanvas:
                def __init__(self, doc, timestamp):
                    self.doc = doc
                    self.timestamp = timestamp
                    self.pages = []
                
                def afterPage(self, canvas, doc):
                    self.pages.append(doc.page)
                
                def beforePage(self, canvas, doc):
                    pass
            
            def add_footer(canvas, doc):
                """Add footer with blue line, branding, and page number."""
                canvas.saveState()
                
                page_width, page_height = A4
                margin = 1.5 * cm
                footer_y = margin - 0.3 * cm
                
                # Blue horizontal line
                canvas.setStrokeColor(HexColor('#2196F3'))  # Material Blue
                canvas.setLineWidth(1.5)
                canvas.line(margin, footer_y + 0.5 * cm, page_width - margin, footer_y + 0.5 * cm)
                
                # "Generated by KiNotes - PCBtools.xyz | timestamp"
                canvas.setFont('Helvetica', 8)
                canvas.setFillColor(HexColor('#666666'))  # Gray
                footer_text = f"Generated by KiNotes - PCBtools.xyz | {timestamp}"
                canvas.drawString(margin, footer_y, footer_text)
                
                # Page number in right corner, bold
                canvas.setFont('Helvetica-Bold', 9)
                canvas.setFillColor(HexColor('#888888'))  # Secondary gray
                page_num = f"Page {doc.page}"
                canvas.drawRightString(page_width - margin, footer_y, page_num)
                
                canvas.restoreState()
            
            doc = SimpleDocTemplate(
                filepath, 
                pagesize=A4,
                leftMargin=1.5*cm,
                rightMargin=1.5*cm,
                topMargin=1.5*cm,
                bottomMargin=2*cm  # Extra space for footer
            )
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=12
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                fontName='Courier'
            )
            
            story = []
            
            # Title
            story.append(Paragraph(f"{project_name} - Design Notes", title_style))
            story.append(Spacer(1, 0.25*inch))
            
            # Content (simple line-by-line)
            for line in content.split('\n'):
                if line.startswith('# '):
                    story.append(Paragraph(line[2:], styles['Heading1']))
                elif line.startswith('## '):
                    story.append(Paragraph(line[3:], styles['Heading2']))
                elif line.startswith('### '):
                    story.append(Paragraph(line[4:], styles['Heading3']))
                elif line.strip():
                    # Escape HTML entities
                    safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(safe_line, body_style))
                else:
                    story.append(Spacer(1, 0.1*inch))
            
            # Build with footer callback
            doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
            return filepath
            
        except ImportError:
            return None
        except Exception as e:
            debug_print(f"KiNotes: reportlab PDF failed: {e}")
            return None


class NotesPrintout(wx.Printout):
    """wx.Printout for notes content."""
    
    def __init__(self, content, title="KiNotes"):
        super().__init__(title)
        self.content = content
        self.title = title
    
    def OnPrintPage(self, page):
        dc = self.GetDC()
        if not dc:
            return False
        
        # Get page size
        w, h = dc.GetSize()
        
        # Margins
        margin = 50
        
        # Draw title
        dc.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        dc.DrawText(self.title, margin, margin)
        
        # Draw content
        dc.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        y = margin + 30
        line_height = 14
        
        for line in self.content.split('\n'):
            if y > h - margin - 40:  # Leave space for footer
                break
            dc.DrawText(line, margin, y)
            y += line_height
        
        # Draw blue horizontal line above footer
        dc.SetPen(wx.Pen(wx.Colour(33, 150, 243), 2))  # Material Blue
        footer_line_y = h - margin - 25
        dc.DrawLine(margin, footer_line_y, w - margin, footer_line_y)
        
        # Draw footer text
        dc.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        dc.SetTextForeground(wx.Colour(102, 102, 102))  # Gray
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        dc.DrawText(f"Generated by KiNotes - PCBtools.xyz | {timestamp}", margin, h - margin - 15)
        
        # Draw page number (right aligned, bold)
        dc.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        dc.SetTextForeground(wx.Colour(136, 136, 136))  # Secondary gray
        page_text = f"Page {page}"
        text_width = dc.GetTextExtent(page_text)[0]
        dc.DrawText(page_text, w - margin - text_width, h - margin - 15)
        
        return True
    
    def GetPageInfo(self):
        return (1, 1, 1, 1)
    
    def HasPage(self, page):
        return page == 1
