"""
KiNotes - Smart Engineering Notes for KiCad 9+
Main Action Plugin Entry Point with Docking Support

Features:
- Multi-tab interface (Notes | Todo List | Settings)
- Markdown-based notes with auto-save
- @REF designator linking to highlight components
- Import board metadata (BOM, stackup, netlist, etc.)
- Export to PDF
- Dockable panel like KiCad Properties

Target: KiCad 9.0+ (Python 3.9+, wxPython 4.2+)
Author: PCBtools.xyz
License: MIT
"""

import pcbnew
import wx
import wx.aui as aui
import os
import sys

# Add package to path for imports
_plugin_dir = os.path.dirname(os.path.abspath(__file__))
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

# Force reload of modules to get latest changes
import importlib
try:
    from ui import main_panel
    importlib.reload(main_panel)
except:
    pass

from core.notes_manager import NotesManager
from core.designator_linker import DesignatorLinker
from core.metadata_extractor import MetadataExtractor
from core.pdf_exporter import PDFExporter
from ui.main_panel import KiNotesMainPanel

# Plugin version - change this to force reload
_PLUGIN_VERSION = "1.1.0"
print(f"KiNotes v{_PLUGIN_VERSION} loaded")


# Global singleton - ensures only ONE window ever
_kinotes_instance = {'frame': None, 'pane': None}


def get_kinotes_frame():
    """Get existing KiNotes frame if it exists and is valid."""
    frame = _kinotes_instance.get('frame')
    if frame is not None:
        try:
            # Check if frame is still valid and not destroyed
            if frame and isinstance(frame, wx.Frame):
                # Try to access a method to ensure it's not a dead object
                _ = frame.IsShown()
                return frame
        except (RuntimeError, wx.PyDeadObjectError, Exception):
            pass
    _kinotes_instance['frame'] = None
    return None


def set_kinotes_frame(frame):
    """Set the KiNotes frame reference."""
    _kinotes_instance['frame'] = frame


def close_all_kinotes_windows():
    """Close any existing KiNotes windows."""
    # Close tracked frame
    frame = _kinotes_instance.get('frame')
    if frame:
        try:
            frame.Destroy()
        except:
            pass
    _kinotes_instance['frame'] = None
    
    # Also search for any orphaned windows
    try:
        for win in wx.GetTopLevelWindows():
            try:
                if 'KiNotes' in win.GetTitle():
                    win.Destroy()
            except:
                pass
    except:
        pass


class KiNotesFrame(wx.MiniFrame):
    """
    KiNotes floating window with docking capability.
    Uses MiniFrame for proper floating behavior like KiCad panels.
    """
    
    def __init__(self, parent=None, project_dir=None):
        self.project_dir = project_dir or self._get_project_dir()
        project_name = os.path.basename(self.project_dir) if self.project_dir else "KiNotes"
        
        # MiniFrame style for proper floating/docking
        style = (wx.CAPTION | wx.CLOSE_BOX | wx.RESIZE_BORDER | 
                 wx.FRAME_TOOL_WINDOW | wx.FRAME_FLOAT_ON_PARENT |
                 wx.FRAME_NO_TASKBAR)
        
        super().__init__(
            parent,
            title=f"KiNotes",
            size=(420, 650),
            style=style
        )
        
        # Initialize core modules
        self.notes_manager = NotesManager(self.project_dir)
        self.designator_linker = DesignatorLinker()
        self.metadata_extractor = MetadataExtractor()
        self.pdf_exporter = PDFExporter(self.project_dir)
        
        self._init_ui()
        self._bind_events()
        self._position_window()
    
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
        """Initialize the UI."""
        self.SetBackgroundColour(wx.Colour(250, 250, 250))
        
        # Set icon
        icon_path = os.path.join(_plugin_dir, "resources", "icon.png")
        if os.path.exists(icon_path):
            try:
                self.SetIcon(wx.Icon(icon_path))
            except:
                pass
        
        # Main panel with tabs
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
        
        # Set minimum size
        self.SetMinSize((350, 400))
    
    def _position_window(self):
        """Position window on the right side like Properties panel."""
        try:
            # Get screen size
            display = wx.Display(0)
            screen_rect = display.GetClientArea()
            
            # Position on right side
            frame_size = self.GetSize()
            x = screen_rect.GetRight() - frame_size.GetWidth() - 20
            y = screen_rect.GetTop() + 100
            
            self.SetPosition((x, y))
        except:
            self.Centre()
    
    def _bind_events(self):
        """Bind window events."""
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_ACTIVATE, self._on_activate)
    
    def _on_close(self, event):
        """Handle close - save and hide."""
        try:
            self.main_panel.force_save()
            self.main_panel.cleanup()
        except:
            pass
        set_kinotes_frame(None)
        self.Destroy()
    
    def _on_activate(self, event):
        """Auto-save on deactivation."""
        if not event.GetActive():
            try:
                self.main_panel.force_save()
            except:
                pass
        event.Skip()


