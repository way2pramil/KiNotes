"""
KiNotes - Smart Engineering Notes for KiCad 9+
Main Action Plugin Entry Point

Features:
- Markdown-based notes with auto-save
- @REF designator linking to highlight components
- Import board metadata (BOM, stackup, netlist, etc.)
- Export to PDF
- iOS-inspired UI with KiCad integration
- Dockable panel or popup window

Target: KiCad 9.0+ (Python 3.9+, wxPython 4.2+)
Author: PCBtools.xyz
License: MIT
"""

import pcbnew
import wx
import os
import sys

# Add package to path for imports
_plugin_dir = os.path.dirname(os.path.abspath(__file__))
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

from core.notes_manager import NotesManager
from core.designator_linker import DesignatorLinker
from core.metadata_extractor import MetadataExtractor
from core.pdf_exporter import PDFExporter
from ui.main_panel import KiNotesMainPanel
from ui.styles import KiNotesStyles


class KiNotesFrame(wx.Frame):
    """
    Main KiNotes window - can be used as popup or docked.
    iOS-inspired design following KiCad UI patterns.
    """
    
    def __init__(self, parent=None, project_dir=None):
        # Get project info
        self.project_dir = project_dir or self._get_project_dir()
        project_name = os.path.basename(self.project_dir) if self.project_dir else "KiNotes"
        
        super().__init__(
            parent,
            title=f"KiNotes - {project_name}",
            size=(500, 700),
            style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT
        )
        
        # Initialize core modules
        self.notes_manager = NotesManager(self.project_dir)
        self.designator_linker = DesignatorLinker()
        self.metadata_extractor = MetadataExtractor()
        self.pdf_exporter = PDFExporter(self.project_dir)
        
        self._init_ui()
        self._bind_events()
        
        # Center on screen
        self.Centre()
    
    def _get_project_dir(self):
        """Get project directory from current board."""
        try:
            board = pcbnew.GetBoard()
            if board:
                filename = board.GetFileName()
                if filename:
                    return os.path.dirname(filename)
        except:
            pass
        return os.getcwd()
    
    def _init_ui(self):
        """Initialize the main UI."""
        # Apply styling
        KiNotesStyles.apply_panel_style(self)
        
        # Set icon
        icon_path = os.path.join(_plugin_dir, "resources", "icon.png")
        if os.path.exists(icon_path):
            self.SetIcon(wx.Icon(icon_path))
        
        # Main panel with all features
        self.main_panel = KiNotesMainPanel(
            self,
            self.notes_manager,
            self.designator_linker,
            self.metadata_extractor,
            self.pdf_exporter
        )
        
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.main_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
    
    def _bind_events(self):
        """Bind window events."""
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_ACTIVATE, self._on_activate)
        
        # Auto-save on focus loss (outside click)
        self.Bind(wx.EVT_KILL_FOCUS, self._on_focus_lost)
    
    def _on_close(self, event):
        """Handle window close - auto-save."""
        try:
            self.main_panel.force_save()
            self.main_panel.cleanup()
        except:
            pass
        self.Destroy()
    
    def _on_activate(self, event):
        """Handle window activation changes."""
        if not event.GetActive():
            # Window deactivated - auto-save
            try:
                self.main_panel.force_save()
            except:
                pass
        event.Skip()
    
    def _on_focus_lost(self, event):
        """Handle focus loss - auto-save."""
        try:
            self.main_panel.force_save()
        except:
            pass
        event.Skip()


class KiNotesDockablePanel(wx.Panel):
    """
    Dockable panel version of KiNotes.
    Can be docked to left/right like KiCad Properties panel.
    """
    
    def __init__(self, parent, project_dir=None):
        super().__init__(parent)
        
        self.project_dir = project_dir or self._get_project_dir()
        
        # Initialize core modules
        self.notes_manager = NotesManager(self.project_dir)
        self.designator_linker = DesignatorLinker()
        self.metadata_extractor = MetadataExtractor()
        self.pdf_exporter = PDFExporter(self.project_dir)
        
        self._init_ui()
    
    def _get_project_dir(self):
        """Get project directory from current board."""
        try:
            board = pcbnew.GetBoard()
            if board:
                filename = board.GetFileName()
                if filename:
                    return os.path.dirname(filename)
        except:
            pass
        return os.getcwd()
    
    def _init_ui(self):
        """Initialize the dockable panel UI."""
        KiNotesStyles.apply_panel_style(self)
        
        # Main panel
        self.main_panel = KiNotesMainPanel(
            self,
            self.notes_manager,
            self.designator_linker,
            self.metadata_extractor,
            self.pdf_exporter
        )
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.main_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)


class KiNotesActionPlugin(pcbnew.ActionPlugin):
    """
    KiCad Action Plugin for KiNotes.
    Registers in Tools → External Plugins menu and toolbar.
    """
    
    def defaults(self):
        """Set plugin defaults."""
        self.name = "KiNotes"
        self.category = "Utilities"
        self.description = "Smart engineering notes linked to your PCB design"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(_plugin_dir, "resources", "icon.png")
        
        # For dark mode icon (KiCad 9+)
        dark_icon = os.path.join(_plugin_dir, "resources", "icon.png")
        if os.path.exists(dark_icon):
            self.dark_icon_file_name = dark_icon
    
    def Run(self):
        """Run the plugin - show KiNotes window."""
        # Validate environment
        if not self._validate_environment():
            return
        
        # Get project directory
        board = pcbnew.GetBoard()
        project_dir = os.path.dirname(board.GetFileName()) if board else None
        
        # Show KiNotes window
        frame = KiNotesFrame(None, project_dir)
        frame.Show(True)
    
    def _validate_environment(self):
        """Validate that we can run the plugin."""
        board = pcbnew.GetBoard()
        
        if not board:
            wx.MessageBox(
                "Please open a PCB layout first.",
                "KiNotes",
                wx.OK | wx.ICON_WARNING
            )
            return False
        
        project_path = board.GetFileName()
        
        if not project_path or project_path.strip() == "":
            wx.MessageBox(
                "Please save your PCB layout before using KiNotes.\n\n"
                "KiNotes stores notes in your project folder.",
                "KiNotes",
                wx.OK | wx.ICON_WARNING
            )
            return False
        
        # Check for read-only locations
        project_path_lower = project_path.lower()
        if (project_path_lower.startswith("c:\\program files") or 
            "kicad\\demos" in project_path_lower or
            "kicad/demos" in project_path_lower):
            wx.MessageBox(
                "Read-only project location detected.\n\n"
                "Please save the PCB project to a writable location "
                "(e.g., Documents) before using KiNotes.",
                "KiNotes",
                wx.OK | wx.ICON_ERROR
            )
            return False
        
        return True


# Register the plugin
KiNotesActionPlugin().register()
