"""
KiNotes Toolbar - Icon-based toolbar with iOS-like styling
"""
import wx
import os


class KiNotesToolbar(wx.Panel):
    """iOS-inspired toolbar with icon buttons."""
    
    def __init__(self, parent, on_save=None, on_export_pdf=None, on_import_metadata=None):
        super().__init__(parent)
        self.on_save = on_save
        self.on_export_pdf = on_export_pdf
        self.on_import_metadata = on_import_metadata
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize toolbar UI."""
        from .styles import KiNotesStyles as Styles
        
        self.SetBackgroundColour(Styles.get_toolbar_bg_color())
        self.SetMinSize((-1, Styles.TOOLBAR_HEIGHT))
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Left side - Title
        title = wx.StaticText(self, label="KiNotes")
        title.SetFont(Styles.get_title_font())
        title.SetForegroundColour(Styles.get_text_color())
        sizer.Add(title, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, Styles.PADDING_LARGE)
        
        sizer.AddStretchSpacer(1)
        
        # Right side - Buttons
        btn_size = (Styles.ICON_BUTTON_SIZE + 20, Styles.ICON_BUTTON_SIZE)
        
        # Import Metadata dropdown
        self.import_btn = wx.Button(self, label="📥 Import", size=(-1, btn_size[1]))
        self.import_btn.SetToolTip("Import board metadata")
        self.import_btn.Bind(wx.EVT_BUTTON, self._on_import_click)
        Styles.apply_button_style(self.import_btn)
        sizer.Add(self.import_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, Styles.PADDING_SMALL)
        
        # Export PDF button
        self.export_btn = wx.Button(self, label="📄 PDF", size=(-1, btn_size[1]))
        self.export_btn.SetToolTip("Export notes as PDF")
        self.export_btn.Bind(wx.EVT_BUTTON, self._on_export_click)
        Styles.apply_button_style(self.export_btn)
        sizer.Add(self.export_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, Styles.PADDING_SMALL)
        
        # Save button
        self.save_btn = wx.Button(self, label="💾 Save", size=(-1, btn_size[1]))
        self.save_btn.SetToolTip("Save notes (auto-saves on edit)")
        self.save_btn.Bind(wx.EVT_BUTTON, self._on_save_click)
        Styles.apply_button_style(self.save_btn)
        sizer.Add(self.save_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, Styles.PADDING_LARGE)
        
        self.SetSizer(sizer)
    
    def _on_save_click(self, event):
        if self.on_save:
            self.on_save()
    
    def _on_export_click(self, event):
        if self.on_export_pdf:
            self.on_export_pdf()
    
    def _on_import_click(self, event):
        """Show metadata import dropdown menu."""
        menu = wx.Menu()
        
        items = [
            ("📋 BOM (Bill of Materials)", "bom"),
            ("📚 Stackup", "stackup"),
            ("📐 Board Size", "board_size"),
            ("⚡ Differential Pairs", "diff_pairs"),
            ("🔌 Netlist Summary", "netlist"),
            ("🗂️ Layer Information", "layers"),
            ("🔩 Drill Table", "drill_table"),
            ("📏 Design Rules", "design_rules"),
            ("📝 All Metadata", "all"),
        ]
        
        for label, meta_type in items:
            item = menu.Append(wx.ID_ANY, label)
            self.Bind(wx.EVT_MENU, lambda e, t=meta_type: self._on_metadata_selected(t), item)
        
        # Show menu below button
        btn_pos = self.import_btn.GetPosition()
        btn_size = self.import_btn.GetSize()
        self.PopupMenu(menu, (btn_pos.x, btn_pos.y + btn_size.y))
        menu.Destroy()
    
    def _on_metadata_selected(self, meta_type):
        if self.on_import_metadata:
            self.on_import_metadata(meta_type)