class KiNotesDockablePanel(wx.Panel):
    """
    Dockable panel version for KiCad AUI integration.
    Can be used with KiCad's AUI manager for docking.
    """
    
    def __init__(self, parent, project_dir=None):
        super().__init__(parent)
        
        self.project_dir = project_dir or self._get_project_dir()
        
        # Core modules
        self.notes_manager = NotesManager(self.project_dir)
        self.designator_linker = DesignatorLinker()
        self.metadata_extractor = MetadataExtractor()
        self.pdf_exporter = PDFExporter(self.project_dir)
        
        self._init_ui()
    
    def _get_project_dir(self):
        """Get project directory."""
        try:
            board = pcbnew.GetBoard()
            if board and board.GetFileName():
                return os.path.dirname(board.GetFileName())
        except:
            pass
        return os.getcwd()
    
    def _init_ui(self):
        """Initialize UI."""
        self.SetBackgroundColour(wx.Colour(250, 250, 250))
        
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
    
    def force_save(self):
        """Force save all data."""
        self.main_panel.force_save()
    
    def cleanup(self):
        """Cleanup resources."""
        self.main_panel.cleanup()


def try_dock_to_kicad(panel, project_dir):
    """
    Try to dock KiNotes panel to KiCad's AUI manager.
    Returns True if docking successful, False otherwise.
    """
    try:
        # Get KiCad's main frame
        main_frame = None
        for win in wx.GetTopLevelWindows():
            if 'pcbnew' in win.GetTitle().lower() or 'kicad' in win.GetTitle().lower():
                main_frame = win
                break
        
        if not main_frame:
            return False
        
        # Try to get AUI manager
        aui_mgr = None
        if hasattr(main_frame, 'GetAuiManager'):
            aui_mgr = main_frame.GetAuiManager()
        elif hasattr(main_frame, 'm_auiManager'):
            aui_mgr = main_frame.m_auiManager
        
        if not aui_mgr:
            return False
        
        # Create dockable panel
        dockable = KiNotesDockablePanel(main_frame, project_dir)
        
        # Create AUI pane info
        pane_info = aui.AuiPaneInfo()
        pane_info.Name("KiNotes")
        pane_info.Caption("KiNotes")
        pane_info.Right()  # Dock on right
        pane_info.Layer(1)
        pane_info.Position(0)
        pane_info.CloseButton(True)
        pane_info.MaximizeButton(False)
        pane_info.MinimizeButton(False)
        pane_info.PinButton(True)
        pane_info.Floatable(True)
        pane_info.Movable(True)
        pane_info.Resizable(True)
        pane_info.BestSize((400, 600))
        pane_info.MinSize((300, 400))
        
        # Add pane
        aui_mgr.AddPane(dockable, pane_info)
        aui_mgr.Update()
        
        _kinotes_instance['pane'] = dockable
        
        return True
        
    except Exception as e:
        print(f"KiNotes: Docking failed: {e}")
        return False


def toggle_kinotes_panel():
    """Toggle KiNotes panel visibility."""
    pane = _kinotes_instance.get('pane')
    
    if pane:
        try:
            # Get AUI manager and toggle
            for win in wx.GetTopLevelWindows():
                if hasattr(win, 'GetAuiManager'):
                    aui_mgr = win.GetAuiManager()
                    if aui_mgr:
                        pane = aui_mgr.GetPane("KiNotes")
                        if pane.IsOk():
                            pane.Show(not pane.IsShown())
                            aui_mgr.Update()
                            return True
        except:
            pass
    
    return False


class KiNotesActionPlugin(pcbnew.ActionPlugin):
    """
    KiCad Action Plugin for KiNotes.
    Registers in Tools → External Plugins menu and toolbar.
    """
    
    def defaults(self):
        """Set plugin defaults."""
        self.name = "KiNotes"
        self.category = "Utilities"
        self.description = "Smart engineering notes with tabs: Notes, Todo List, Settings"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(_plugin_dir, "resources", "icon.png")
        
        # Dark mode icon
        dark_icon = os.path.join(_plugin_dir, "resources", "icon.png")
        if os.path.exists(dark_icon):
            self.dark_icon_file_name = dark_icon
    
    def Run(self):
        """Run the plugin - ensures only one frame is open."""
        print("KiNotes: Run() called")
        
        # Validate environment
        if not self._validate_environment():
            return
        
        # Get project directory
        board = pcbnew.GetBoard()
        project_dir = os.path.dirname(board.GetFileName()) if board else None
        
        # Check if already open - bring to front if so
        existing_frame = get_kinotes_frame()
        if existing_frame is not None:
            print("KiNotes: Found existing frame, raising it")
            try:
                if existing_frame.IsShown():
                    existing_frame.Raise()
                    existing_frame.SetFocus()
                    return
                else:
                    existing_frame.Show(True)
                    existing_frame.Raise()
                    return
            except (RuntimeError, wx.PyDeadObjectError, AttributeError):
                # Frame was destroyed, clear reference
                print("KiNotes: Existing frame invalid, clearing")
                set_kinotes_frame(None)
        
        # Close any orphaned KiNotes windows before creating new one
        close_all_kinotes_windows()
        
        # Create new floating window - only one allowed
        print("KiNotes: Creating new frame")
        new_frame = KiNotesFrame(None, project_dir)
        set_kinotes_frame(new_frame)
        new_frame.Show(True)
        print("KiNotes: Frame shown")
    
    def _validate_environment(self):
        """Validate environment."""
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
        
        # Check read-only
        project_path_lower = project_path.lower()
        if (project_path_lower.startswith("c:\\program files") or 
            "kicad\\demos" in project_path_lower or
            "kicad/demos" in project_path_lower):
            wx.MessageBox(
                "Read-only project location.\n\n"
                "Please save to a writable location.",
                "KiNotes",
                wx.OK | wx.ICON_ERROR
            )
            return False
        
        return True


# Register plugin
KiNotesActionPlugin().register()
