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
import traceback
import threading

# Add package to path for imports
_plugin_dir = os.path.dirname(os.path.abspath(__file__))
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

# Import centralized defaults
from core.defaultsConfig import WINDOW_DEFAULTS, debug_print, DEPLOY_BUILD


# ============================================================
# GLOBAL EXCEPTION HANDLER - Prevents KiCad crashes
# ============================================================
_original_excepthook = sys.excepthook

def _kinotes_exception_handler(exc_type, exc_value, exc_tb):
    """Global exception handler to prevent KiNotes from crashing KiCad."""
    try:
        # Log to console
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(f"[KiNotes ERROR] Caught exception:\n{error_msg}")
        
        # Try to save user data before anything else
        _emergency_save()
        
        # Show user-friendly error (non-blocking)
        try:
            wx.CallAfter(_show_error_dialog, str(exc_value))
        except:
            pass
            
    except Exception as e:
        print(f"[KiNotes] Exception handler error: {e}")
    
    # Don't call original hook to prevent KiCad crash
    # Only log, don't propagate


def _emergency_save():
    """Emergency save of user data on crash."""
    try:
        frame = _kinotes_instance.get('frame')
        if frame and hasattr(frame, 'main_panel'):
            try:
                frame.main_panel.force_save()
                print("[KiNotes] Emergency save completed")
            except:
                pass
    except:
        pass


def _show_error_dialog(error_msg):
    """Show error dialog to user."""
    try:
        wx.MessageBox(
            f"KiNotes encountered an error:\n{error_msg[:200]}\n\nYour notes have been saved.",
            "KiNotes Error",
            wx.OK | wx.ICON_WARNING
        )
    except:
        pass


# Install global exception handler for KiNotes
sys.excepthook = _kinotes_exception_handler


# ============================================================
# THREAD-SAFE LOCK FOR SINGLETON MANAGEMENT
# ============================================================
_instance_lock = threading.Lock()

# Force reload of modules to get latest changes
import importlib

def _force_reload_modules():
    """Force reload all UI modules to pick up latest changes."""
    try:
        # Reload in dependency order: visual_editor, markdown_converter, then main_panel
        from ui import visual_editor, markdown_converter, main_panel
        importlib.reload(visual_editor)
        print("[KiNotes] Reloaded visual_editor")
        importlib.reload(markdown_converter)
        print("[KiNotes] Reloaded markdown_converter")
        importlib.reload(main_panel)
        print("[KiNotes] Reloaded main_panel")
    except Exception as e:
        print(f"[KiNotes] Module reload warning: {e}")

_force_reload_modules()

from core.notes_manager import NotesManager
from core.designator_linker import DesignatorLinker
from core.metadata_extractor import MetadataExtractor
from core.pdf_exporter import PDFExporter
from ui.main_panel import KiNotesMainPanel

# Import version from single source of truth
from __version__ import __version__ as _PLUGIN_VERSION
print(f"KiNotes v{_PLUGIN_VERSION} (Build {DEPLOY_BUILD}) loaded - Crash-safe edition")


# Global singleton - ensures only ONE window ever
_kinotes_instance = {'frame': None, 'pane': None, 'closing': False, 'opening': False}


def get_kinotes_frame():
    """Get existing KiNotes frame if it exists and is valid."""
    # Don't return frame during close/open operations
    if _kinotes_instance.get('closing') or _kinotes_instance.get('opening'):
        return None
    
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


def is_kinotes_busy():
    """Check if KiNotes is currently opening or closing."""
    return _kinotes_instance.get('closing', False) or _kinotes_instance.get('opening', False)


def close_all_kinotes_windows():
    """Close any existing KiNotes windows safely."""
    if _kinotes_instance.get('closing'):
        return  # Already closing
    
    _kinotes_instance['closing'] = True
    
    try:
        # Close tracked frame
        frame = _kinotes_instance.get('frame')
        if frame:
            try:
                if hasattr(frame, 'IsBeingDeleted') and frame.IsBeingDeleted():
                    pass  # Already being deleted
                else:
                    frame.Destroy()
            except (RuntimeError, wx.PyDeadObjectError, Exception):
                pass
        _kinotes_instance['frame'] = None
        
        # Also search for any orphaned windows - be careful with iteration
        try:
            windows_to_close = []
            for win in wx.GetTopLevelWindows():
                try:
                    if win and 'KiNotes' in win.GetTitle():
                        windows_to_close.append(win)
                except:
                    pass
            
            for win in windows_to_close:
                try:
                    win.Destroy()
                except:
                    pass
        except:
            pass
        
        # Allow pending events to process
        wx.SafeYield()
        
    finally:
        _kinotes_instance['closing'] = False


class KiNotesFrame(wx.Frame):
    """
    KiNotes floating window - uses regular Frame for visible close button.
    """
    
    def __init__(self, parent=None, project_dir=None):
        self.project_dir = project_dir or self._get_project_dir()
        project_name = os.path.basename(self.project_dir) if self.project_dir else "KiNotes"
        
        # Get version from package
        try:
            from . import __version__
            version = __version__
        except:
            version = "1.4.1"
        
        # Load panel size from settings (use centralized defaults)
        panel_width = WINDOW_DEFAULTS['panel_width']
        panel_height = WINDOW_DEFAULTS['panel_height']
        debug_print(f"[KiNotes SIZE] Frame defaults: {panel_width}x{panel_height}")
        try:
            notes_manager = NotesManager(self.project_dir)
            settings = notes_manager.load_settings()
            if settings:
                panel_width = settings.get("panel_width", WINDOW_DEFAULTS['panel_width'])
                panel_height = settings.get("panel_height", WINDOW_DEFAULTS['panel_height'])
                debug_print(f"[KiNotes SIZE] Frame from settings: {panel_width}x{panel_height}")
            else:
                debug_print(f"[KiNotes SIZE] No settings found, using defaults")
        except Exception as e:
            debug_print(f"[KiNotes SIZE] Error loading settings: {e}")
        
        # Use regular Frame style for better close button visibility
        style = (wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)
        
        super().__init__(
            parent,
            title=f"KiNotes v{version}",
            size=(panel_width, panel_height),
            style=style
        )
        debug_print(f"[KiNotes SIZE] Frame created with size: {self.GetSize()}")
        
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
        
        # Set window icon (PNG format)
        icon_png = os.path.join(_plugin_dir, "resources", "icon.png")
        if os.path.exists(icon_png):
            try:
                self.SetIcon(wx.Icon(icon_png))
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
        
        # Set minimum size (800x600 - Windows standard minimum)
        self.SetMinSize((800, 600))
        debug_print(f"[KiNotes SIZE] Frame after SetMinSize: {self.GetSize()}, MinSize: {self.GetMinSize()}")
    
    def _position_window(self):
        """Position window on the right side of the CURRENT display (where mouse is)."""
        try:
            # Get display where mouse currently is (multi-monitor aware)
            mouse_pos = wx.GetMousePosition()
            display_idx = wx.Display.GetFromPoint(mouse_pos)
            if display_idx == wx.NOT_FOUND:
                display_idx = 0  # Fallback to primary
            
            display = wx.Display(display_idx)
            screen_rect = display.GetClientArea()
            debug_print(f"[KiNotes SIZE] Display {display_idx}, Screen rect: {screen_rect.GetWidth()}x{screen_rect.GetHeight()}, origin: ({screen_rect.GetX()}, {screen_rect.GetY()})")
            
            # Position on right side of CURRENT display
            frame_size = self.GetSize()
            x = screen_rect.GetRight() - frame_size.GetWidth() - 20
            y = screen_rect.GetTop() + 100
            
            # Ensure position is within screen bounds
            if x < screen_rect.GetX():
                x = screen_rect.GetX() + 20
            if y < screen_rect.GetY():
                y = screen_rect.GetY() + 20
            
            self.SetPosition((x, y))
            debug_print(f"[KiNotes SIZE] Frame positioned at ({x}, {y}), final size: {self.GetSize()}")
        except Exception as e:
            debug_print(f"[KiNotes SIZE] Position error: {e}, centering instead")
            self.Centre()
    
    def _bind_events(self):
        """Bind window events."""
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_ACTIVATE, self._on_activate)
    
    def _on_close(self, event):
        """Handle close - save and cleanup safely with full error protection."""
        # Prevent re-entry during close
        with _instance_lock:
            if _kinotes_instance.get('closing'):
                event.Skip()
                return
            _kinotes_instance['closing'] = True
        
        try:
            # PRIORITY 1: Save KiNotes data first
            try:
                if hasattr(self, 'main_panel') and self.main_panel:
                    self.main_panel.force_save()
                    print("[KiNotes] Data saved on close")
            except Exception as e:
                print(f"[KiNotes] Save warning: {e}")
            
            # PRIORITY 2: Cleanup timers and resources
            try:
                if hasattr(self, 'main_panel') and self.main_panel:
                    self.main_panel.cleanup()
            except Exception as e:
                print(f"[KiNotes] Cleanup warning: {e}")
            
            # Clear global reference BEFORE destroying
            set_kinotes_frame(None)
            
            # Use CallAfter for safer destruction
            wx.CallAfter(self._safe_destroy)
            
        except Exception as e:
            print(f"[KiNotes] Close error: {e}")
            set_kinotes_frame(None)
            with _instance_lock:
                _kinotes_instance['closing'] = False
        
        # Don't skip - we handle destruction ourselves
        event.Veto()
    
    def _safe_destroy(self):
        """Safely destroy the frame after pending events."""
        try:
            # NOTE: force_save() already called in _on_close() before cleanup()
            # Calling it again here would fail since cleanup() sets notes_manager = None
            # So we skip the redundant save and just proceed to destruction cleanup
            
            # Unbind frame events before destroy
            try:
                self.Unbind(wx.EVT_CLOSE)
                self.Unbind(wx.EVT_ACTIVATE)
            except:
                pass
            
            # Destroy main_panel reference
            try:
                if hasattr(self, 'main_panel'):
                    self.main_panel = None
            except:
                pass
            
            # Destroy frame
            self.Destroy()
            print("[KiNotes] Frame destroyed successfully")
        except Exception as e:
            print(f"[KiNotes] Destroy warning: {e}")
        finally:
            with _instance_lock:
                _kinotes_instance['closing'] = False
    
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
        
        # KiCad requires PNG format for toolbar icons (24x24)
        icon_png = os.path.join(_plugin_dir, "resources", "icon.png")
        
        if os.path.exists(icon_png):
            self.icon_file_name = icon_png
            self.dark_icon_file_name = icon_png
        else:
            self.icon_file_name = ""
            self.dark_icon_file_name = ""
    
    def Run(self):
        """Run the plugin - ensures only one frame is open with race condition protection."""
        print("KiNotes: Run() called")
        
        # Prevent rapid clicking crashes
        if is_kinotes_busy():
            print("KiNotes: Busy (opening/closing), ignoring click")
            return
        
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
        
        # Mark as opening to prevent race conditions
        _kinotes_instance['opening'] = True
        
        try:
            # Close any orphaned KiNotes windows before creating new one
            close_all_kinotes_windows()
            
            # Small delay to ensure cleanup is complete
            wx.SafeYield()
            
            # Create new floating window - only one allowed
            print("KiNotes: Creating new frame")
            new_frame = KiNotesFrame(None, project_dir)
            set_kinotes_frame(new_frame)
            new_frame.Show(True)
            print("KiNotes: Frame shown")
            
        except Exception as e:
            print(f"KiNotes: Error creating frame: {e}")
            set_kinotes_frame(None)
        finally:
            _kinotes_instance['opening'] = False
    
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
